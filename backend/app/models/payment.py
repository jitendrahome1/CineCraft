"""
Payment transaction model.
Records all payment transactions from Stripe.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Numeric, DateTime, Boolean
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class Payment(BaseModel):
    """
    Payment transaction model.

    Attributes:
        user_id: Foreign key to users table
        subscription_id: Foreign key to subscriptions table
        stripe_payment_intent_id: Stripe PaymentIntent ID
        stripe_invoice_id: Stripe Invoice ID
        amount: Payment amount
        currency: Currency code
        status: Payment status (succeeded, failed, pending, etc.)
        payment_method: Payment method type
        receipt_url: URL to payment receipt
        paid_at: Payment timestamp
        refunded: Whether payment was refunded
        refunded_at: Refund timestamp
        refund_amount: Refund amount
    """
    __tablename__ = "payments"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    subscription_id = Column(Integer, ForeignKey("subscriptions.id"), nullable=True)

    # Stripe identifiers
    stripe_payment_intent_id = Column(String(255), unique=True, nullable=True, index=True)
    stripe_invoice_id = Column(String(255), nullable=True, index=True)

    # Payment details
    amount = Column(Numeric(10, 2), nullable=False)
    currency = Column(String(3), nullable=False, default="USD")
    status = Column(String(50), nullable=False, index=True)
    payment_method = Column(String(50), nullable=True)

    # Receipt
    receipt_url = Column(String(500), nullable=True)

    # Timestamps
    paid_at = Column(DateTime(timezone=True), nullable=True)

    # Refunds
    refunded = Column(Boolean, default=False, nullable=False)
    refunded_at = Column(DateTime(timezone=True), nullable=True)
    refund_amount = Column(Numeric(10, 2), nullable=True)

    # Relationships
    user = relationship("User", backref="payments")
    subscription = relationship("Subscription", backref="payments")

    def __repr__(self):
        return f"<Payment(id={self.id}, user_id={self.user_id}, amount=${self.amount}, status={self.status})>"
