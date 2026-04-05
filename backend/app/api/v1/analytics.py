"""
Analytics API endpoints for CineCraft.
Provides usage tracking and reporting endpoints.
"""
from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.api.deps import get_current_user, get_current_admin_user
from app.models.user import User
from app.services.analytics import AnalyticsService
from app.schemas.analytics import (
    AnalyticsLogResponse,
    AnalyticsLogListResponse,
    UserStatsResponse,
    SystemStatsResponse,
    DailyStatsResponse,
    DailyStatsListResponse,
    EndpointStatsResponse,
    EndpointStatsListResponse,
    UserActivityResponse,
    UserActivityTimelineResponse,
    AnalyticsSummaryResponse,
    AnalyticsRevenueResponse,
    AnalyticsUsageResponse,
    AnalyticsPerformanceResponse,
    AnalyticsEngagementResponse
)
from app.core.logging import get_logger

logger = get_logger(__name__)
router = APIRouter()


def get_analytics_service(db: Session = Depends(get_db)) -> AnalyticsService:
    """Dependency to get analytics service."""
    return AnalyticsService(db)


# User Analytics Endpoints

@router.get("/users/me/stats", response_model=UserStatsResponse)
async def get_my_stats(
    start_date: Optional[datetime] = Query(None, description="Start date for stats"),
    end_date: Optional[datetime] = Query(None, description="End date for stats"),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get usage statistics for the current user.

    Returns event counts, API calls, costs, and performance metrics.
    """
    try:
        stats = analytics_service.get_user_stats(
            user_id=current_user.id,
            start_date=start_date,
            end_date=end_date
        )
        return stats
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )


@router.get("/users/me/activity", response_model=UserActivityTimelineResponse)
async def get_my_activity(
    days: int = Query(7, ge=1, le=90, description="Number of days to include"),
    current_user: User = Depends(get_current_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get activity timeline for the current user.

    Returns recent activities within the specified time period.
    """
    try:
        activities = analytics_service.get_user_activity_timeline(
            user_id=current_user.id,
            days=days
        )

        return UserActivityTimelineResponse(
            user_id=current_user.id,
            activities=[
                UserActivityResponse(
                    event_type=activity["event_type"],
                    event_category=activity["event_category"],
                    timestamp=activity["timestamp"],
                    project_id=activity["project_id"],
                    event_data=activity["event_data"]
                )
                for activity in activities
            ],
            period_days=days
        )
    except Exception as e:
        logger.error(f"Error getting user activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user activity"
        )


@router.get("/users/{user_id}/stats", response_model=UserStatsResponse)
async def get_user_stats(
    user_id: int,
    start_date: Optional[datetime] = Query(None, description="Start date for stats"),
    end_date: Optional[datetime] = Query(None, description="End date for stats"),
    current_user: User = Depends(get_current_admin_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get usage statistics for a specific user (admin only).

    Returns event counts, API calls, costs, and performance metrics.
    """
    try:
        stats = analytics_service.get_user_stats(
            user_id=user_id,
            start_date=start_date,
            end_date=end_date
        )
        return stats
    except Exception as e:
        logger.error(f"Error getting user stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user statistics"
        )


@router.get("/users/{user_id}/activity", response_model=UserActivityTimelineResponse)
async def get_user_activity(
    user_id: int,
    days: int = Query(7, ge=1, le=90, description="Number of days to include"),
    current_user: User = Depends(get_current_admin_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get activity timeline for a specific user (admin only).

    Returns recent activities within the specified time period.
    """
    try:
        activities = analytics_service.get_user_activity_timeline(
            user_id=user_id,
            days=days
        )

        return UserActivityTimelineResponse(
            user_id=user_id,
            activities=[
                UserActivityResponse(
                    event_type=activity["event_type"],
                    event_category=activity["event_category"],
                    timestamp=activity["timestamp"],
                    project_id=activity["project_id"],
                    event_data=activity["event_data"]
                )
                for activity in activities
            ],
            period_days=days
        )
    except Exception as e:
        logger.error(f"Error getting user activity: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve user activity"
        )


# System Analytics Endpoints

@router.get("/system/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    start_date: Optional[datetime] = Query(None, description="Start date for stats"),
    end_date: Optional[datetime] = Query(None, description="End date for stats"),
    current_user: User = Depends(get_current_admin_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get system-wide statistics (admin only).

    Returns event counts, user counts, API calls, and error rates.
    """
    try:
        stats = analytics_service.get_system_stats(
            start_date=start_date,
            end_date=end_date
        )
        return stats
    except Exception as e:
        logger.error(f"Error getting system stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system statistics"
        )


@router.get("/system/daily", response_model=DailyStatsListResponse)
async def get_daily_stats(
    days: int = Query(30, ge=1, le=365, description="Number of days to include"),
    current_user: User = Depends(get_current_admin_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get daily statistics (admin only).

    Returns event counts grouped by date for the specified period.
    """
    try:
        stats = analytics_service.get_daily_stats(days=days)

        return DailyStatsListResponse(
            stats=[
                DailyStatsResponse(
                    date=stat["date"],
                    events=stat["events"]
                )
                for stat in stats
            ],
            period=f"last_{days}_days"
        )
    except Exception as e:
        logger.error(f"Error getting daily stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve daily statistics"
        )


# Performance Analytics Endpoints

@router.get("/performance/endpoints", response_model=EndpointStatsListResponse)
async def get_top_endpoints(
    limit: int = Query(10, ge=1, le=100, description="Number of endpoints to return"),
    start_date: Optional[datetime] = Query(None, description="Start date for stats"),
    end_date: Optional[datetime] = Query(None, description="End date for stats"),
    current_user: User = Depends(get_current_admin_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get most called API endpoints (admin only).

    Returns endpoints sorted by call count with average response times.
    """
    try:
        endpoints = analytics_service.get_top_endpoints(
            limit=limit,
            start_date=start_date,
            end_date=end_date
        )

        return EndpointStatsListResponse(
            endpoints=[
                EndpointStatsResponse(
                    endpoint=ep["endpoint"],
                    method=ep["method"],
                    count=ep["count"],
                    avg_response_time_ms=ep["avg_response_time_ms"]
                )
                for ep in endpoints
            ],
            total=len(endpoints)
        )
    except Exception as e:
        logger.error(f"Error getting top endpoints: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve endpoint statistics"
        )


@router.get("/performance/slowest", response_model=EndpointStatsListResponse)
async def get_slowest_endpoints(
    limit: int = Query(10, ge=1, le=100, description="Number of endpoints to return"),
    start_date: Optional[datetime] = Query(None, description="Start date for stats"),
    end_date: Optional[datetime] = Query(None, description="End date for stats"),
    current_user: User = Depends(get_current_admin_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Get slowest API endpoints (admin only).

    Returns endpoints sorted by average response time.
    """
    try:
        endpoints = analytics_service.get_slowest_endpoints(
            limit=limit,
            start_date=start_date,
            end_date=end_date
        )

        return EndpointStatsListResponse(
            endpoints=[
                EndpointStatsResponse(
                    endpoint=ep["endpoint"],
                    method=ep["method"],
                    count=ep["count"],
                    avg_response_time_ms=ep["avg_response_time_ms"]
                )
                for ep in endpoints
            ],
            total=len(endpoints)
        )
    except Exception as e:
        logger.error(f"Error getting slowest endpoints: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve endpoint statistics"
        )


# Maintenance Endpoints

@router.post("/maintenance/cleanup", status_code=status.HTTP_200_OK)
async def cleanup_old_logs(
    days: int = Query(90, ge=30, le=365, description="Age threshold in days"),
    current_user: User = Depends(get_current_admin_user),
    analytics_service: AnalyticsService = Depends(get_analytics_service)
):
    """
    Delete old analytics logs (admin only).

    Removes logs older than the specified number of days.
    """
    try:
        deleted = analytics_service.cleanup_old_logs(days=days)
        return {
            "message": f"Cleaned up {deleted} analytics logs older than {days} days",
            "deleted_count": deleted,
            "threshold_days": days
        }
    except Exception as e:
        logger.error(f"Error cleaning up logs: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to clean up analytics logs"
        )


# Health check endpoint
@router.get("/health", status_code=status.HTTP_200_OK)
async def analytics_health():
    """
    Health check endpoint for analytics service.
    """
    return {
        "status": "healthy",
        "service": "analytics",
        "timestamp": datetime.utcnow().isoformat()
    }
