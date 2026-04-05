"""
Admin API endpoints.
Handles platform administration, user management, and monitoring.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime

from app.api.deps import get_db, get_current_admin_user
from app.models.user import User, UserRole
from app.repositories.user import UserRepository
from app.repositories.subscription import SubscriptionRepository
from app.repositories.render_job import RenderJobRepository
from app.repositories.project import ProjectRepository
from app.services.feature_flag import FeatureFlagService
from app.schemas.admin import (
    FeatureFlagCreate,
    FeatureFlagUpdate,
    FeatureFlagResponse,
    FeatureFlagListResponse,
    FeatureFlagStatsResponse,
    AdminUserUpdate,
    AdminUserResponse,
    AdminUserListResponse,
    UserBanRequest,
    SystemHealthResponse,
    SystemStatsResponse,
    AdminJobListResponse,
    AdminSubscriptionListResponse
)
from app.core.logging import get_logger
from app.core.websocket import manager

logger = get_logger(__name__)

router = APIRouter()


# Feature Flag Endpoints

@router.post("/feature-flags", response_model=FeatureFlagResponse)
async def create_feature_flag(
    request: FeatureFlagCreate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Create a new feature flag.

    Args:
        request: Feature flag creation request
        current_user: Current admin user
        db: Database session

    Returns:
        Created feature flag
    """
    flag_service = FeatureFlagService(db)

    flag = flag_service.create_flag(
        key=request.key,
        name=request.name,
        description=request.description,
        enabled=request.enabled,
        created_by=current_user.id,
        flag_type=request.flag_type.value,
        scope=request.scope.value,
        value_string=request.value_string,
        value_number=request.value_number,
        value_json=request.value_json,
        target_user_ids=request.target_user_ids,
        target_plan_ids=request.target_plan_ids,
        target_roles=request.target_roles,
        category=request.category,
        tags=request.tags,
        rollout_percentage=request.rollout_percentage
    )

    logger.info(f"Admin {current_user.email} created feature flag: {flag.key}")

    return FeatureFlagResponse.model_validate(flag)


@router.get("/feature-flags", response_model=FeatureFlagListResponse)
async def list_feature_flags(
    category: Optional[str] = None,
    enabled_only: bool = False,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    List all feature flags.

    Args:
        category: Filter by category
        enabled_only: Only show enabled flags
        skip: Number to skip
        limit: Maximum number to return
        current_user: Current admin user
        db: Database session

    Returns:
        List of feature flags
    """
    flag_service = FeatureFlagService(db)

    flags = flag_service.get_all_flags(
        category=category,
        enabled_only=enabled_only,
        skip=skip,
        limit=limit
    )

    total = flag_service.flag_repo.count()

    return FeatureFlagListResponse(
        flags=[FeatureFlagResponse.model_validate(f) for f in flags],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/feature-flags/{flag_id}", response_model=FeatureFlagResponse)
async def get_feature_flag(
    flag_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get feature flag by ID.

    Args:
        flag_id: Feature flag ID
        current_user: Current admin user
        db: Database session

    Returns:
        Feature flag
    """
    flag_service = FeatureFlagService(db)
    flag = flag_service.flag_repo.get(flag_id)

    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag {flag_id} not found"
        )

    return FeatureFlagResponse.model_validate(flag)


@router.put("/feature-flags/{flag_id}", response_model=FeatureFlagResponse)
async def update_feature_flag(
    flag_id: int,
    request: FeatureFlagUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update feature flag.

    Args:
        flag_id: Feature flag ID
        request: Update request
        current_user: Current admin user
        db: Database session

    Returns:
        Updated feature flag
    """
    flag_service = FeatureFlagService(db)

    update_data = request.model_dump(exclude_unset=True)

    flag = flag_service.update_flag(
        flag_id=flag_id,
        updated_by=current_user.id,
        **update_data
    )

    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag {flag_id} not found"
        )

    logger.info(f"Admin {current_user.email} updated feature flag: {flag.key}")

    return FeatureFlagResponse.model_validate(flag)


@router.post("/feature-flags/{flag_id}/toggle", response_model=FeatureFlagResponse)
async def toggle_feature_flag(
    flag_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Toggle feature flag enabled state.

    Args:
        flag_id: Feature flag ID
        current_user: Current admin user
        db: Database session

    Returns:
        Updated feature flag
    """
    flag_service = FeatureFlagService(db)

    flag = flag_service.toggle_flag(flag_id, updated_by=current_user.id)

    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag {flag_id} not found"
        )

    return FeatureFlagResponse.model_validate(flag)


