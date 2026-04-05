"""
Analytics service for CineCraft.
Business logic for usage tracking and reporting.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

from app.repositories.analytics import AnalyticsRepository
from app.models.analytics_log import EventType
from app.core.logging import get_logger

logger = get_logger(__name__)


class AnalyticsService:
    """Service for analytics operations."""

    def __init__(self, db: Session):
        self.db = db
        self.analytics_repo = AnalyticsRepository(db)

    def log_event(
        self,
        event_type: str,
        user_id: Optional[int] = None,
        project_id: Optional[int] = None,
        job_id: Optional[int] = None,
        event_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Log an analytics event.

        Args:
            event_type: Type of event
            user_id: Optional user ID
            project_id: Optional project ID
            job_id: Optional job ID
            event_data: Optional event-specific data
            **kwargs: Additional fields
        """
        try:
            self.analytics_repo.log_event(
                event_type=event_type,
                user_id=user_id,
                project_id=project_id,
                job_id=job_id,
                event_data=event_data,
                **kwargs
            )
        except Exception as e:
            # Don't fail requests if analytics logging fails
            logger.error(f"Failed to log analytics event: {e}")

    def log_api_call(
        self,
        endpoint: str,
        method: str,
        status_code: int,
        response_time_ms: float,
        user_id: Optional[int] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """
        Log an API call.

        Args:
            endpoint: API endpoint
            method: HTTP method
            status_code: Response status code
            response_time_ms: Response time in milliseconds
            user_id: Optional user ID
            ip_address: Optional IP address
            user_agent: Optional user agent
        """
        self.log_event(
            event_type=EventType.API_CALL.value,
            event_category="api",
            user_id=user_id,
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            response_time_ms=response_time_ms,
            ip_address=ip_address,
            user_agent=user_agent
        )

    def log_user_signup(self, user_id: int, ip_address: Optional[str] = None):
        """Log user signup event."""
        self.log_event(
            event_type=EventType.USER_SIGNUP.value,
            event_category="auth",
            user_id=user_id,
            ip_address=ip_address
        )

    def log_user_login(self, user_id: int, ip_address: Optional[str] = None):
        """Log user login event."""
        self.log_event(
            event_type=EventType.USER_LOGIN.value,
            event_category="auth",
            user_id=user_id,
            ip_address=ip_address
        )

    def log_project_created(self, user_id: int, project_id: int):
        """Log project creation event."""
        self.log_event(
            event_type=EventType.PROJECT_CREATED.value,
            event_category="project",
            user_id=user_id,
            project_id=project_id
        )

    def log_story_generated(
        self,
        user_id: int,
        project_id: int,
        duration_seconds: float,
        cost_cents: int
    ):
        """Log story generation event."""
        self.log_event(
            event_type=EventType.STORY_GENERATED.value,
            event_category="ai",
            user_id=user_id,
            project_id=project_id,
            duration_seconds=duration_seconds,
            cost_cents=cost_cents
        )

    def log_image_generated(
        self,
        user_id: int,
        project_id: int,
        duration_seconds: float,
        cost_cents: int
    ):
        """Log image generation event."""
        self.log_event(
            event_type=EventType.IMAGE_GENERATED.value,
            event_category="ai",
            user_id=user_id,
            project_id=project_id,
            duration_seconds=duration_seconds,
            cost_cents=cost_cents
        )

    def log_voice_generated(
        self,
        user_id: int,
        project_id: int,
        duration_seconds: float,
        cost_cents: int
    ):
        """Log voice generation event."""
        self.log_event(
            event_type=EventType.VOICE_GENERATED.value,
            event_category="ai",
            user_id=user_id,
            project_id=project_id,
            duration_seconds=duration_seconds,
            cost_cents=cost_cents
        )

    def log_music_generated(
        self,
        user_id: int,
        project_id: int,
        duration_seconds: float,
        cost_cents: int
    ):
        """Log music generation event."""
        self.log_event(
            event_type=EventType.MUSIC_GENERATED.value,
            event_category="ai",
            user_id=user_id,
            project_id=project_id,
            duration_seconds=duration_seconds,
            cost_cents=cost_cents
        )

    def log_video_render_started(
        self,
        user_id: int,
        project_id: int,
        job_id: int
    ):
        """Log video render started event."""
        self.log_event(
            event_type=EventType.VIDEO_RENDER_STARTED.value,
            event_category="rendering",
            user_id=user_id,
            project_id=project_id,
            job_id=job_id
        )

    def log_video_render_completed(
        self,
        user_id: int,
        project_id: int,
        job_id: int,
        duration_seconds: float,
        file_size_bytes: int
    ):
        """Log video render completed event."""
        self.log_event(
            event_type=EventType.VIDEO_RENDER_COMPLETED.value,
            event_category="rendering",
            user_id=user_id,
            project_id=project_id,
            job_id=job_id,
            duration_seconds=duration_seconds,
            file_size_bytes=file_size_bytes
        )

    def log_video_render_failed(
        self,
        user_id: int,
        project_id: int,
        job_id: int,
        error_type: str,
        error_message: str
    ):
        """Log video render failed event."""
        self.log_event(
            event_type=EventType.VIDEO_RENDER_FAILED.value,
            event_category="rendering",
            user_id=user_id,
            project_id=project_id,
            job_id=job_id,
            error_type=error_type,
            error_message=error_message
        )

    def log_subscription_created(
        self,
        user_id: int,
        plan_id: int,
        amount_cents: int
    ):
        """Log subscription creation event."""
        self.log_event(
            event_type=EventType.SUBSCRIPTION_CREATED.value,
            event_category="subscription",
            user_id=user_id,
            cost_cents=amount_cents,
            event_data={"plan_id": plan_id}
        )

    def log_file_uploaded(
        self,
        user_id: int,
        project_id: Optional[int],
        file_size_bytes: int,
        file_type: str
    ):
        """Log file upload event."""
        self.log_event(
            event_type=EventType.FILE_UPLOADED.value,
            event_category="storage",
            user_id=user_id,
            project_id=project_id,
            file_size_bytes=file_size_bytes,
            event_data={"file_type": file_type}
        )

    def get_user_stats(
        self,
        user_id: int,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get usage statistics for a user.

        Args:
            user_id: User ID
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            User statistics dictionary
        """
        return self.analytics_repo.get_user_stats(user_id, start_date, end_date)

    def get_system_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """
        Get system-wide statistics.

        Args:
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            System statistics dictionary
        """
        return self.analytics_repo.get_system_stats(start_date, end_date)

    def get_daily_stats(self, days: int = 30) -> List[Dict[str, Any]]:
        """
        Get daily statistics for the last N days.

        Args:
            days: Number of days

        Returns:
            List of daily statistics
        """
        return self.analytics_repo.get_daily_stats(days)

    def get_top_endpoints(
        self,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get most called API endpoints.

        Args:
            limit: Number of endpoints
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            List of endpoint statistics
        """
        return self.analytics_repo.get_top_endpoints(limit, start_date, end_date)

    def get_slowest_endpoints(
        self,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get slowest API endpoints.

        Args:
            limit: Number of endpoints
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            List of endpoint statistics
        """
        return self.analytics_repo.get_slowest_endpoints(limit, start_date, end_date)

    def get_user_activity_timeline(
        self,
        user_id: int,
        days: int = 7
    ) -> List[Dict[str, Any]]:
        """
        Get user activity timeline.

        Args:
            user_id: User ID
            days: Number of days to include

        Returns:
            List of recent activities
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        logs = self.analytics_repo.get_by_user(
            user_id=user_id,
            start_date=start_date,
            limit=100
        )

        return [
            {
                "event_type": log.event_type,
                "event_category": log.event_category,
                "timestamp": log.created_at.isoformat(),
                "project_id": log.project_id,
                "event_data": log.event_data
            }
            for log in logs
        ]

    def cleanup_old_logs(self, days: int = 90) -> int:
        """
        Delete old analytics logs.

        Args:
            days: Age threshold in days

        Returns:
            Number of logs deleted
        """
        deleted = self.analytics_repo.cleanup_old_logs(days)
        logger.info(f"Cleaned up {deleted} analytics logs older than {days} days")
        return deleted
