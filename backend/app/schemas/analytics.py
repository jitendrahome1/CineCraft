"""
Pydantic schemas for analytics operations.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime


class AnalyticsLogResponse(BaseModel):
    """Schema for analytics log response."""
    id: int
    event_type: str
    event_category: Optional[str]
    user_id: Optional[int]
    project_id: Optional[int]
    job_id: Optional[int]
    endpoint: Optional[str]
    method: Optional[str]
    status_code: Optional[int]
    response_time_ms: Optional[float]
    event_data: Optional[Dict[str, Any]]
    duration_seconds: Optional[float]
    file_size_bytes: Optional[int]
    cost_cents: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class AnalyticsLogListResponse(BaseModel):
    """Schema for analytics log list."""
    logs: List[AnalyticsLogResponse]
    total: int
    skip: int
    limit: int


class UserStatsResponse(BaseModel):
    """Schema for user statistics."""
    user_id: int
    event_counts: Dict[str, int]
    total_events: int
    api_calls: int
    total_cost_cents: int
    avg_response_time_ms: float


class SystemStatsResponse(BaseModel):
    """Schema for system statistics."""
    event_counts: Dict[str, int]
    total_events: int
    unique_users: int
    api_calls: int
    error_rate: float
    avg_response_time_ms: float


class DailyStatsResponse(BaseModel):
    """Schema for daily statistics."""
    date: str
    events: Dict[str, int]


class DailyStatsListResponse(BaseModel):
    """Schema for list of daily statistics."""
    stats: List[DailyStatsResponse]
    period: str  # e.g., "last_30_days"


class EndpointStatsResponse(BaseModel):
    """Schema for endpoint statistics."""
    endpoint: str
    method: str
    count: int
    avg_response_time_ms: float


class EndpointStatsListResponse(BaseModel):
    """Schema for list of endpoint statistics."""
    endpoints: List[EndpointStatsResponse]
    total: int


class UserActivityResponse(BaseModel):
    """Schema for user activity."""
    event_type: str
    event_category: Optional[str]
    timestamp: str
    project_id: Optional[int]
    event_data: Optional[Dict[str, Any]]


class UserActivityTimelineResponse(BaseModel):
    """Schema for user activity timeline."""
    user_id: int
    activities: List[UserActivityResponse]
    period_days: int


class AnalyticsSummaryResponse(BaseModel):
    """Schema for analytics summary dashboard."""
    period: str
    start_date: datetime
    end_date: datetime

    # User metrics
    total_users: int
    active_users: int
    new_signups: int

    # Content metrics
    projects_created: int
    videos_rendered: int
    stories_generated: int
    images_generated: int

    # System metrics
    total_api_calls: int
    avg_response_time_ms: float
    error_rate: float

    # Financial metrics
    total_revenue_cents: int
    subscriptions_created: int

    # Performance
    total_render_time_seconds: float
    avg_render_time_seconds: float


class AnalyticsRevenueResponse(BaseModel):
    """Schema for revenue analytics."""
    period: str
    total_revenue_cents: int
    subscriptions_created: int
    subscriptions_cancelled: int
    revenue_by_plan: Dict[str, int]
    mrr_cents: int  # Monthly Recurring Revenue


class AnalyticsUsageResponse(BaseModel):
    """Schema for usage analytics."""
    period: str
    videos_rendered: int
    total_render_time_seconds: float
    storage_used_bytes: int
    api_calls: int
    ai_generations: Dict[str, int]  # by type


class AnalyticsPerformanceResponse(BaseModel):
    """Schema for performance analytics."""
    period: str
    avg_response_time_ms: float
    p50_response_time_ms: float
    p95_response_time_ms: float
    p99_response_time_ms: float
    error_rate: float
    slowest_endpoints: List[EndpointStatsResponse]


class AnalyticsEngagementResponse(BaseModel):
    """Schema for user engagement analytics."""
    period: str
    dau: int  # Daily Active Users
    wau: int  # Weekly Active Users
    mau: int  # Monthly Active Users
    retention_rate: float
    churn_rate: float
    avg_session_duration_minutes: float
