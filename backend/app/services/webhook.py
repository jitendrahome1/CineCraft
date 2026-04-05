"""
Webhook handler service for Stripe events.
Processes Stripe webhooks for subscription and payment events.
"""
import stripe
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.core.errors import StripeWebhookError
from app.services.subscription import SubscriptionService
from app.services.payment import PaymentService
from app.repositories.plan import PlanRepository

logger = get_logger(__name__)


class WebhookService:
    """Service for handling Stripe webhooks."""

    def __init__(self, db: Session):
        """
        Initialize webhook service.

        Args:
            db: Database session
        """
        self.db = db
        self.subscription_service = SubscriptionService(db)
        self.payment_service = PaymentService(db)
        self.plan_repo = PlanRepository(db)

    def verify_webhook_signature(self, payload: bytes, signature: str) -> dict:
        """
        Verify Stripe webhook signature.

        Args:
            payload: Request body as bytes
            signature: Stripe-Signature header value

        Returns:
            Verified event dict

        Raises:
            StripeWebhookError: If signature verification fails
        """
        if not settings.STRIPE_WEBHOOK_SECRET:
            raise StripeWebhookError("Stripe webhook secret not configured")

        try:
            event = stripe.Webhook.construct_event(
                payload,
                signature,
                settings.STRIPE_WEBHOOK_SECRET
            )
            return event
        except ValueError as e:
            logger.error(f"Invalid webhook payload: {str(e)}")
            raise StripeWebhookError("Invalid payload")
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid webhook signature: {str(e)}")
            raise StripeWebhookError("Invalid signature")

    def handle_webhook_event(self, event: dict) -> dict:
        """
        Handle Stripe webhook event.

        Args:
            event: Stripe event dict

        Returns:
            Processing result

        Raises:
            StripeWebhookError: If event processing fails
        """
        event_type = event["type"]
        data = event["data"]["object"]

        logger.info(f"Processing Stripe webhook: {event_type}")

        try:
            # Route to appropriate handler
            if event_type == "checkout.session.completed":
                return self._handle_checkout_completed(data)
            elif event_type == "customer.subscription.created":
                return self._handle_subscription_created(data)
            elif event_type == "customer.subscription.updated":
                return self._handle_subscription_updated(data)
            elif event_type == "customer.subscription.deleted":
                return self._handle_subscription_deleted(data)
            elif event_type == "invoice.payment_succeeded":
                return self._handle_invoice_payment_succeeded(data)
            elif event_type == "invoice.payment_failed":
                return self._handle_invoice_payment_failed(data)
            else:
                logger.info(f"Unhandled webhook event type: {event_type}")
                return {"status": "unhandled", "event_type": event_type}

        except Exception as e:
            logger.error(f"Error processing webhook {event_type}: {str(e)}")
            raise StripeWebhookError(f"Failed to process webhook: {str(e)}")

    def _handle_checkout_completed(self, session: dict) -> dict:
        """
        Handle checkout.session.completed event.

        Args:
            session: Checkout session data

        Returns:
            Processing result
        """
        logger.info(f"Checkout completed: {session['id']}")

        # Get subscription from Stripe
        subscription_id = session.get("subscription")
        if not subscription_id:
            logger.warning("No subscription ID in checkout session")
            return {"status": "no_subscription"}

        # Get subscription details
        stripe_subscription = stripe.Subscription.retrieve(subscription_id)

        # Extract metadata
        metadata = session.get("metadata", {})
        user_id = int(metadata.get("user_id"))
        plan_id = int(metadata.get("plan_id"))
        billing_interval = metadata.get("billing_interval", "monthly")

        # Create subscription in database
        self.subscription_service.create_paid_subscription(
            user_id=user_id,
            plan_id=plan_id,
            stripe_subscription_id=subscription_id,
            stripe_customer_id=session["customer"],
            billing_interval=billing_interval,
            current_period_start=datetime.fromtimestamp(stripe_subscription["current_period_start"]),
            current_period_end=datetime.fromtimestamp(stripe_subscription["current_period_end"])
        )

        return {"status": "success", "subscription_id": subscription_id}

    def _handle_subscription_created(self, subscription: dict) -> dict:
        """
        Handle customer.subscription.created event.

        Args:
            subscription: Subscription data

        Returns:
            Processing result
        """
        logger.info(f"Subscription created: {subscription['id']}")
        return {"status": "success"}

    def _handle_subscription_updated(self, subscription: dict) -> dict:
        """
        Handle customer.subscription.updated event.

        Args:
            subscription: Subscription data

        Returns:
            Processing result
        """
        logger.info(f"Subscription updated: {subscription['id']}")

        # Update subscription in database
        self.subscription_service.update_subscription_from_stripe(
            stripe_subscription_id=subscription["id"],
            status=subscription["status"],
            current_period_start=datetime.fromtimestamp(subscription["current_period_start"]),
            current_period_end=datetime.fromtimestamp(subscription["current_period_end"])
        )

        return {"status": "success"}

    def _handle_subscription_deleted(self, subscription: dict) -> dict:
        """
        Handle customer.subscription.deleted event.

        Args:
            subscription: Subscription data

        Returns:
            Processing result
        """
        logger.info(f"Subscription deleted: {subscription['id']}")

        # Update subscription status
        self.subscription_service.update_subscription_from_stripe(
            stripe_subscription_id=subscription["id"],
            status="canceled",
            current_period_start=datetime.fromtimestamp(subscription["current_period_start"]),
            current_period_end=datetime.fromtimestamp(subscription["current_period_end"])
        )

        return {"status": "success"}

    def _handle_invoice_payment_succeeded(self, invoice: dict) -> dict:
        """
        Handle invoice.payment_succeeded event.

        Args:
            invoice: Invoice data

        Returns:
            Processing result
        """
        logger.info(f"Invoice payment succeeded: {invoice['id']}")

        # Get subscription from invoice
        subscription_id = invoice.get("subscription")
        if not subscription_id:
            return {"status": "no_subscription"}

        # Get subscription from database
        from app.repositories.subscription import SubscriptionRepository
        subscription_repo = SubscriptionRepository(self.db)
        subscription = subscription_repo.get_by_stripe_subscription_id(subscription_id)

        if not subscription:
            logger.warning(f"Subscription not found for invoice: {invoice['id']}")
            return {"status": "subscription_not_found"}

        # Record payment
        self.payment_service.record_payment(
            user_id=subscription.user_id,
            subscription_id=subscription.id,
            stripe_payment_intent_id=invoice.get("payment_intent"),
            stripe_invoice_id=invoice["id"],
            amount=invoice["amount_paid"] / 100,  # Convert from cents
            currency=invoice["currency"],
            status="succeeded",
            receipt_url=invoice.get("hosted_invoice_url")
        )

        return {"status": "success"}

    def _handle_invoice_payment_failed(self, invoice: dict) -> dict:
        """
        Handle invoice.payment_failed event.

        Args:
            invoice: Invoice data

        Returns:
            Processing result
        """
        logger.warning(f"Invoice payment failed: {invoice['id']}")

        # Get subscription from invoice
        subscription_id = invoice.get("subscription")
        if not subscription_id:
            return {"status": "no_subscription"}

        # Get subscription from database
        from app.repositories.subscription import SubscriptionRepository
        subscription_repo = SubscriptionRepository(self.db)
        subscription = subscription_repo.get_by_stripe_subscription_id(subscription_id)

        if not subscription:
            return {"status": "subscription_not_found"}

        # Record failed payment
        self.payment_service.record_payment(
            user_id=subscription.user_id,
            subscription_id=subscription.id,
            stripe_payment_intent_id=invoice.get("payment_intent"),
            stripe_invoice_id=invoice["id"],
            amount=invoice["amount_due"] / 100,  # Convert from cents
            currency=invoice["currency"],
            status="failed"
        )

        return {"status": "success"}
