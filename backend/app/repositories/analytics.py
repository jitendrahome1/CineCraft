"""
Analytics repository for CineCraft.
Data access layer for analytics logs.
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import func, and_, or_

from app.repositories.base import BaseRepository
from app.models.analytics_log import AnalyticsLog, EventType


class AnalyticsRepository(BaseRepository[AnalyticsLog]):
    """Repository for analytics operations."""

    def __init__(self, db: Session):
        super().__init__(AnalyticsLog, db)

    def log_event(
        self,
        event_type: str,
        user_id: Optional[int] = None,
        event_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ) -> AnalyticsLog:
        """
        Log an analytics event.

        Args:
            event_type: Type of event
            user_id: Optional user ID
            event_data: Optional event-specific data
            **kwargs: Additional fields

        Returns:
            Created analytics log
        """
        data = {
            "event_type": event_type,
            "user_id": user_id,
            "event_data": event_data,
            **kwargs
        }

        return self.create(data)

    def get_by_user(
        self,
        user_id: int,
        event_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AnalyticsLog]:
        """
        Get analytics logs for a user.

        Args:
            user_id: User ID
            event_type: Optional event type filter
            start_date: Optional start date
            end_date: Optional end date
            skip: Number to skip
            limit: Maximum number to return

        Returns:
            List of analytics logs
        """
        query = self.db.query(AnalyticsLog).filter(
            AnalyticsLog.user_id == user_id
        )

        if event_type:
            query = query.filter(AnalyticsLog.event_type == event_type)

        if start_date:
            query = query.filter(AnalyticsLog.created_at >= start_date)

        if end_date:
            query = query.filter(AnalyticsLog.created_at <= end_date)

        return query.order_by(AnalyticsLog.created_at.desc()).offset(skip).limit(limit).all()

    def get_by_project(
        self,
        project_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[AnalyticsLog]:
        """
        Get analytics logs for a project.

        Args:
            project_id: Project ID
            skip: Number to skip
            limit: Maximum number to return

        Returns:
            List of analytics logs
        """
        return self.db.query(AnalyticsLog).filter(
            AnalyticsLog.project_id == project_id
        ).order_by(AnalyticsLog.created_at.desc()).offset(skip).limit(limit).all()

    def get_by_event_type(
        self,
        event_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[AnalyticsLog]:
        """
        Get analytics logs by event type.

        Args:
            event_type: Event type
            start_date: Optional start date
            end_date: Optional end date
            skip: Number to skip
            limit: Maximum number to return

        Returns:
            List of analytics logs
        """
        query = self.db.query(AnalyticsLog).filter(
            AnalyticsLog.event_type == event_type
        )

        if start_date:
            query = query.filter(AnalyticsLog.created_at >= start_date)

        if end_date:
            query = query.filter(AnalyticsLog.created_at <= end_date)

        return query.order_by(AnalyticsLog.created_at.desc()).offset(skip).limit(limit).all()

    def count_by_event_type(
        self,
        event_type: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> int:
        """
        Count events by type.

        Args:
            event_type: Event type
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            Event count
        """
        query = self.db.query(func.count(AnalyticsLog.id)).filter(
            AnalyticsLog.event_type == event_type
        )

        if start_date:
            query = query.filter(AnalyticsLog.created_at >= start_date)

        if end_date:
            query = query.filter(AnalyticsLog.created_at <= end_date)

        return query.scalar() or 0

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
            Dictionary with statistics
        """
        query = self.db.query(AnalyticsLog).filter(
            AnalyticsLog.user_id == user_id
        )

        if start_date:
            query = query.filter(AnalyticsLog.created_at >= start_date)

        if end_date:
            query = query.filter(AnalyticsLog.created_at <= end_date)

        # Count by event type
        event_counts = {}
        for event_type in EventType:
            count = query.filter(
                AnalyticsLog.event_type == event_type.value
            ).count()
            if count > 0:
                event_counts[event_type.value] = count

        # Total API calls
        api_calls = query.filter(
            AnalyticsLog.event_type == EventType.API_CALL.value
        ).count()

        # Total cost
        total_cost = query.with_entities(
            func.sum(AnalyticsLog.cost_cents)
        ).scalar() or 0

        # Average response time
        avg_response_time = query.filter(
            AnalyticsLog.response_time_ms.isnot(None)
        ).with_entities(
            func.avg(AnalyticsLog.response_time_ms)
        ).scalar() or 0

        return {
            "user_id": user_id,
            "event_counts": event_counts,
            "total_events": sum(event_counts.values()),
            "api_calls": api_calls,
            "total_cost_cents": int(total_cost),
            "avg_response_time_ms": float(avg_response_time)
        }

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
            Dictionary with statistics
        """
        query = self.db.query(AnalyticsLog)

        if start_date:
            query = query.filter(AnalyticsLog.created_at >= start_date)

        if end_date:
            query = query.filter(AnalyticsLog.created_at <= end_date)

        # Count by event type
        event_counts = {}
        for event_type in EventType:
            count = query.filter(
                AnalyticsLog.event_type == event_type.value
            ).count()
            if count > 0:
                event_counts[event_type.value] = count

        # Unique users
        unique_users = query.filter(
            AnalyticsLog.user_id.isnot(None)
        ).with_entities(
            func.count(func.distinct(AnalyticsLog.user_id))
        ).scalar() or 0

        # Total API calls
        api_calls = query.filter(
            AnalyticsLog.event_type == EventType.API_CALL.value
        ).count()

        # Error rate
        total_requests = query.filter(
            AnalyticsLog.status_code.isnot(None)
        ).count()

        error_requests = query.filter(
            AnalyticsLog.status_code >= 400
        ).count()

        error_rate = (error_requests / total_requests * 100) if total_requests > 0 else 0

        # Average response time
        avg_response_time = query.filter(
            AnalyticsLog.response_time_ms.isnot(None)
        ).with_entities(
            func.avg(AnalyticsLog.response_time_ms)
        ).scalar() or 0

        return {
            "event_counts": event_counts,
            "total_events": sum(event_counts.values()),
            "unique_users": unique_users,
            "api_calls": api_calls,
            "error_rate": round(error_rate, 2),
            "avg_response_time_ms": float(avg_response_time)
        }

    def get_daily_stats(
        self,
        days: int = 30
    ) -> List[Dict[str, Any]]:
        """
        Get daily statistics for the last N days.

        Args:
            days: Number of days to include

        Returns:
            List of daily statistics
        """
        start_date = datetime.utcnow() - timedelta(days=days)

        # Query grouped by date
        results = self.db.query(
            func.date(AnalyticsLog.created_at).label('date'),
            AnalyticsLog.event_type,
            func.count(AnalyticsLog.id).label('count')
        ).filter(
            AnalyticsLog.created_at >= start_date
        ).group_by(
            func.date(AnalyticsLog.created_at),
            AnalyticsLog.event_type
        ).all()

        # Organize by date
        daily_stats = {}
        for result in results:
            date_str = result.date.isoformat()
            if date_str not in daily_stats:
                daily_stats[date_str] = {
                    "date": date_str,
                    "events": {}
                }
            daily_stats[date_str]["events"][result.event_type] = result.count

        return list(daily_stats.values())

    def get_top_endpoints(
        self,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get most called API endpoints.

        Args:
            limit: Number of endpoints to return
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            List of endpoint statistics
        """
        query = self.db.query(
            AnalyticsLog.endpoint,
            AnalyticsLog.method,
            func.count(AnalyticsLog.id).label('count'),
            func.avg(AnalyticsLog.response_time_ms).label('avg_response_time')
        ).filter(
            AnalyticsLog.endpoint.isnot(None)
        )

        if start_date:
            query = query.filter(AnalyticsLog.created_at >= start_date)

        if end_date:
            query = query.filter(AnalyticsLog.created_at <= end_date)

        results = query.group_by(
            AnalyticsLog.endpoint,
            AnalyticsLog.method
        ).order_by(
            func.count(AnalyticsLog.id).desc()
        ).limit(limit).all()

        return [
            {
                "endpoint": r.endpoint,
                "method": r.method,
                "count": r.count,
                "avg_response_time_ms": float(r.avg_response_time) if r.avg_response_time else 0
            }
            for r in results
        ]

    def get_slowest_endpoints(
        self,
        limit: int = 10,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Get slowest API endpoints.

        Args:
            limit: Number of endpoints to return
            start_date: Optional start date
            end_date: Optional end date

        Returns:
            List of endpoint statistics
        """
        query = self.db.query(
            AnalyticsLog.endpoint,
            AnalyticsLog.method,
            func.avg(AnalyticsLog.response_time_ms).label('avg_response_time'),
            func.count(AnalyticsLog.id).label('count')
        ).filter(
            AnalyticsLog.endpoint.isnot(None),
            AnalyticsLog.response_time_ms.isnot(None)
        )

        if start_date:
            query = query.filter(AnalyticsLog.created_at >= start_date)

        if end_date:
            query = query.filter(AnalyticsLog.created_at <= end_date)

        results = query.group_by(
            AnalyticsLog.endpoint,
            AnalyticsLog.method
        ).order_by(
            func.avg(AnalyticsLog.response_time_ms).desc()
        ).limit(limit).all()

        return [
            {
                "endpoint": r.endpoint,
                "method": r.method,
                "avg_response_time_ms": float(r.avg_response_time),
                "count": r.count
            }
            for r in results
        ]

    def cleanup_old_logs(self, days: int = 90) -> int:
        """
        Delete analytics logs older than specified days.

        Args:
            days: Age threshold in days

        Returns:
            Number of logs deleted
        """
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        deleted = self.db.query(AnalyticsLog).filter(
            AnalyticsLog.created_at < cutoff_date
        ).delete()

        self.db.commit()

        return deleted
