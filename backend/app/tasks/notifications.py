"""
Celery tasks for notification operations.
Handles async email and webhook notifications.
"""
from celery import Task

from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
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


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.notifications.send_job_completion_email")
def send_job_completion_email(
    self,
    user_email: str,
    job_id: int,
    job_type: str,
    status: str
):
    """
    Send job completion email to user.

    Args:
        user_email: User email address
        job_id: RenderJob ID
        job_type: Job type
        status: Job status (completed/failed)
    """
    try:
        logger.info(f"Sending job completion email to {user_email}")

        # TODO: Implement email sending
        # This could use SendGrid, AWS SES, or other email service
        # For now, just log

        subject = f"CineCraft: {job_type} {status}"
        message = f"Your job #{job_id} has {status}."

        logger.info(f"Email: {subject} - {message}")

        # In production, send actual email:
        # send_email(to=user_email, subject=subject, body=message)

        return {"sent": True, "email": user_email}

    except Exception as e:
        logger.exception(f"Failed to send email to {user_email}")
        raise


@celery_app.task(bind=True, name="app.tasks.notifications.send_webhook_notification")
def send_webhook_notification(
    self,
    webhook_url: str,
    payload: dict
):
    """
    Send webhook notification.

    Args:
        webhook_url: Webhook URL
        payload: Notification payload
    """
    try:
        import httpx

        logger.info(f"Sending webhook notification to {webhook_url}")

        # Send webhook
        with httpx.Client(timeout=10.0) as client:
            response = client.post(webhook_url, json=payload)

            if response.status_code >= 200 and response.status_code < 300:
                logger.info(f"Webhook sent successfully to {webhook_url}")
                return {"sent": True, "status_code": response.status_code}
            else:
                logger.warning(f"Webhook failed: {response.status_code}")
                return {"sent": False, "status_code": response.status_code}

    except Exception as e:
        logger.exception(f"Failed to send webhook to {webhook_url}")
        raise
