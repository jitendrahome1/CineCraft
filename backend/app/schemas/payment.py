"""
Pydantic schemas for Payment model.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PaymentResponse(BaseModel):
    """Schema for payment response."""
    id: int
    user_id: int
    subscription_id: Optional[int]
    amount: float
    currency: str
    status: str
    payment_method: Optional[str]
    receipt_url: Optional[str]
    paid_at: Optional[datetime]
    refunded: bool
    created_at: datetime

    class Config:
        from_attributes = True
