"""
Payment service for Stripe integration.
Handles payment processing, checkout sessions, and customer management.
"""
from typing import Optional
import stripe
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.core.errors import PaymentError
from app.repositories.payment import PaymentRepository
from app.repositories.subscription import SubscriptionRepository
from app.models.payment import Payment
from app.models.user import User
from app.models.plan import Plan

logger = get_logger(__name__)

# Initialize Stripe
if settings.STRIPE_API_KEY:
    stripe.api_key = settings.STRIPE_API_KEY


class PaymentService:
    """Service for payment operations."""

    def __init__(self, db: Session):
        """
        Initialize payment service.

        Args:
            db: Database session
        """
        self.db = db
        self.payment_repo = PaymentRepository(db)
        self.subscription_repo = SubscriptionRepository(db)

    def create_or_get_customer(self, user: User) -> str:
        """
        Create or get existing Stripe customer.

        Args:
            user: User instance

        Returns:
            Stripe customer ID

        Raises:
            PaymentError: If Stripe API fails
        """
        try:
            # Check if user already has a subscription with customer ID
            subscription = self.subscription_repo.get_by_user_id(user.id)
            if subscription and subscription.stripe_customer_id:
                return subscription.stripe_customer_id

            # Create new Stripe customer
            customer = stripe.Customer.create(
                email=user.email,
                name=user.full_name,
                metadata={"user_id": str(user.id)}
            )

            logger.info(f"Created Stripe customer for user {user.email}: {customer.id}")
            return customer.id

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating customer: {str(e)}")
            raise PaymentError(f"Failed to create payment customer: {str(e)}")

    def create_checkout_session(
        self,
        user: User,
        plan: Plan,
        billing_interval: str = "monthly",
        success_url: str = None,
        cancel_url: str = None
    ) -> dict:
        """
        Create Stripe checkout session for subscription.

        Args:
            user: User instance
            plan: Plan instance
            billing_interval: "monthly" or "yearly"
            success_url: URL to redirect after successful payment
            cancel_url: URL to redirect if payment is canceled

        Returns:
            Checkout session data

        Raises:
            PaymentError: If Stripe API fails
        """
        try:
            # Get or create customer
            customer_id = self.create_or_get_customer(user)

            # Get appropriate price ID
            price_id = (
                plan.stripe_price_id_monthly
                if billing_interval == "monthly"
                else plan.stripe_price_id_yearly
            )

            if not price_id:
                raise PaymentError(f"No Stripe price ID configured for {billing_interval} billing")

            # Create checkout session
            session = stripe.checkout.Session.create(
                customer=customer_id,
                payment_method_types=["card"],
                line_items=[{
                    "price": price_id,
                    "quantity": 1
                }],
                mode="subscription",
                success_url=success_url or f"{settings.cors_origins_list[0]}/subscription/success?session_id={{CHECKOUT_SESSION_ID}}",
                cancel_url=cancel_url or f"{settings.cors_origins_list[0]}/subscription/cancel",
                metadata={
                    "user_id": str(user.id),
                    "plan_id": str(plan.id),
                    "billing_interval": billing_interval
                }
            )

            logger.info(f"Created checkout session for user {user.email}: {session.id}")

            return {
                "session_id": session.id,
                "url": session.url,
                "customer_id": customer_id
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating checkout session: {str(e)}")
            raise PaymentError(f"Failed to create checkout session: {str(e)}")

    def create_customer_portal_session(
        self,
        customer_id: str,
        return_url: str = None
    ) -> dict:
        """
        Create Stripe customer portal session for managing subscription.

        Args:
            customer_id: Stripe customer ID
            return_url: URL to return to after portal session

        Returns:
            Portal session data

        Raises:
            PaymentError: If Stripe API fails
        """
        try:
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=return_url or f"{settings.cors_origins_list[0]}/subscription"
            )

            return {
                "url": session.url
            }

        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating portal session: {str(e)}")
            raise PaymentError(f"Failed to create portal session: {str(e)}")

    def record_payment(
        self,
        user_id: int,
        subscription_id: Optional[int],
        stripe_payment_intent_id: str,
        stripe_invoice_id: Optional[str],
        amount: float,
        currency: str,
        status: str,
        receipt_url: Optional[str] = None
    ) -> Payment:
        """
        Record a payment in database.

        Args:
            user_id: User ID
            subscription_id: Subscription ID
            stripe_payment_intent_id: Stripe PaymentIntent ID
            stripe_invoice_id: Stripe Invoice ID
            amount: Payment amount
            currency: Currency code
            status: Payment status
            receipt_url: Receipt URL

        Returns:
            Created payment instance
        """
        payment = self.payment_repo.create({
            "user_id": user_id,
            "subscription_id": subscription_id,
            "stripe_payment_intent_id": stripe_payment_intent_id,
            "stripe_invoice_id": stripe_invoice_id,
            "amount": amount,
            "currency": currency,
            "status": status,
            "receipt_url": receipt_url
        })

        logger.info(f"Recorded payment for user {user_id}: ${amount} {currency}")
        return payment

    def get_payment_history(self, user_id: int, limit: int = 50):
        """
        Get payment history for user.

        Args:
            user_id: User ID
            limit: Maximum number of payments

        Returns:
            List of payments
        """
        return self.payment_repo.get_by_user_id(user_id, limit=limit)
