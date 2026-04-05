"""
Pydantic schemas for Subscription model.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from app.models.subscription import SubscriptionStatus, BillingInterval


class CheckoutSessionRequest(BaseModel):
    """Schema for creating checkout session."""
    plan_id: int
    billing_interval: str = "monthly"  # "monthly" or "yearly"
    success_url: Optional[str] = None
    cancel_url: Optional[str] = None


class CheckoutSessionResponse(BaseModel):
    """Schema for checkout session response."""
    session_id: str
    url: str
    customer_id: str


class SubscriptionResponse(BaseModel):
    """Schema for subscription response."""
    id: int
    user_id: int
    plan_id: int
    status: SubscriptionStatus
    billing_interval: BillingInterval
    current_period_start: Optional[datetime]
    current_period_end: Optional[datetime]
    cancel_at_period_end: bool
    videos_used_this_month: int
    created_at: datetime

    class Config:
        from_attributes = True


class SubscriptionWithPlanResponse(BaseModel):
    """Schema for subscription with plan details."""
    subscription: SubscriptionResponse
    plan: dict
    usage: dict


class CancelSubscriptionRequest(BaseModel):
    """Schema for canceling subscription."""
    at_period_end: bool = True


class CustomerPortalResponse(BaseModel):
    """Schema for customer portal session."""
    url: str
