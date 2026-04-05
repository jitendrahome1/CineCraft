"""
Repository for RenderJob model.
Handles data access operations for render jobs.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, desc

from app.repositories.base import BaseRepository
from app.models.render_job import RenderJob, JobStatus, JobType
from app.core.logging import get_logger

logger = get_logger(__name__)


class RenderJobRepository(BaseRepository[RenderJob]):
    """Repository for RenderJob CRUD operations."""

    def __init__(self, db: Session):
        super().__init__(RenderJob, db)

    def get_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[JobStatus] = None,
        job_type: Optional[JobType] = None
    ) -> List[RenderJob]:
        """
        Get all jobs for a user.

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records
            status: Optional status filter
            job_type: Optional job type filter

        Returns:
            List of render jobs
        """
        query = self.db.query(RenderJob).filter(RenderJob.user_id == user_id)

        if status:
            query = query.filter(RenderJob.status == status)

        if job_type:
            query = query.filter(RenderJob.job_type == job_type)

        return query.order_by(desc(RenderJob.created_at)).offset(skip).limit(limit).all()

    def get_by_project(
        self,
        project_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[JobStatus] = None
    ) -> List[RenderJob]:
        """
        Get all jobs for a project.

        Args:
            project_id: Project ID
            skip: Number of records to skip
            limit: Maximum number of records
            status: Optional status filter

        Returns:
            List of render jobs
        """
        query = self.db.query(RenderJob).filter(RenderJob.project_id == project_id)

        if status:
            query = query.filter(RenderJob.status == status)

        return query.order_by(desc(RenderJob.created_at)).offset(skip).limit(limit).all()

    def get_by_task_id(self, task_id: str) -> Optional[RenderJob]:
        """
        Get job by Celery task ID.

        Args:
            task_id: Celery task ID

        Returns:
            RenderJob or None
        """
        return self.db.query(RenderJob).filter(RenderJob.task_id == task_id).first()

    def get_active_jobs(
        self,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[RenderJob]:
        """
        Get all active (running) jobs.

        Args:
            user_id: Optional user ID filter
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of active render jobs
        """
        query = self.db.query(RenderJob).filter(
            RenderJob.status.in_([JobStatus.QUEUED, JobStatus.PROCESSING])
        )

        if user_id:
            query = query.filter(RenderJob.user_id == user_id)

        return query.order_by(desc(RenderJob.created_at)).offset(skip).limit(limit).all()

    def get_pending_jobs(
        self,
        job_type: Optional[JobType] = None,
        limit: int = 100
    ) -> List[RenderJob]:
        """
        Get pending jobs waiting to be queued.

        Args:
            job_type: Optional job type filter
            limit: Maximum number of records

        Returns:
            List of pending render jobs
        """
        query = self.db.query(RenderJob).filter(RenderJob.status == JobStatus.PENDING)

        if job_type:
            query = query.filter(RenderJob.job_type == job_type)

        # Order by priority (descending) then creation time
        return query.order_by(
            desc(RenderJob.priority),
            RenderJob.created_at
        ).limit(limit).all()

    def get_failed_jobs(
        self,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[RenderJob]:
        """
        Get failed jobs.

        Args:
            user_id: Optional user ID filter
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of failed render jobs
        """
        query = self.db.query(RenderJob).filter(RenderJob.status == JobStatus.FAILED)

        if user_id:
            query = query.filter(RenderJob.user_id == user_id)

        return query.order_by(desc(RenderJob.created_at)).offset(skip).limit(limit).all()

    def count_user_jobs(
        self,
        user_id: int,
        status: Optional[JobStatus] = None,
        job_type: Optional[JobType] = None
    ) -> int:
        """
        Count jobs for a user.

        Args:
            user_id: User ID
            status: Optional status filter
            job_type: Optional job type filter

        Returns:
            Number of jobs
        """
        query = self.db.query(RenderJob).filter(RenderJob.user_id == user_id)

        if status:
            query = query.filter(RenderJob.status == status)

        if job_type:
            query = query.filter(RenderJob.job_type == job_type)

        return query.count()

    def count_active_jobs(self, user_id: Optional[int] = None) -> int:
        """
        Count active jobs.

        Args:
            user_id: Optional user ID filter

        Returns:
            Number of active jobs
        """
        query = self.db.query(RenderJob).filter(
            RenderJob.status.in_([JobStatus.QUEUED, JobStatus.PROCESSING])
        )

        if user_id:
            query = query.filter(RenderJob.user_id == user_id)

        return query.count()

    def cleanup_old_jobs(self, days: int = 30) -> int:
        """
        Delete old completed/failed jobs.

        Args:
            days: Delete jobs older than this many days

        Returns:
            Number of jobs deleted
        """
        from datetime import datetime, timedelta

        cutoff_date = datetime.utcnow() - timedelta(days=days)

        jobs = self.db.query(RenderJob).filter(
            and_(
                RenderJob.status.in_([JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]),
                RenderJob.completed_at < cutoff_date
            )
        ).all()

        count = len(jobs)

        for job in jobs:
            self.db.delete(job)

        self.db.commit()
        logger.info(f"Cleaned up {count} old jobs")
        return count

    def get_job_stats(self, user_id: Optional[int] = None) -> dict:
        """
        Get job statistics.

        Args:
            user_id: Optional user ID filter

        Returns:
            Dictionary with statistics
        """
        from sqlalchemy import func

        query = self.db.query(RenderJob)

        if user_id:
            query = query.filter(RenderJob.user_id == user_id)

        # Total counts by status
        stats = {
            "total": query.count(),
            "pending": query.filter(RenderJob.status == JobStatus.PENDING).count(),
            "queued": query.filter(RenderJob.status == JobStatus.QUEUED).count(),
            "processing": query.filter(RenderJob.status == JobStatus.PROCESSING).count(),
            "completed": query.filter(RenderJob.status == JobStatus.COMPLETED).count(),
            "failed": query.filter(RenderJob.status == JobStatus.FAILED).count(),
            "cancelled": query.filter(RenderJob.status == JobStatus.CANCELLED).count(),
        }

        # Average duration for completed jobs
        avg_duration = query.filter(
            and_(
                RenderJob.status == JobStatus.COMPLETED,
                RenderJob.duration_seconds.isnot(None)
            )
        ).with_entities(func.avg(RenderJob.duration_seconds)).scalar()

        stats["avg_duration_seconds"] = float(avg_duration) if avg_duration else 0.0

        # Counts by job type
        stats["by_type"] = {}
        for job_type in JobType:
            count = query.filter(RenderJob.job_type == job_type).count()
            stats["by_type"][job_type.value] = count

        return stats
