"""
Pydantic schemas for webhook events.
"""
from pydantic import BaseModel
from typing import Any, Optional


class WebhookEventResponse(BaseModel):
    """Schema for webhook event response."""
    status: str
    event_type: Optional[str] = None
    message: Optional[str] = None
    details: Optional[dict] = None
