"""
Subscription plan model.
Defines available subscription tiers and their features.
"""
from sqlalchemy import Column, String, Integer, Boolean, Numeric, JSON
from app.models.base import BaseModel


class Plan(BaseModel):
    """
    Subscription plan model.

    Attributes:
        name: Plan name (Free, Pro, Enterprise)
        stripe_price_id: Stripe Price ID for this plan
        price_monthly: Monthly price in dollars
        price_yearly: Yearly price in dollars
        currency: Currency code (default: USD)
        max_videos_per_month: Maximum videos per month (null = unlimited)
        max_video_duration: Maximum video duration in seconds
        max_resolution: Maximum video resolution (e.g., "1080p", "4k")
        features: JSON object with plan features
        is_active: Whether plan is active and available
    """
    __tablename__ = "plans"

    name = Column(String(50), unique=True, nullable=False, index=True)
    stripe_price_id_monthly = Column(String(255), nullable=True)
    stripe_price_id_yearly = Column(String(255), nullable=True)
    price_monthly = Column(Numeric(10, 2), nullable=False, default=0)
    price_yearly = Column(Numeric(10, 2), nullable=False, default=0)
    currency = Column(String(3), nullable=False, default="USD")

    # Usage limits
    max_videos_per_month = Column(Integer, nullable=True)  # null = unlimited
    max_video_duration = Column(Integer, nullable=False, default=300)  # seconds
    max_resolution = Column(String(20), nullable=False, default="720p")

    # Features (stored as JSON)
    features = Column(JSON, nullable=False, default=dict)

    # Status
    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self):
        return f"<Plan(id={self.id}, name={self.name}, price_monthly=${self.price_monthly})>"
