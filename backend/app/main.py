"""
FastAPI application entry point for CineCraft.
Main application initialization and configuration.
"""
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import time
import os

from app.core.config import settings
from app.core.logging import setup_logging, get_logger
from app.core.errors import CineCraftException
from app.db.session import init_db

# Setup logging
setup_logging(environment=settings.ENVIRONMENT)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    Handles startup and shutdown events.
    """
    # Startup
    logger.info(f"Starting {settings.APP_NAME} in {settings.ENVIRONMENT} mode")

    # Initialize database tables
    if settings.ENVIRONMENT == "development":
        init_db()

    logger.info("Application startup complete")

    yield

    # Shutdown
    logger.info("Application shutting down")


# Create FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="AI-powered Story-to-Video automation platform",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files directory for serving media assets
# This allows the frontend to load images from /storage/media/...
storage_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "storage")
if os.path.exists(storage_path):
    app.mount("/storage", StaticFiles(directory=storage_path), name="storage")
    logger.info(f"Static files mounted: /storage -> {storage_path}")
else:
    logger.warning(f"Storage directory not found: {storage_path}")


# Request timing middleware
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """Add processing time to response headers."""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# Global exception handler
@app.exception_handler(CineCraftException)
async def cinecraft_exception_handler(request: Request, exc: CineCraftException):
    """Handle custom CineCraft exceptions."""
    logger.error(
        f"CineCraft error: {exc.code} - {exc.message}",
        extra={"details": exc.details}
    )
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={
            "error": exc.code,
            "message": exc.message,
            "details": exc.details
        }
    )


# General exception handler
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.exception(f"Unexpected error: {str(exc)}")

    if settings.DEBUG:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "message": str(exc),
                "type": type(exc).__name__
            }
        )
    else:
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "error": "InternalServerError",
                "message": "An unexpected error occurred"
            }
        )


# Health check endpoint
@app.get("/health", tags=["Health"])
async def health_check():
    """
    Health check endpoint.
    Returns application status.
    """
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "environment": settings.ENVIRONMENT,
        "version": "1.0.0"
    }


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Root endpoint with API information."""
    return {
        "message": f"Welcome to {settings.APP_NAME} API",
        "version": "1.0.0",
        "docs": "/docs" if settings.DEBUG else "Documentation disabled in production",
        "health": "/health"
    }


# Import API routers
from app.api.v1 import auth, users, subscriptions, webhooks, projects, scenes, ai, storage, jobs, rendering, websocket, admin, analytics, media

# Include routers
app.include_router(
    auth.router,
    prefix=f"{settings.API_V1_PREFIX}/auth",
    tags=["Authentication"]
)
app.include_router(
    users.router,
    prefix=f"{settings.API_V1_PREFIX}/users",
    tags=["Users"]
)
app.include_router(
    subscriptions.router,
    prefix=f"{settings.API_V1_PREFIX}/subscriptions",
    tags=["Subscriptions"]
)
app.include_router(
    webhooks.router,
    prefix=f"{settings.API_V1_PREFIX}/webhooks",
    tags=["Webhooks"]
)
app.include_router(
    projects.router,
    prefix=f"{settings.API_V1_PREFIX}/projects",
    tags=["Projects"]
)
app.include_router(
    scenes.router,
    prefix=f"{settings.API_V1_PREFIX}",
    tags=["Scenes"]
)
app.include_router(
    ai.router,
    prefix=f"{settings.API_V1_PREFIX}/ai",
    tags=["AI Generation"]
)
app.include_router(
    media.router,
    prefix=f"{settings.API_V1_PREFIX}/media",
    tags=["Media Generation"]
)
app.include_router(
    storage.router,
    prefix=f"{settings.API_V1_PREFIX}/storage",
    tags=["Storage"]
)
app.include_router(
    jobs.router,
    prefix=f"{settings.API_V1_PREFIX}/jobs",
    tags=["Jobs"]
)
app.include_router(
    rendering.router,
    prefix=f"{settings.API_V1_PREFIX}/rendering",
    tags=["Rendering"]
)
app.include_router(
    websocket.router,
    prefix=f"{settings.API_V1_PREFIX}/ws",
    tags=["WebSocket"]
)
app.include_router(
    admin.router,
    prefix=f"{settings.API_V1_PREFIX}/admin",
    tags=["Admin"]
)
app.include_router(
    analytics.router,
    prefix=f"{settings.API_V1_PREFIX}/analytics",
    tags=["Analytics"]
)

# Add rate limiting and request logging middleware
from app.core.middleware import RateLimitMiddleware, RequestLoggingMiddleware
from app.core.analytics_middleware import setup_analytics_middleware

# Note: Add these after CORS middleware but before route handlers
# Uncomment to enable:
# app.add_middleware(RateLimitMiddleware)
# app.add_middleware(RequestLoggingMiddleware)

# Setup analytics middleware (automatically logs all API calls)
setup_analytics_middleware(
    app,
    excluded_paths=[
        "/docs",
        "/redoc",
        "/openapi.json",
        "/health",
        "/api/v1/analytics/health",
        "/api/v1/ws"  # Exclude WebSocket connections
    ]
)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG
    )
