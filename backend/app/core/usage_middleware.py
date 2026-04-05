"""
Usage limit enforcement middleware.
Checks user subscription limits before allowing video generation.
"""
from fastapi import HTTPException, status, Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import re

from app.core.logging import get_logger
from app.db.session import SessionLocal
from app.services.subscription import SubscriptionService

logger = get_logger(__name__)


class UsageLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware to enforce subscription usage limits.

    Checks if user has exceeded their video generation limit
    before allowing access to video creation endpoints.
    """

    # Regex patterns for endpoints that require usage checks
    VIDEO_GENERATION_PATTERNS = [
        re.compile(r"^/api/v1/projects/\d+/generate$"),
        re.compile(r"^/api/v1/ai/generate-story$"),
        re.compile(r"^/api/v1/rendering/render$"),
    ]

    async def dispatch(self, request: Request, call_next: Callable):
        """
        Check usage limits for protected endpoints.

        Args:
            request: FastAPI request
            call_next: Next middleware/handler

        Returns:
            Response from next handler or error response
        """
        # Check if this endpoint requires usage limit check
        if not self._requires_usage_check(request.url.path):
            return await call_next(request)

        # Only check on POST/PUT requests (creation/update)
        if request.method not in ["POST", "PUT"]:
            return await call_next(request)

        # Get user from request state (set by auth middleware)
        user = getattr(request.state, "user", None)

        if not user:
            # No user authenticated, let auth middleware handle it
            return await call_next(request)

        # Check usage limits
        try:
            db = SessionLocal()
            try:
                subscription_service = SubscriptionService(db)
                can_create, reason = subscription_service.can_create_video(user.id)

                if not can_create:
                    logger.warning(
                        f"User {user.id} exceeded usage limit",
                        extra={"reason": reason}
                    )
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content={
                            "error": "UsageLimitExceeded",
                            "message": reason or "You have reached your usage limit",
                            "details": {
                                "user_id": user.id,
                                "upgrade_url": "/api/v1/subscriptions/plans"
                            }
                        }
                    )

                # User can create video, proceed
                response = await call_next(request)

                # If request was successful (2xx status), increment usage
                if 200 <= response.status_code < 300:
                    try:
                        subscription_service.increment_video_usage(user.id)
                        logger.info(f"Incremented video usage for user {user.id}")
                    except Exception as e:
                        # Don't fail the request if usage increment fails
                        logger.error(
                            f"Failed to increment usage for user {user.id}: {str(e)}"
                        )

                return response

            finally:
                db.close()

        except Exception as e:
            logger.exception(f"Error checking usage limits: {str(e)}")
            # Don't block the request on middleware errors
            # Let it proceed and handle errors elsewhere
            return await call_next(request)

    def _requires_usage_check(self, path: str) -> bool:
        """
        Check if endpoint requires usage limit verification.

        Args:
            path: Request path

        Returns:
            True if endpoint requires check
        """
        for pattern in self.VIDEO_GENERATION_PATTERNS:
            if pattern.match(path):
                return True
        return False


async def check_video_creation_limit(user_id: int, db) -> tuple[bool, str | None]:
    """
    Helper function to check if user can create videos.
    Can be used as a FastAPI dependency.

    Args:
        user_id: User ID
        db: Database session

    Returns:
        Tuple of (can_create, reason)

    Raises:
        HTTPException: If limit exceeded
    """
    subscription_service = SubscriptionService(db)
    can_create, reason = subscription_service.can_create_video(user_id)

    if not can_create:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "error": "UsageLimitExceeded",
                "message": reason or "You have reached your usage limit",
                "upgrade_url": "/api/v1/subscriptions/plans"
            }
        )

    return can_create, reason
