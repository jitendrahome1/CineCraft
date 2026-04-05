"""
Celery application configuration for CineCraft.
Handles asynchronous task processing for media generation and video rendering.
"""
from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
from kombu import Queue, Exchange

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

# Create Celery application
celery_app = Celery(
    "cinecraft",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.ai_generation",
        "app.tasks.rendering",
        "app.tasks.notifications"
    ]
)

# Celery configuration
celery_app.conf.update(
    # Task settings
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,

    # Task execution settings
    task_track_started=True,
    task_time_limit=3600,  # 1 hour hard limit
    task_soft_time_limit=3300,  # 55 minutes soft limit
    task_acks_late=True,  # Acknowledge tasks after completion
    task_reject_on_worker_lost=True,

    # Result backend settings
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",
        "visibility_timeout": 3600,
    },

    # Worker settings
    worker_prefetch_multiplier=1,  # Fetch one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
    worker_disable_rate_limits=False,

    # Retry settings
    task_autoretry_for=(Exception,),
    task_retry_kwargs={"max_retries": 3},
    task_retry_backoff=True,
    task_retry_backoff_max=600,  # Max 10 minutes
    task_retry_jitter=True,

    # Beat schedule (for periodic tasks)
    beat_schedule={
        "cleanup-expired-assets": {
            "task": "app.tasks.ai_generation.cleanup_expired_assets",
            "schedule": 3600.0,  # Every hour
        },
        "cleanup-old-jobs": {
            "task": "app.tasks.rendering.cleanup_old_jobs",
            "schedule": 86400.0,  # Every day
        },
    },

    # Queue configuration
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",

    # Define queues
    task_queues=(
        Queue("default", Exchange("default"), routing_key="default"),
        Queue("ai_generation", Exchange("ai_generation"), routing_key="ai.#"),
        Queue("rendering", Exchange("rendering"), routing_key="render.#"),
        Queue("notifications", Exchange("notifications"), routing_key="notify.#"),
    ),

    # Task routing
    task_routes={
        "app.tasks.ai_generation.*": {
            "queue": "ai_generation",
            "routing_key": "ai.generation"
        },
        "app.tasks.rendering.*": {
            "queue": "rendering",
            "routing_key": "render.video"
        },
        "app.tasks.notifications.*": {
            "queue": "notifications",
            "routing_key": "notify.user"
        },
    },
)


@task_prerun.connect
def task_prerun_handler(task_id, task, *args, **kwargs):
    """
    Handler called before task execution.

    Args:
        task_id: Task ID
        task: Task instance
    """
    logger.info(f"Starting task: {task.name} (ID: {task_id})")


@task_postrun.connect
def task_postrun_handler(task_id, task, *args, **kwargs):
    """
    Handler called after successful task execution.

    Args:
        task_id: Task ID
        task: Task instance
    """
    logger.info(f"Completed task: {task.name} (ID: {task_id})")


@task_failure.connect
def task_failure_handler(task_id, exception, *args, **kwargs):
    """
    Handler called when task fails.

    Args:
        task_id: Task ID
        exception: Exception that caused failure
    """
    logger.error(f"Task {task_id} failed with exception: {exception}")


def get_celery_app():
    """
    Get Celery application instance.

    Returns:
        Celery application
    """
    return celery_app


# Task status constants
class TaskStatus:
    """Task status constants."""
    PENDING = "pending"
    STARTED = "started"
    PROGRESS = "progress"
    SUCCESS = "success"
    FAILURE = "failure"
    RETRY = "retry"
    REVOKED = "revoked"


# Task priority constants
class TaskPriority:
    """Task priority constants."""
    LOW = 0
    NORMAL = 5
    HIGH = 9


if __name__ == "__main__":
    celery_app.start()
