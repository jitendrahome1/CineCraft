"""
Analytics log model for CineCraft.
Tracks usage events, API calls, and user activities.
"""
from sqlalchemy import Column, Integer, String, Float, JSON, ForeignKey, Index
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class EventType(str, enum.Enum):
    """Analytics event types."""
    # User events
    USER_SIGNUP = "user_signup"
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"

    # Project events
    PROJECT_CREATED = "project_created"
    PROJECT_UPDATED = "project_updated"
    PROJECT_DELETED = "project_deleted"

    # Story generation events
    STORY_GENERATED = "story_generated"
    SCENE_GENERATED = "scene_generated"

    # Media generation events
    IMAGE_GENERATED = "image_generated"
    VOICE_GENERATED = "voice_generated"
    MUSIC_GENERATED = "music_generated"

    # Rendering events
    VIDEO_RENDER_STARTED = "video_render_started"
    VIDEO_RENDER_COMPLETED = "video_render_completed"
    VIDEO_RENDER_FAILED = "video_render_failed"

    # API events
    API_CALL = "api_call"
    API_ERROR = "api_error"

    # Subscription events
    SUBSCRIPTION_CREATED = "subscription_created"
    SUBSCRIPTION_UPDATED = "subscription_updated"
    SUBSCRIPTION_CANCELLED = "subscription_cancelled"

    # Storage events
    FILE_UPLOADED = "file_uploaded"
    FILE_DOWNLOADED = "file_downloaded"
    FILE_DELETED = "file_deleted"

    # Feature usage
    FEATURE_USED = "feature_used"


class AnalyticsLog(BaseModel):
    """
    Analytics log model for tracking user activities and system events.

    Stores structured event data for reporting and analysis.
    """
    __tablename__ = "analytics_logs"

    # Event info
    event_type = Column(String(50), nullable=False, index=True)
    event_category = Column(String(50), nullable=True, index=True)  # e.g., "rendering", "ai", "auth"

    # User context
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    user = relationship("User", backref="analytics_logs")

    # Resource references
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=True, index=True)
    job_id = Column(Integer, ForeignKey("render_jobs.id"), nullable=True, index=True)

    # Request context
    ip_address = Column(String(50), nullable=True)
    user_agent = Column(String(500), nullable=True)
    endpoint = Column(String(200), nullable=True, index=True)
    method = Column(String(10), nullable=True)  # GET, POST, etc.

    # Response info
    status_code = Column(Integer, nullable=True, index=True)
    response_time_ms = Column(Float, nullable=True)

    # Event data
    event_data = Column(JSON, nullable=True)  # Flexible event-specific data

    # Metrics
    duration_seconds = Column(Float, nullable=True)  # For timed events
    file_size_bytes = Column(Integer, nullable=True)  # For file operations
    cost_cents = Column(Integer, nullable=True)  # For paid operations

    # Error tracking
    error_type = Column(String(100), nullable=True)
    error_message = Column(String(500), nullable=True)

    # Metadata
    tags = Column(JSON, nullable=True)  # List of tags for filtering

    # Indexes for common queries
    __table_args__ = (
        Index('idx_analytics_user_event', 'user_id', 'event_type'),
        Index('idx_analytics_project', 'project_id', 'event_type'),
        Index('idx_analytics_date_event', 'created_at', 'event_type'),
        Index('idx_analytics_category', 'event_category', 'created_at'),
    )

    def __repr__(self):
        return f"<AnalyticsLog {self.event_type} user={self.user_id}>"

    @property
    def is_api_call(self) -> bool:
        """Check if this is an API call event."""
        return self.event_type in [EventType.API_CALL, EventType.API_ERROR]

    @property
    def is_error(self) -> bool:
        """Check if this is an error event."""
        return self.status_code and self.status_code >= 400

    @property
    def is_successful(self) -> bool:
        """Check if this is a successful event."""
        return self.status_code and 200 <= self.status_code < 400
