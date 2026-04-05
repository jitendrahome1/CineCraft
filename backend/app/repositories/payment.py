"""
Payment repository for database operations related to payments.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from sqlalchemy import desc
from app.repositories.base import BaseRepository
from app.models.payment import Payment
from app.core.logging import get_logger

logger = get_logger(__name__)


class PaymentRepository(BaseRepository[Payment]):
    """Repository for Payment model operations."""

    def __init__(self, db: Session):
        """
        Initialize payment repository.

        Args:
            db: Database session
        """
        super().__init__(Payment, db)

    def get_by_stripe_payment_intent_id(self, payment_intent_id: str) -> Optional[Payment]:
        """
        Get payment by Stripe PaymentIntent ID.

        Args:
            payment_intent_id: Stripe PaymentIntent ID

        Returns:
            Payment instance or None
        """
        return self.db.query(Payment).filter(
            Payment.stripe_payment_intent_id == payment_intent_id
        ).first()

    def get_by_user_id(self, user_id: int, limit: int = 50) -> List[Payment]:
        """
        Get payments for a user.

        Args:
            user_id: User ID
            limit: Maximum number of payments

        Returns:
            List of payments
        """
        return self.db.query(Payment).filter(
            Payment.user_id == user_id
        ).order_by(desc(Payment.created_at)).limit(limit).all()

    def get_by_subscription_id(self, subscription_id: int) -> List[Payment]:
        """
        Get payments for a subscription.

        Args:
            subscription_id: Subscription ID

        Returns:
            List of payments
        """
        return self.db.query(Payment).filter(
            Payment.subscription_id == subscription_id
        ).order_by(desc(Payment.created_at)).all()

    def get_successful_payments(self, user_id: int) -> List[Payment]:
        """
        Get successful payments for a user.

        Args:
            user_id: User ID

        Returns:
            List of successful payments
        """
        return self.db.query(Payment).filter(
            Payment.user_id == user_id,
            Payment.status == "succeeded"
        ).order_by(desc(Payment.created_at)).all()
