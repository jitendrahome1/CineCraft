"""
Celery tasks for video rendering operations.
Handles async video rendering (Phase 9 implementation).
"""
from celery import Task

from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from app.repositories.render_job import RenderJobRepository
from app.core.logging import get_logger

logger = get_logger(__name__)


class DatabaseTask(Task):
    """Base task class that provides database session."""

    _db = None

    @property
    def db(self):
        """Get database session."""
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        """Close database session after task completion."""
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.rendering.render_video")
def render_video(
    self,
    job_id: int,
    project_id: int,
    user_id: int,
    config: dict = None
):
    """
    Render video from project assets.

    Args:
        job_id: RenderJob ID
        project_id: Project ID
        user_id: User ID
        config: Rendering configuration with optional parameters:
            - width: Video width (default: 1920)
            - height: Video height (default: 1080)
            - fps: Frames per second (default: 30)
            - enable_ken_burns: Apply Ken Burns effect (default: True)
            - music_volume: Background music volume (default: 0.3)
            - enable_ducking: Enable audio ducking (default: True)
            - enable_subtitles: Add subtitles (default: True)
    """
    import asyncio
    from app.services.rendering import RenderingService

    job_repo = RenderJobRepository(self.db)
    job = job_repo.get(job_id)

    if not job:
        logger.error(f"Job {job_id} not found")
        return

    try:
        logger.info(f"Starting video render for job {job_id}, project {project_id}")

        # Extract config parameters
        config = config or {}
        width = config.get("width", 1920)
        height = config.get("height", 1080)
        fps = config.get("fps", 30)
        enable_ken_burns = config.get("enable_ken_burns", True)
        music_volume = config.get("music_volume", 0.3)
        enable_ducking = config.get("enable_ducking", True)
        enable_subtitles = config.get("enable_subtitles", True)

        # Create rendering service
        rendering_service = RenderingService(self.db)

        # Progress callback for Celery task updates
        def progress_callback(job_id: int, progress: float, stage: str):
            """Callback to update task state."""
            self.update_state(
                state="PROGRESS",
                meta={
                    "job_id": job_id,
                    "progress": progress,
                    "stage": stage
                }
            )

        # Run async rendering in a new event loop (Celery workers don't have one)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(
                rendering_service.render_project_video(
                    project_id=project_id,
                    user_id=user_id,
                    job_id=job_id,
                    width=width,
                    height=height,
                    fps=fps,
                    enable_ken_burns=enable_ken_burns,
                    music_volume=music_volume,
                    enable_ducking=enable_ducking,
                    enable_subtitles=enable_subtitles,
                    progress_callback=progress_callback
                )
            )
        finally:
            loop.close()

        logger.info(f"Video render complete for job {job_id}")

        return {
            "status": "success",
            "job_id": job_id,
            "result": result
        }

    except Exception as e:
        logger.exception(f"Video rendering failed for job {job_id}")
        job.fail(str(e), {"exception": type(e).__name__})
        self.db.commit()
        raise


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.rendering.cleanup_old_jobs")
def cleanup_old_jobs(self, days: int = 30):
    """
    Periodic task to clean up old completed/failed jobs.

    Args:
        days: Delete jobs older than this many days
    """
    try:
        logger.info(f"Starting cleanup of jobs older than {days} days")

        job_repo = RenderJobRepository(self.db)
        deleted_count = job_repo.cleanup_old_jobs(days=days)

        logger.info(f"Cleaned up {deleted_count} old jobs")
        return {"deleted_count": deleted_count}

    except Exception as e:
        logger.exception("Job cleanup failed")
        raise
