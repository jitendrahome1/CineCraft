"""
User subscription model.
Links users to their subscription plans.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Enum as SQLEnum
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import enum
from app.models.base import BaseModel


class SubscriptionStatus(str, enum.Enum):
    """Subscription status enumeration."""
    ACTIVE = "active"
    CANCELED = "canceled"
    PAST_DUE = "past_due"
    TRIALING = "trialing"
    INCOMPLETE = "incomplete"
    INCOMPLETE_EXPIRED = "incomplete_expired"
    UNPAID = "unpaid"


class BillingInterval(str, enum.Enum):
    """Billing interval enumeration."""
    MONTHLY = "monthly"
    YEARLY = "yearly"


class Subscription(BaseModel):
    """
    User subscription model.

    Attributes:
        user_id: Foreign key to users table
        plan_id: Foreign key to plans table
        stripe_subscription_id: Stripe Subscription ID
        stripe_customer_id: Stripe Customer ID
        status: Subscription status
        billing_interval: Billing interval (monthly/yearly)
        current_period_start: Current billing period start
        current_period_end: Current billing period end
        cancel_at_period_end: Whether to cancel at period end
        canceled_at: Cancellation timestamp
        videos_used_this_month: Number of videos used in current month
        usage_reset_date: Date when usage counter resets
    """
    __tablename__ = "subscriptions"

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan_id = Column(Integer, ForeignKey("plans.id"), nullable=False)

    # Stripe identifiers
    stripe_subscription_id = Column(String(255), unique=True, nullable=True, index=True)
    stripe_customer_id = Column(String(255), nullable=True, index=True)

    # Status
    status = Column(
        SQLEnum(SubscriptionStatus),
        default=SubscriptionStatus.ACTIVE,
        nullable=False,
        index=True
    )
    billing_interval = Column(
        SQLEnum(BillingInterval),
        default=BillingInterval.MONTHLY,
        nullable=False
    )

    # Billing period
    current_period_start = Column(DateTime(timezone=True), nullable=True)
    current_period_end = Column(DateTime(timezone=True), nullable=True)

    # Cancellation
    cancel_at_period_end = Column(Boolean, default=False, nullable=False)
    canceled_at = Column(DateTime(timezone=True), nullable=True)

    # Usage tracking
    videos_used_this_month = Column(Integer, default=0, nullable=False)
    usage_reset_date = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    user = relationship("User", backref="subscriptions")
    plan = relationship("Plan", backref="subscriptions")

    def __repr__(self):
        return f"<Subscription(id={self.id}, user_id={self.user_id}, plan_id={self.plan_id}, status={self.status})>"