@router.delete("/feature-flags/{flag_id}")
async def delete_feature_flag(
    flag_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Delete feature flag.

    Args:
        flag_id: Feature flag ID
        current_user: Current admin user
        db: Database session

    Returns:
        Success message
    """
    flag_service = FeatureFlagService(db)

    flag = flag_service.flag_repo.get(flag_id)
    if not flag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Feature flag {flag_id} not found"
        )

    flag_service.delete_flag(flag_id)

    logger.warning(f"Admin {current_user.email} deleted feature flag: {flag.key}")

    return {"message": "Feature flag deleted successfully"}


@router.get("/feature-flags/stats/summary", response_model=FeatureFlagStatsResponse)
async def get_feature_flag_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get feature flag statistics.

    Args:
        current_user: Current admin user
        db: Database session

    Returns:
        Feature flag statistics
    """
    flag_service = FeatureFlagService(db)
    stats = flag_service.get_stats()

    return FeatureFlagStatsResponse(**stats)


# User Management Endpoints

@router.get("/users", response_model=AdminUserListResponse)
async def list_users(
    role: Optional[UserRole] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    List all users with optional filtering.

    Args:
        role: Filter by user role
        is_active: Filter by active status
        search: Search by email or name
        skip: Number to skip
        limit: Maximum number to return
        current_user: Current admin user
        db: Database session

    Returns:
        List of users
    """
    user_repo = UserRepository(db)

    if search:
        users = user_repo.search_by_email(search, skip, limit)
    else:
        users = user_repo.get_all(skip, limit)

    # Apply filters
    if role:
        users = [u for u in users if u.role == role]

    if is_active is not None:
        users = [u for u in users if u.is_active == is_active]

    total = user_repo.count()

    return AdminUserListResponse(
        users=[AdminUserResponse.model_validate(u) for u in users],
        total=total,
        skip=skip,
        limit=limit
    )


@router.get("/users/{user_id}", response_model=AdminUserResponse)
async def get_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get user by ID.

    Args:
        user_id: User ID
        current_user: Current admin user
        db: Database session

    Returns:
        User details
    """
    user_repo = UserRepository(db)
    user = user_repo.get(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )

    return AdminUserResponse.model_validate(user)


@router.put("/users/{user_id}", response_model=AdminUserResponse)
async def update_user(
    user_id: int,
    request: AdminUserUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Update user details.

    Args:
        user_id: User ID
        request: Update request
        current_user: Current admin user
        db: Database session

    Returns:
        Updated user
    """
    user_repo = UserRepository(db)

    update_data = request.model_dump(exclude_unset=True)

    # Convert role enum to value
    if 'role' in update_data:
        update_data['role'] = update_data['role'].value

    user = user_repo.update(user_id, update_data)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )

    logger.info(f"Admin {current_user.email} updated user {user.email}")

    return AdminUserResponse.model_validate(user)


@router.post("/users/{user_id}/ban")
async def ban_user(
    user_id: int,
    request: UserBanRequest,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Ban a user (deactivate account).

    Args:
        user_id: User ID
        request: Ban request with reason
        current_user: Current admin user
        db: Database session

    Returns:
        Success message
    """
    user_repo = UserRepository(db)
    user = user_repo.get(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )

    if user.id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot ban yourself"
        )

    user_repo.update(user_id, {"is_active": False})

    logger.warning(f"Admin {current_user.email} banned user {user.email}. Reason: {request.reason}")

    return {"message": f"User {user.email} has been banned"}


@router.post("/users/{user_id}/unban")
async def unban_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Unban a user (reactivate account).

    Args:
        user_id: User ID
        current_user: Current admin user
        db: Database session

    Returns:
        Success message
    """
    user_repo = UserRepository(db)
    user = user_repo.get(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )

    user_repo.update(user_id, {"is_active": True})

    logger.info(f"Admin {current_user.email} unbanned user {user.email}")

    return {"message": f"User {user.email} has been unbanned"}


# System Health Endpoints

@router.get("/health", response_model=SystemHealthResponse)
async def get_system_health(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get system health status.

    Args:
        current_user: Current admin user
        db: Database session

    Returns:
        System health information
    """
    # Check database
    try:
        db.execute("SELECT 1")
        database_status = "healthy"
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        database_status = "unhealthy"

    # Check Redis (simplified - would need actual Redis connection)
    redis_status = "unknown"

    # Get WebSocket connection count
    ws_connections = manager.get_total_connections()

    # Get Celery worker count (simplified - would need actual Celery inspection)
    celery_workers = 0

    return SystemHealthResponse(
        status="healthy" if database_status == "healthy" else "degraded",
        database=database_status,
        redis=redis_status,
        celery_workers=celery_workers,
        websocket_connections=ws_connections,
        timestamp=datetime.utcnow()
    )


@router.get("/stats", response_model=SystemStatsResponse)
async def get_system_stats(
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Get system statistics.

    Args:
        current_user: Current admin user
        db: Database session

    Returns:
        System statistics
    """
    user_repo = UserRepository(db)
    project_repo = ProjectRepository(db)
    job_repo = RenderJobRepository(db)
    subscription_repo = SubscriptionRepository(db)

    total_users = user_repo.count()
    active_users = user_repo.count_active_users()
    total_projects = project_repo.count()
    total_render_jobs = job_repo.count()

    from app.models.render_job import JobStatus
    completed_jobs = job_repo.count_by_status(JobStatus.COMPLETED)
    failed_jobs = job_repo.count_by_status(JobStatus.FAILED)

    active_subscriptions = subscription_repo.count_active()

    # Revenue calculation (simplified - would need actual payment data)
    total_revenue = 0.0

    # Storage calculation (simplified - would need actual storage provider)
    storage_used_gb = 0.0

    return SystemStatsResponse(
        total_users=total_users,
        active_users=active_users,
        total_projects=total_projects,
        total_render_jobs=total_render_jobs,
        completed_jobs=completed_jobs,
        failed_jobs=failed_jobs,
        active_subscriptions=active_subscriptions,
        total_revenue=total_revenue,
        storage_used_gb=storage_used_gb,
        timestamp=datetime.utcnow()
    )


# Job Monitoring Endpoints

@router.get("/jobs", response_model=AdminJobListResponse)
async def list_all_jobs(
    status_filter: Optional[str] = None,
    user_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    List all render jobs across all users.

    Args:
        status_filter: Filter by job status
        user_id: Filter by user ID
        skip: Number to skip
        limit: Maximum number to return
        current_user: Current admin user
        db: Database session

    Returns:
        List of render jobs
    """
    job_repo = RenderJobRepository(db)
    user_repo = UserRepository(db)
    project_repo = ProjectRepository(db)

    if user_id:
        from app.models.render_job import JobStatus
        status_enum = JobStatus(status_filter) if status_filter else None
        jobs = job_repo.get_by_user(user_id, skip, limit, status=status_enum)
    else:
        jobs = job_repo.get_all(skip, limit)

    total = job_repo.count()

    # Enrich with user and project info
    admin_jobs = []
    for job in jobs:
        user = user_repo.get(job.user_id)
        project = project_repo.get(job.project_id)

        admin_jobs.append({
            "id": job.id,
            "user_id": job.user_id,
            "user_email": user.email if user else "unknown",
            "project_id": job.project_id,
            "project_title": project.title if project else "unknown",
            "job_type": job.job_type.value,
            "status": job.status.value,
            "progress": job.progress,
            "current_stage": job.current_stage,
            "error_message": job.error_message,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "duration_seconds": job.duration_seconds,
            "created_at": job.created_at
        })

    return AdminJobListResponse(
        jobs=admin_jobs,
        total=total,
        skip=skip,
        limit=limit
    )


# Subscription Management Endpoints

@router.get("/subscriptions", response_model=AdminSubscriptionListResponse)
async def list_all_subscriptions(
    status_filter: Optional[str] = None,
    plan_id: Optional[int] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    List all subscriptions.

    Args:
        status_filter: Filter by subscription status
        plan_id: Filter by plan ID
        skip: Number to skip
        limit: Maximum number to return
        current_user: Current admin user
        db: Database session

    Returns:
        List of subscriptions
    """
    subscription_repo = SubscriptionRepository(db)
    user_repo = UserRepository(db)

    subscriptions = subscription_repo.get_all(skip, limit)

    # Apply filters
    if status_filter:
        subscriptions = [s for s in subscriptions if s.status == status_filter]

    if plan_id:
        subscriptions = [s for s in subscriptions if s.plan_id == plan_id]

    total = subscription_repo.count()

    # Enrich with user info
    admin_subs = []
    for sub in subscriptions:
        user = user_repo.get(sub.user_id)

        admin_subs.append({
            "id": sub.id,
            "user_id": sub.user_id,
            "user_email": user.email if user else "unknown",
            "plan_id": sub.plan_id,
            "plan_name": sub.plan.name if sub.plan else "unknown",
            "status": sub.status,
            "current_period_start": sub.current_period_start,
            "current_period_end": sub.current_period_end,
            "cancel_at_period_end": sub.cancel_at_period_end,
            "created_at": sub.created_at,
            "updated_at": sub.updated_at
        })

    return AdminSubscriptionListResponse(
        subscriptions=admin_subs,
        total=total,
        skip=skip,
        limit=limit
    )
