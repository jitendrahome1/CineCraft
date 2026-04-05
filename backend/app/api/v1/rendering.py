"""
Rendering API endpoints.
Handles video rendering operations and status tracking.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.render_job import JobStatus, JobType
from app.repositories.render_job import RenderJobRepository
from app.repositories.project import ProjectRepository
from app.services.rendering import RenderingService
from app.schemas.render import (
    RenderVideoRequest,
    RenderVideoResponse,
    RenderStatusResponse,
    RenderResultResponse,
    CancelRenderResponse,
    RenderPresetsResponse,
    RenderConfigResponse
)
from app.tasks import rendering
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/render", response_model=RenderVideoResponse)
async def start_render(
    request: RenderVideoRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start video rendering for a project.

    Args:
        request: Render request with project ID and configuration
        current_user: Current authenticated user
        db: Database session

    Returns:
        Response with job ID and status

    Raises:
        HTTPException: If project not found or validation fails
    """
    project_repo = ProjectRepository(db)
    job_repo = RenderJobRepository(db)

    # Validate project exists and belongs to user
    project = project_repo.get(request.project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {request.project_id} not found"
        )

    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access to project"
        )

    # Check if project has scenes
    from app.repositories.scene import SceneRepository
    scene_repo = SceneRepository(db)
    scenes = scene_repo.get_by_project(request.project_id)

    if not scenes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project has no scenes. Generate scenes first."
        )

    # Check if project has required assets
    from app.repositories.media_asset import MediaAssetRepository
    from app.models.media_asset import MediaType

    asset_repo = MediaAssetRepository(db)
    missing_assets = []

    for scene in scenes:
        # Check for image
        image_assets = asset_repo.get_by_scene(scene.id, media_type=MediaType.IMAGE)
        if not image_assets:
            missing_assets.append(f"Scene {scene.id} missing image")

    if missing_assets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Missing required assets: {', '.join(missing_assets)}"
        )

    # Create render job
    job_data = {
        "user_id": current_user.id,
        "project_id": request.project_id,
        "job_type": JobType.VIDEO_RENDERING,
        "status": JobStatus.QUEUED,
        "config": {
            "width": request.width,
            "height": request.height,
            "fps": request.fps,
            "enable_ken_burns": request.enable_ken_burns,
            "music_volume": request.music_volume,
            "enable_ducking": request.enable_ducking,
            "enable_subtitles": request.enable_subtitles
        }
    }

    job = job_repo.create(job_data)

    # Check if Celery worker is available
    celery_available = False
    try:
        from app.tasks.celery_app import celery_app
        inspect = celery_app.control.inspect()
        active_workers = inspect.ping()
        celery_available = bool(active_workers)
    except Exception:
        celery_available = False

    if celery_available:
        # Use Celery for async rendering
        try:
            task = rendering.render_video.delay(
                job_id=job.id,
                project_id=request.project_id,
                user_id=current_user.id,
                config=job_data["config"]
            )
            job.task_id = task.id
            job.task_name = task.name
            db.commit()
            db.refresh(job)
            logger.info(f"Started render job {job.id} via Celery for project {request.project_id}")
        except Exception as e:
            logger.warning(f"Celery dispatch failed, will render directly: {e}")
            celery_available = False

    if not celery_available:
        # Run rendering directly in the request (no Celery worker)
        logger.info(f"Running direct render for job {job.id} (no Celery worker)")
        rendering_service = RenderingService(db)
        config = job_data["config"]

        try:
            await rendering_service.render_project_video(
                project_id=request.project_id,
                user_id=current_user.id,
                job_id=job.id,
                width=config.get("width", 1920),
                height=config.get("height", 1080),
                fps=config.get("fps", 30),
                enable_ken_burns=config.get("enable_ken_burns", True),
                music_volume=config.get("music_volume", 0.3),
                enable_ducking=config.get("enable_ducking", True),
                enable_subtitles=config.get("enable_subtitles", True)
            )
            db.refresh(job)
            logger.info(f"Direct render completed for job {job.id}")
        except Exception as render_err:
            logger.exception(f"Direct render failed for job {job.id}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Rendering failed: {str(render_err)}"
            )

    return RenderVideoResponse(
        job_id=job.id,
        status=job.status.value if hasattr(job.status, 'value') else str(job.status),
        message="Video rendering started successfully"
    )


