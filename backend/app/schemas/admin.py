"""
Pydantic schemas for admin operations.
"""
from pydantic import BaseModel, Field, EmailStr
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.models.user import UserRole
from app.models.feature_flag import FeatureFlagType, FeatureFlagScope


# Feature Flag Schemas

class FeatureFlagCreate(BaseModel):
    """Schema for creating a feature flag."""
    key: str = Field(..., min_length=1, max_length=100)
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    flag_type: FeatureFlagType = FeatureFlagType.BOOLEAN
    scope: FeatureFlagScope = FeatureFlagScope.GLOBAL
    enabled: bool = False
    value_string: Optional[str] = None
    value_number: Optional[int] = None
    value_json: Optional[Dict[str, Any]] = None
    target_user_ids: Optional[List[int]] = None
    target_plan_ids: Optional[List[int]] = None
    target_roles: Optional[List[str]] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    rollout_percentage: int = Field(default=100, ge=0, le=100)


class FeatureFlagUpdate(BaseModel):
    """Schema for updating a feature flag."""
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    enabled: Optional[bool] = None
    value_string: Optional[str] = None
    value_number: Optional[int] = None
    value_json: Optional[Dict[str, Any]] = None
    target_user_ids: Optional[List[int]] = None
    target_plan_ids: Optional[List[int]] = None
    target_roles: Optional[List[str]] = None
    category: Optional[str] = None
    tags: Optional[List[str]] = None
    rollout_percentage: Optional[int] = Field(None, ge=0, le=100)


class FeatureFlagResponse(BaseModel):
    """Schema for feature flag response."""
    id: int
    key: str
    name: str
    description: Optional[str]
    flag_type: str
    scope: str
    enabled: bool
    value_string: Optional[str]
    value_number: Optional[int]
    value_json: Optional[Dict[str, Any]]
    target_user_ids: Optional[List[int]]
    target_plan_ids: Optional[List[int]]
    target_roles: Optional[List[str]]
    category: Optional[str]
    tags: Optional[List[str]]
    rollout_percentage: int
    created_by: Optional[int]
    updated_by: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class FeatureFlagListResponse(BaseModel):
    """Schema for feature flag list."""
    flags: List[FeatureFlagResponse]
    total: int
    skip: int
    limit: int


class FeatureFlagStatsResponse(BaseModel):
    """Schema for feature flag statistics."""
    total: int
    enabled: int
    disabled: int
    by_scope: Dict[str, int]
    by_type: Dict[str, int]


# User Management Schemas

class AdminUserUpdate(BaseModel):
    """Schema for admin updating user."""
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None
    role: Optional[UserRole] = None
    is_active: Optional[bool] = None


class AdminUserResponse(BaseModel):
    """Schema for admin user response."""
    id: int
    email: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    is_email_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]

    class Config:
        from_attributes = True


class AdminUserListResponse(BaseModel):
    """Schema for user list."""
    users: List[AdminUserResponse]
    total: int
    skip: int
    limit: int


class UserBanRequest(BaseModel):
    """Schema for banning a user."""
    reason: Optional[str] = None


# System Health Schemas

class SystemHealthResponse(BaseModel):
    """Schema for system health check."""
    status: str
    database: str
    redis: str
    celery_workers: int
    websocket_connections: int
    timestamp: datetime


class SystemStatsResponse(BaseModel):
    """Schema for system statistics."""
    total_users: int
    active_users: int
    total_projects: int
    total_render_jobs: int
    completed_jobs: int
    failed_jobs: int
    active_subscriptions: int
    total_revenue: float
    storage_used_gb: float
    timestamp: datetime


# Job Monitoring Schemas

class AdminJobResponse(BaseModel):
    """Schema for admin job response."""
    id: int
    user_id: int
    user_email: str
    project_id: int
    project_title: str
    job_type: str
    status: str
    progress: float
    current_stage: Optional[str]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    created_at: datetime


class AdminJobListResponse(BaseModel):
    """Schema for admin job list."""
    jobs: List[AdminJobResponse]
    total: int
    skip: int
    limit: int


# Subscription Management Schemas

class AdminSubscriptionResponse(BaseModel):
    """Schema for admin subscription response."""
    id: int
    user_id: int
    user_email: str
    plan_id: int
    plan_name: str
    status: str
    current_period_start: datetime
    current_period_end: datetime
    cancel_at_period_end: bool
    created_at: datetime
    updated_at: datetime


class AdminSubscriptionListResponse(BaseModel):
    """Schema for admin subscription list."""
    subscriptions: List[AdminSubscriptionResponse]
    total: int
    skip: int
    limit: int


# Analytics Schemas

class AdminAnalyticsResponse(BaseModel):
    """Schema for admin analytics."""
    period: str  # "day", "week", "month"
    users_created: int
    projects_created: int
    videos_rendered: int
    revenue: float
    storage_used_gb: float
    api_calls: int
    avg_render_time_seconds: float
    timestamp: datetime


class AdminAnalyticsListResponse(BaseModel):
    """Schema for admin analytics list."""
    analytics: List[AdminAnalyticsResponse]
    summary: Dict[str, Any]
