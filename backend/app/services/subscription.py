"""
Subscription service for managing user subscriptions.
Handles subscription creation, upgrades, downgrades, and usage tracking.
"""
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.repositories.subscription import SubscriptionRepository
from app.repositories.plan import PlanRepository
from app.core.logging import get_logger
from app.core.errors import SubscriptionError, SubscriptionNotFoundError, SubscriptionLimitError
from app.models.subscription import Subscription, SubscriptionStatus, BillingInterval
from app.models.user import User
from app.models.plan import Plan

logger = get_logger(__name__)


class SubscriptionService:
    """Service for subscription operations."""

    def __init__(self, db: Session):
        """
        Initialize subscription service.

        Args:
            db: Database session
        """
        self.db = db
        self.subscription_repo = SubscriptionRepository(db)
        self.plan_repo = PlanRepository(db)

    def get_user_subscription(self, user_id: int) -> Optional[Subscription]:
        """
        Get active subscription for user.

        Args:
            user_id: User ID

        Returns:
            Active subscription or None
        """
        return self.subscription_repo.get_by_user_id(user_id)

    def create_free_subscription(self, user: User) -> Subscription:
        """
        Create a free subscription for new user.

        Args:
            user: User instance

        Returns:
            Created subscription

        Raises:
            SubscriptionError: If free plan not found
        """
        # Get free plan
        free_plan = self.plan_repo.get_by_name("Free")
        if not free_plan:
            raise SubscriptionError("Free plan not found")

        # Create subscription
        subscription = self.subscription_repo.create({
            "user_id": user.id,
            "plan_id": free_plan.id,
            "status": SubscriptionStatus.ACTIVE,
            "billing_interval": BillingInterval.MONTHLY,
            "current_period_start": datetime.utcnow(),
            "current_period_end": datetime.utcnow() + timedelta(days=30),
            "usage_reset_date": datetime.utcnow() + timedelta(days=30)
        })

        logger.info(f"Created free subscription for user {user.email}")
        return subscription

    def create_paid_subscription(
        self,
        user_id: int,
        plan_id: int,
        stripe_subscription_id: str,
        stripe_customer_id: str,
        billing_interval: str,
        current_period_start: datetime,
        current_period_end: datetime
    ) -> Subscription:
        """
        Create a paid subscription from Stripe checkout.

        Args:
            user_id: User ID
            plan_id: Plan ID
            stripe_subscription_id: Stripe Subscription ID
            stripe_customer_id: Stripe Customer ID
            billing_interval: Billing interval
            current_period_start: Period start
            current_period_end: Period end

        Returns:
            Created subscription
        """
        # Cancel existing subscription if any
        existing = self.subscription_repo.get_by_user_id(user_id)
        if existing:
            self.subscription_repo.cancel_subscription(existing.id, at_period_end=False)

        # Create new subscription
        subscription = self.subscription_repo.create({
            "user_id": user_id,
            "plan_id": plan_id,
            "stripe_subscription_id": stripe_subscription_id,
            "stripe_customer_id": stripe_customer_id,
            "status": SubscriptionStatus.ACTIVE,
            "billing_interval": billing_interval,
            "current_period_start": current_period_start,
            "current_period_end": current_period_end,
            "usage_reset_date": datetime.utcnow() + timedelta(days=30)
        })

        logger.info(f"Created paid subscription for user {user_id}, plan {plan_id}")
        return subscription

    def can_create_video(self, user_id: int) -> tuple[bool, Optional[str]]:
        """
        Check if user can create a new video based on subscription limits.

        Args:
            user_id: User ID

        Returns:
            Tuple of (can_create, reason_if_not)
        """
        subscription = self.subscription_repo.get_by_user_id(user_id)

        if not subscription:
            return False, "No active subscription found"

        if subscription.status != SubscriptionStatus.ACTIVE:
            return False, f"Subscription is {subscription.status}"

        # Get plan limits
        plan = subscription.plan

        # Check video limit
        if plan.max_videos_per_month is not None:
            if subscription.videos_used_this_month >= plan.max_videos_per_month:
                return False, f"Monthly video limit reached ({plan.max_videos_per_month} videos)"

        # Reset usage if needed
        if subscription.usage_reset_date and datetime.utcnow() >= subscription.usage_reset_date:
            self.subscription_repo.reset_usage(subscription.id)

        return True, None

    def increment_video_usage(self, user_id: int) -> Subscription:
        """
        Increment video usage count for user.

        Args:
            user_id: User ID

        Returns:
            Updated subscription

        Raises:
            SubscriptionNotFoundError: If subscription not found
        """
        subscription = self.subscription_repo.get_by_user_id(user_id)

        if not subscription:
            raise SubscriptionNotFoundError("No active subscription found")

        return self.subscription_repo.increment_usage(subscription.id)

    def cancel_subscription(self, user_id: int, at_period_end: bool = True) -> Subscription:
        """
        Cancel user subscription.

        Args:
            user_id: User ID
            at_period_end: Whether to cancel at period end

        Returns:
            Updated subscription

        Raises:
            SubscriptionNotFoundError: If subscription not found
        """
        subscription = self.subscription_repo.get_by_user_id(user_id)

        if not subscription:
            raise SubscriptionNotFoundError("No active subscription found")

        return self.subscription_repo.cancel_subscription(subscription.id, at_period_end)

    def update_subscription_from_stripe(
        self,
        stripe_subscription_id: str,
        status: str,
        current_period_start: datetime,
        current_period_end: datetime
    ) -> Optional[Subscription]:
        """
        Update subscription from Stripe webhook event.

        Args:
            stripe_subscription_id: Stripe Subscription ID
            status: Subscription status
            current_period_start: Period start
            current_period_end: Period end

        Returns:
            Updated subscription or None
        """
        subscription = self.subscription_repo.get_by_stripe_subscription_id(stripe_subscription_id)

        if not subscription:
            logger.warning(f"Subscription not found for Stripe ID: {stripe_subscription_id}")
            return None

        # Map Stripe status to our status
        status_map = {
            "active": SubscriptionStatus.ACTIVE,
            "canceled": SubscriptionStatus.CANCELED,
            "past_due": SubscriptionStatus.PAST_DUE,
            "trialing": SubscriptionStatus.TRIALING,
            "incomplete": SubscriptionStatus.INCOMPLETE,
            "incomplete_expired": SubscriptionStatus.INCOMPLETE_EXPIRED,
            "unpaid": SubscriptionStatus.UNPAID
        }

        subscription_status = status_map.get(status, SubscriptionStatus.ACTIVE)

        # Update subscription
        self.subscription_repo.update(subscription, {
            "status": subscription_status,
            "current_period_start": current_period_start,
            "current_period_end": current_period_end
        })

        logger.info(f"Updated subscription {subscription.id} from Stripe webhook")
        return subscription

    def get_subscription_with_plan(self, user_id: int) -> Optional[dict]:
        """
        Get subscription with plan details for user.

        Args:
            user_id: User ID

        Returns:
            Dict with subscription and plan info
        """
        subscription = self.subscription_repo.get_by_user_id(user_id)

        if not subscription:
            return None

        plan = subscription.plan

        return {
            "subscription": subscription,
            "plan": plan,
            "usage": {
                "videos_used": subscription.videos_used_this_month,
                "videos_limit": plan.max_videos_per_month,
                "videos_remaining": (
                    plan.max_videos_per_month - subscription.videos_used_this_month
                    if plan.max_videos_per_month is not None
                    else None
                )
            }
        }
