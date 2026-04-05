"""
Middleware for rate limiting, request logging, and other cross-cutting concerns.
"""
from fastapi import Request, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import time
from collections import defaultdict
from datetime import datetime, timedelta
import redis
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware using Redis.
    Limits requests per IP address per minute.
    """

    def __init__(self, app, redis_url: str = None, requests_per_minute: int = None):
        """
        Initialize rate limiter.

        Args:
            app: FastAPI application
            redis_url: Redis connection URL
            requests_per_minute: Max requests per minute per IP
        """
        super().__init__(app)
        self.redis_url = redis_url or settings.REDIS_URL
        self.requests_per_minute = requests_per_minute or settings.RATE_LIMIT_PER_MINUTE

        try:
            self.redis_client = redis.from_url(self.redis_url, decode_responses=True)
            # Test connection
            self.redis_client.ping()
            self.use_redis = True
            logger.info("Rate limiter initialized with Redis")
        except Exception as e:
            logger.warning(f"Redis connection failed, using in-memory rate limiting: {e}")
            self.use_redis = False
            self.in_memory_store = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable):
        """
        Process request and apply rate limiting.

        Args:
            request: HTTP request
            call_next: Next middleware in chain

        Returns:
            HTTP response

        Raises:
            HTTPException: If rate limit exceeded
        """
        # Skip rate limiting for health check
        if request.url.path == "/health":
            return await call_next(request)

        # Get client IP
        client_ip = request.client.host

        # Check rate limit
        if not self._check_rate_limit(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Too many requests. Please try again later."
            )

        # Process request
        response = await call_next(request)
        return response

    def _check_rate_limit(self, client_ip: str) -> bool:
        """
        Check if client has exceeded rate limit.

        Args:
            client_ip: Client IP address

        Returns:
            True if within limit, False if exceeded
        """
        if self.use_redis:
            return self._check_rate_limit_redis(client_ip)
        else:
            return self._check_rate_limit_memory(client_ip)

    def _check_rate_limit_redis(self, client_ip: str) -> bool:
        """
        Check rate limit using Redis.

        Args:
            client_ip: Client IP address

        Returns:
            True if within limit, False if exceeded
        """
        try:
            key = f"rate_limit:{client_ip}"
            current = self.redis_client.get(key)

            if current is None:
                # First request
                self.redis_client.setex(key, 60, 1)
                return True

            if int(current) >= self.requests_per_minute:
                return False

            # Increment counter
            self.redis_client.incr(key)
            return True

        except Exception as e:
            logger.error(f"Redis rate limit check failed: {e}")
            # Allow request if Redis fails
            return True

    def _check_rate_limit_memory(self, client_ip: str) -> bool:
        """
        Check rate limit using in-memory storage.

        Args:
            client_ip: Client IP address

        Returns:
            True if within limit, False if exceeded
        """
        now = datetime.utcnow()
        minute_ago = now - timedelta(minutes=1)

        # Get timestamps for this IP
        timestamps = self.in_memory_store[client_ip]

        # Remove old timestamps
        timestamps = [ts for ts in timestamps if ts > minute_ago]
        self.in_memory_store[client_ip] = timestamps

        # Check limit
        if len(timestamps) >= self.requests_per_minute:
            return False

        # Add current timestamp
        timestamps.append(now)
        return True


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware for logging all requests and responses.
    """

    async def dispatch(self, request: Request, call_next: Callable):
        """
        Log request and response.

        Args:
            request: HTTP request
            call_next: Next middleware in chain

        Returns:
            HTTP response
        """
        # Start timer
        start_time = time.time()

        # Log request
        logger.info(
            f"Request: {request.method} {request.url.path}",
            extra={
                "method": request.method,
                "path": request.url.path,
                "client_ip": request.client.host
            }
        )

        # Process request
        response = await call_next(request)

        # Calculate duration
        duration = time.time() - start_time

        # Log response
        logger.info(
            f"Response: {response.status_code} - Duration: {duration:.3f}s",
            extra={
                "status_code": response.status_code,
                "duration": duration,
                "path": request.url.path
            }
        )

        return response