@router.get("/status/{job_id}", response_model=RenderStatusResponse)
async def get_render_status(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get status of a render job.

    Args:
        job_id: Render job ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Render job status and progress

    Raises:
        HTTPException: If job not found or unauthorized
    """
    rendering_service = RenderingService(db)

    try:
        status_data = rendering_service.get_render_status(
            job_id=job_id,
            user_id=current_user.id
        )

        return RenderStatusResponse(**status_data)

    except Exception as e:
        logger.error(f"Failed to get render status for job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.get("/result/{job_id}", response_model=RenderResultResponse)
async def get_render_result(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get result of a completed render job.

    Args:
        job_id: Render job ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Render job result with video URL

    Raises:
        HTTPException: If job not found, not completed, or unauthorized
    """
    job_repo = RenderJobRepository(db)
    job = job_repo.get(job_id)

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Job {job_id} not found"
        )

    if job.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access to job"
        )

    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job is not completed (current status: {job.status.value})"
        )

    if not job.result_data:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Job completed but no result data available"
        )

    result_data = job.result_data

    return RenderResultResponse(
        video_asset_id=result_data.get("video_asset_id"),
        output_url=job.output_url,
        duration_seconds=result_data.get("duration_seconds", 0),
        file_size=result_data.get("file_size", 0),
        scene_count=result_data.get("scene_count", 0),
        resolution=result_data.get("resolution", "1920x1080"),
        metadata=result_data
    )


@router.delete("/{job_id}", response_model=CancelRenderResponse)
async def cancel_render(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel a running render job.

    Args:
        job_id: Render job ID
        current_user: Current authenticated user
        db: Database session

    Returns:
        Cancellation confirmation

    Raises:
        HTTPException: If job not found, cannot be cancelled, or unauthorized
    """
    rendering_service = RenderingService(db)
    job_repo = RenderJobRepository(db)

    try:
        success = rendering_service.cancel_render(
            job_id=job_id,
            user_id=current_user.id
        )

        if success:
            # Also revoke Celery task
            job = job_repo.get(job_id)
            if job and job.task_id:
                from celery import current_app
                current_app.control.revoke(job.task_id, terminate=True)

            return CancelRenderResponse(
                job_id=job_id,
                status="cancelled",
                message="Render job cancelled successfully"
            )

    except Exception as e:
        logger.error(f"Failed to cancel render job {job_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/presets", response_model=RenderPresetsResponse)
async def get_render_presets(
    current_user: User = Depends(get_current_user)
):
    """
    Get available render presets.

    Args:
        current_user: Current authenticated user

    Returns:
        Dictionary of render presets
    """
    presets = {
        "hd_1080p": {
            "name": "Full HD (1080p)",
            "width": 1920,
            "height": 1080,
            "fps": 30,
            "description": "Standard high definition quality"
        },
        "hd_720p": {
            "name": "HD (720p)",
            "width": 1280,
            "height": 720,
            "fps": 30,
            "description": "Good quality, smaller file size"
        },
        "4k": {
            "name": "4K Ultra HD",
            "width": 3840,
            "height": 2160,
            "fps": 30,
            "description": "Highest quality (requires Pro plan)"
        },
        "vertical_1080p": {
            "name": "Vertical HD (Stories/Reels)",
            "width": 1080,
            "height": 1920,
            "fps": 30,
            "description": "Optimized for mobile/social"
        },
        "square_1080p": {
            "name": "Square (1:1)",
            "width": 1080,
            "height": 1080,
            "fps": 30,
            "description": "Perfect for Instagram posts"
        }
    }

    return RenderPresetsResponse(presets=presets)


@router.get("/config", response_model=RenderConfigResponse)
async def get_render_config(
    current_user: User = Depends(get_current_user)
):
    """
    Get available render configuration options.

    Args:
        current_user: Current authenticated user

    Returns:
        Available render configuration options
    """
    resolutions = [
        {"width": 1280, "height": 720, "name": "HD 720p"},
        {"width": 1920, "height": 1080, "name": "Full HD 1080p"},
        {"width": 2560, "height": 1440, "name": "QHD 1440p"},
        {"width": 3840, "height": 2160, "name": "4K Ultra HD"},
        {"width": 1080, "height": 1920, "name": "Vertical HD"},
        {"width": 1080, "height": 1080, "name": "Square"}
    ]

    fps_options = [24, 25, 30, 60]

    quality_presets = {
        "draft": {
            "name": "Draft",
            "description": "Fast preview quality",
            "music_volume": 0.2,
            "enable_ken_burns": False,
            "enable_subtitles": False
        },
        "standard": {
            "name": "Standard",
            "description": "Balanced quality and speed",
            "music_volume": 0.3,
            "enable_ken_burns": True,
            "enable_subtitles": True
        },
        "high": {
            "name": "High",
            "description": "Best quality (slower)",
            "music_volume": 0.3,
            "enable_ken_burns": True,
            "enable_subtitles": True
        }
    }

    features = {
        "ken_burns_effect": True,
        "audio_ducking": True,
        "subtitles": True,
        "fade_transitions": True,
        "custom_music_volume": True
    }

    return RenderConfigResponse(
        resolutions=resolutions,
        fps_options=fps_options,
        quality_presets=quality_presets,
        features=features
    )
