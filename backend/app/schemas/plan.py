"""
Pydantic schemas for Plan model.
"""
from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class PlanBase(BaseModel):
    """Base plan schema."""
    name: str
    price_monthly: float
    price_yearly: float
    currency: str = "USD"
    max_videos_per_month: Optional[int] = None
    max_video_duration: int
    max_resolution: str
    features: dict = {}


class PlanResponse(PlanBase):
    """Schema for plan response."""
    id: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
