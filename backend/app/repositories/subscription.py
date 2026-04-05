"""
Subscription repository for database operations related to user subscriptions.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import and_
from datetime import datetime, timedelta
from app.repositories.base import BaseRepository
from app.models.subscription import Subscription, SubscriptionStatus
from app.core.logging import get_logger

logger = get_logger(__name__)


class SubscriptionRepository(BaseRepository[Subscription]):
    """Repository for Subscription model operations."""

    def __init__(self, db: Session):
        """
        Initialize subscription repository.

        Args:
            db: Database session
        """
        super().__init__(Subscription, db)

    def get_by_user_id(self, user_id: int) -> Optional[Subscription]:
        """
        Get active subscription for user.

        Args:
            user_id: User ID

        Returns:
            Active subscription or None
        """
        return self.db.query(Subscription).filter(
            and_(
                Subscription.user_id == user_id,
                Subscription.status == SubscriptionStatus.ACTIVE
            )
        ).first()

    def get_by_stripe_subscription_id(self, stripe_subscription_id: str) -> Optional[Subscription]:
        """
        Get subscription by Stripe subscription ID.

        Args:
            stripe_subscription_id: Stripe Subscription ID

        Returns:
            Subscription instance or None
        """
        return self.db.query(Subscription).filter(
            Subscription.stripe_subscription_id == stripe_subscription_id
        ).first()

    def get_by_stripe_customer_id(self, stripe_customer_id: str) -> Optional[Subscription]:
        """
        Get subscription by Stripe customer ID.

        Args:
            stripe_customer_id: Stripe Customer ID

        Returns:
            Subscription instance or None
        """
        return self.db.query(Subscription).filter(
            Subscription.stripe_customer_id == stripe_customer_id
        ).first()

    def increment_usage(self, subscription_id: int) -> Optional[Subscription]:
        """
        Increment video usage count for subscription.

        Args:
            subscription_id: Subscription ID

        Returns:
            Updated subscription or None
        """
        subscription = self.get(subscription_id)
        if subscription:
            subscription.videos_used_this_month += 1
            self.db.commit()
            self.db.refresh(subscription)
        return subscription

    def reset_usage(self, subscription_id: int) -> Optional[Subscription]:
        """
        Reset monthly usage counter.

        Args:
            subscription_id: Subscription ID

        Returns:
            Updated subscription or None
        """
        subscription = self.get(subscription_id)
        if subscription:
            subscription.videos_used_this_month = 0
            subscription.usage_reset_date = datetime.utcnow() + timedelta(days=30)
            self.db.commit()
            self.db.refresh(subscription)
            logger.info(f"Reset usage for subscription {subscription_id}")
        return subscription

    def cancel_subscription(self, subscription_id: int, at_period_end: bool = True) -> Optional[Subscription]:
        """
        Cancel a subscription.

        Args:
            subscription_id: Subscription ID
            at_period_end: Whether to cancel at period end

        Returns:
            Updated subscription or None
        """
        subscription = self.get(subscription_id)
        if subscription:
            subscription.cancel_at_period_end = at_period_end
            if not at_period_end:
                subscription.status = SubscriptionStatus.CANCELED
                subscription.canceled_at = datetime.utcnow()
            else:
                subscription.canceled_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(subscription)
            logger.info(f"Canceled subscription {subscription_id} (at_period_end={at_period_end})")
        return subscription

    def get_expiring_soon(self, days: int = 7) -> List[Subscription]:
        """
        Get subscriptions expiring in the next N days.

        Args:
            days: Number of days to look ahead

        Returns:
            List of subscriptions
        """
        cutoff_date = datetime.utcnow() + timedelta(days=days)
        return self.db.query(Subscription).filter(
            and_(
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.current_period_end <= cutoff_date,
                Subscription.cancel_at_period_end == True
            )
        ).all()
