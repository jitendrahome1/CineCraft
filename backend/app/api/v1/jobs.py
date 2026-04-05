"""
Jobs API endpoints.
Handles render job management and status tracking.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.render_job import JobStatus, JobType
from app.repositories.render_job import RenderJobRepository
from app.schemas.job import (
    JobResponse,
    JobListResponse,
    JobStatsResponse,
    StartJobRequest,
    StartJobResponse
)
from app.tasks import ai_generation
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/start", response_model=StartJobResponse)
async def start_job(
    request: StartJobRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Start a new render job.

    Args:
        request: Job start request
        current_user: Current user
        db: Database session

    Returns:
        Job response with task ID
    """
    job_repo = RenderJobRepository(db)

    # Create job record
    job_data = {
        "user_id": current_user.id,
        "project_id": request.project_id,
        "job_type": request.job_type,
        "status": JobStatus.QUEUED,
        "config": request.config or {}
    }

    job = job_repo.create(job_data)

    # Queue Celery task based on job type
    try:
        if request.job_type == JobType.STORY_GENERATION:
            task = ai_generation.generate_complete_story.delay(
                job_id=job.id,
                project_id=request.project_id,
                user_id=current_user.id
            )
        elif request.job_type == JobType.IMAGE_GENERATION:
            config = request.config or {}
            task = ai_generation.generate_project_images.delay(
                job_id=job.id,
                project_id=request.project_id,
                user_id=current_user.id,
                width=config.get("width", 1024),
                height=config.get("height", 1024),
                style=config.get("style")
            )
        elif request.job_type == JobType.VOICE_GENERATION:
            config = request.config or {}
            task = ai_generation.generate_project_voices.delay(
                job_id=job.id,
                project_id=request.project_id,
                user_id=current_user.id,
                voice_id=config.get("voice_id"),
                speed=config.get("speed", 1.0)
            )
        elif request.job_type == JobType.MUSIC_GENERATION:
            config = request.config or {}
            task = ai_generation.generate_project_music.delay(
                job_id=job.id,
                project_id=request.project_id,
                user_id=current_user.id,
                duration=config.get("duration", 60),
                mood=config.get("mood"),
                genre=config.get("genre"),
                prompt=config.get("prompt")
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Job type {request.job_type} not yet implemented"
            )

        # Update job with task ID
        job.task_id = task.id
        job.task_name = task.name
        db.commit()
        db.refresh(job)

        logger.info(f"Started job {job.id} with task {task.id}")

        return StartJobResponse(
            job=JobResponse.model_validate(job),
            message="Job started successfully"
        )

    except Exception as e:
        logger.exception(f"Failed to start job {job.id}")
        job_repo.delete(job.id)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start job: {str(e)}"
        )


@router.get("/", response_model=JobListResponse)
async def list_jobs(
    project_id: Optional[int] = None,
    status_filter: Optional[JobStatus] = None,
    job_type: Optional[JobType] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List user's render jobs.

    Args:
        project_id: Optional project filter
        status_filter: Optional status filter
        job_type: Optional job type filter
        skip: Pagination offset
        limit: Pagination limit
        current_user: Current user
        db: Database session

    Returns:
        List of jobs
    """
    job_repo = RenderJobRepository(db)

    if project_id:
        jobs = job_repo.get_by_project(
            project_id=project_id,
            skip=skip,
            limit=limit,
            status=status_filter
        )
        total = job_repo.count_user_jobs(
            user_id=current_user.id,
            status=status_filter,
            job_type=job_type
        )
    else:
        jobs = job_repo.get_by_user(
            user_id=current_user.id,
            skip=skip,
            limit=limit,
            status=status_filter,
            job_type=job_type
        )
        total = job_repo.count_user_jobs(
            user_id=current_user.id,
            status=status_filter,
            job_type=job_type
        )

    return JobListResponse(
        jobs=[JobResponse.model_validate(job) for job in jobs],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/{job_id}", response_model=JobResponse)
async def get_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get job details.

    Args:
        job_id: Job ID
        current_user: Current user
        db: Database session

    Returns:
        Job details
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

    return JobResponse.model_validate(job)


@router.delete("/{job_id}")
async def cancel_job(
    job_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Cancel a job.

    Args:
        job_id: Job ID
        current_user: Current user
        db: Database session

    Returns:
        Success message
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

    if job.is_finished:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot cancel finished job"
        )

    # Revoke Celery task
    if job.task_id:
        from celery import current_app
        current_app.control.revoke(job.task_id, terminate=True)

    # Update job status
    job.cancel()
    db.commit()

    logger.info(f"Cancelled job {job_id}")

    return {"message": "Job cancelled successfully"}


@router.get("/stats/summary", response_model=JobStatsResponse)
async def get_job_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get job statistics for current user.

    Args:
        current_user: Current user
        db: Database session

    Returns:
        Job statistics
    """
    job_repo = RenderJobRepository(db)
    stats = job_repo.get_job_stats(user_id=current_user.id)

    return JobStatsResponse(**stats)
