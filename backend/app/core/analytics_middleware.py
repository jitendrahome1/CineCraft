"""
Analytics middleware for CineCraft.
Automatically logs API calls and tracks performance metrics.
"""
import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.services.analytics import AnalyticsService
from app.db.session import SessionLocal
from app.core.logging import get_logger

logger = get_logger(__name__)


class AnalyticsMiddleware(BaseHTTPMiddleware):
    """
    Middleware to automatically log all API calls to analytics.

    Tracks:
    - Endpoint and HTTP method
    - Response status code
    - Response time
    - User ID (if authenticated)
    - IP address
    - User agent
    """

    def __init__(self, app: ASGIApp, excluded_paths: list = None):
        super().__init__(app)
        # Paths to exclude from analytics logging
        self.excluded_paths = excluded_paths or [
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health",
            "/api/v1/analytics/health"
        ]

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process the request and log analytics.
        """
        # Skip analytics for excluded paths
        if any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)

        # Record start time
        start_time = time.time()

        # Process request
        response = await call_next(request)

        # Calculate response time
        response_time_ms = (time.time() - start_time) * 1000

        # Log to analytics (don't block request on logging failure)
        try:
            await self._log_api_call(request, response, response_time_ms)
        except Exception as e:
            logger.error(f"Failed to log analytics: {e}")

        return response

    async def _log_api_call(
        self,
        request: Request,
        response: Response,
        response_time_ms: float
    ):
        """
        Log API call to analytics database.
        """
        # Extract user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)

        # Extract IP address
        ip_address = self._get_client_ip(request)

        # Extract user agent
        user_agent = request.headers.get("user-agent")

        # Get endpoint path
        endpoint = request.url.path

        # Get HTTP method
        method = request.method

        # Get status code
        status_code = response.status_code

        # Log to database
        db = SessionLocal()
        try:
            analytics_service = AnalyticsService(db)
            analytics_service.log_api_call(
                endpoint=endpoint,
                method=method,
                status_code=status_code,
                response_time_ms=response_time_ms,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent
            )
            db.commit()
        except Exception as e:
            logger.error(f"Error logging API call to database: {e}")
            db.rollback()
        finally:
            db.close()

    def _get_client_ip(self, request: Request) -> str:
        """
        Extract client IP address from request.

        Handles X-Forwarded-For header for proxied requests.
        """
        # Check X-Forwarded-For header (for proxied requests)
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            # Take the first IP in the chain
            return forwarded.split(",")[0].strip()

        # Check X-Real-IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip

        # Fallback to direct client IP
        if request.client:
            return request.client.host

        return "unknown"


def setup_analytics_middleware(app, excluded_paths: list = None):
    """
    Setup analytics middleware for the FastAPI app.

    Args:
        app: FastAPI application instance
        excluded_paths: List of paths to exclude from analytics
    """
    app.add_middleware(
        AnalyticsMiddleware,
        excluded_paths=excluded_paths
    )
    logger.info("Analytics middleware configured")
