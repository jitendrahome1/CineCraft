"""
WebSocket utility functions for use in Celery tasks.
Provides synchronous wrappers for async WebSocket operations.
"""
import asyncio
from typing import Optional, Dict, Any

from app.core.logging import get_logger

logger = get_logger(__name__)


def broadcast_progress_sync(
    job_id: int,
    progress: float,
    stage: str,
    status: str = "processing"
):
    """
    Broadcast progress update (synchronous wrapper for Celery tasks).

    Args:
        job_id: Job ID
        progress: Progress percentage (0-100)
        stage: Current stage description
        status: Job status
    """
    try:
        from app.core.websocket import manager

        # Get or create event loop
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        # Run async function in sync context
        loop.run_until_complete(
            manager.broadcast_progress(job_id, progress, stage, status)
        )
    except Exception as e:
        logger.warning(f"Failed to broadcast progress for job {job_id}: {e}")


def broadcast_completion_sync(
    job_id: int,
    result_data: Dict[str, Any]
):
    """
    Broadcast job completion (synchronous wrapper for Celery tasks).

    Args:
        job_id: Job ID
        result_data: Result data dictionary
    """
    try:
        from app.core.websocket import manager

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(
            manager.broadcast_completion(job_id, result_data)
        )
    except Exception as e:
        logger.warning(f"Failed to broadcast completion for job {job_id}: {e}")


def broadcast_error_sync(
    job_id: int,
    error_message: str
):
    """
    Broadcast job error (synchronous wrapper for Celery tasks).

    Args:
        job_id: Job ID
        error_message: Error message
    """
    try:
        from app.core.websocket import manager

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(
            manager.broadcast_error(job_id, error_message)
        )
    except Exception as e:
        logger.warning(f"Failed to broadcast error for job {job_id}: {e}")


def broadcast_stage_complete_sync(
    job_id: int,
    stage: str,
    progress: float
):
    """
    Broadcast stage completion (synchronous wrapper for Celery tasks).

    Args:
        job_id: Job ID
        stage: Completed stage name
        progress: Current progress percentage
    """
    try:
        from app.core.websocket import manager

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(
            manager.broadcast_stage_complete(job_id, stage, progress)
        )
    except Exception as e:
        logger.warning(f"Failed to broadcast stage complete for job {job_id}: {e}")


def broadcast_status_change_sync(
    job_id: int,
    old_status: str,
    new_status: str
):
    """
    Broadcast job status change (synchronous wrapper for Celery tasks).

    Args:
        job_id: Job ID
        old_status: Previous status
        new_status: New status
    """
    try:
        from app.core.websocket import manager

        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        loop.run_until_complete(
            manager.broadcast_status_change(job_id, old_status, new_status)
        )
    except Exception as e:
        logger.warning(f"Failed to broadcast status change for job {job_id}: {e}")
