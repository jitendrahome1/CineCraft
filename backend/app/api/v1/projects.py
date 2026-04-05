"""
Project API endpoints.
Handles project CRUD operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import List, Optional
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.project import ProjectStatus
from app.services.project import ProjectService
from app.schemas.project import (
    ProjectCreateRequest,
    ProjectUpdateRequest,
    ProjectResponse,
    ProjectDetailResponse,
    ProjectStatsResponse,
    ProjectVisibilityRequest
)
from app.core.errors import ProjectNotFoundError, AuthorizationError, ValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    request: ProjectCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new project.

    Args:
        request: Project creation data
        current_user: Current user
        db: Database session

    Returns:
        Created project

    Raises:
        HTTPException: If creation fails
    """
    try:
        project_service = ProjectService(db)
        project = project_service.create_project(
            user_id=current_user.id,
            title=request.title,
            description=request.description,
            story_prompt=request.story_prompt,
            metadata=request.metadata,
            language=request.language,
            video_length=request.video_length
        )
        return project

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("", response_model=List[ProjectResponse])
async def list_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    status_filter: Optional[ProjectStatus] = None,
    include_archived: bool = False,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List user's projects.

    Args:
        skip: Number of records to skip
        limit: Maximum number of records
        status_filter: Optional status filter
        include_archived: Include archived projects
        current_user: Current user
        db: Database session

    Returns:
        List of projects
    """
    project_service = ProjectService(db)
    projects = project_service.list_user_projects(
        user_id=current_user.id,
        skip=skip,
        limit=limit,
        status=status_filter,
        include_archived=include_archived
    )
    return projects


@router.get("/search", response_model=List[ProjectResponse])
async def search_projects(
    q: str = Query(..., min_length=1),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search user's projects.

    Args:
        q: Search query
        skip: Number of records to skip
        limit: Maximum number of records
        current_user: Current user
        db: Database session

    Returns:
        List of matching projects
    """
    project_service = ProjectService(db)
    projects = project_service.search_projects(
        user_id=current_user.id,
        query=q,
        skip=skip,
        limit=limit
    )
    return projects


@router.get("/public", response_model=List[ProjectResponse])
async def list_public_projects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    List public projects (no authentication required).

    Args:
        skip: Number of records to skip
        limit: Maximum number of records
        db: Database session

    Returns:
        List of public projects
    """
    project_service = ProjectService(db)
    projects = project_service.get_public_projects(skip=skip, limit=limit)
    return projects


@router.get("/{project_id}", response_model=ProjectDetailResponse)
async def get_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get project details.

    Args:
        project_id: Project ID
        current_user: Current user
        db: Database session

    Returns:
        Project with scenes and characters

    Raises:
        HTTPException: If project not found or access denied
    """
    try:
        project_service = ProjectService(db)
        project = project_service.get_project_with_details(
            project_id=project_id,
            user_id=current_user.id
        )
        return project

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.get("/{project_id}/stats", response_model=ProjectStatsResponse)
async def get_project_stats(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get project statistics.

    Args:
        project_id: Project ID
        current_user: Current user
        db: Database session

    Returns:
        Project statistics

    Raises:
        HTTPException: If project not found or access denied
    """
    try:
        project_service = ProjectService(db)
        stats = project_service.get_project_stats(
            project_id=project_id,
            user_id=current_user.id
        )
        return stats

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    request: ProjectUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a project.

    Args:
        project_id: Project ID
        request: Update data
        current_user: Current user
        db: Database session

    Returns:
        Updated project

    Raises:
        HTTPException: If project not found or access denied
    """
    try:
        project_service = ProjectService(db)
        project = project_service.update_project(
            project_id=project_id,
            user_id=current_user.id,
            **request.model_dump(exclude_unset=True)
        )
        return project

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.post("/{project_id}/visibility", response_model=ProjectResponse)
async def set_project_visibility(
    project_id: int,
    request: ProjectVisibilityRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Set project visibility (public/private).

    Args:
        project_id: Project ID
        request: Visibility setting
        current_user: Current user
        db: Database session

    Returns:
        Updated project

    Raises:
        HTTPException: If project not found or access denied
    """
    try:
        project_service = ProjectService(db)
        project = project_service.set_project_visibility(
            project_id=project_id,
            user_id=current_user.id,
            is_public=request.is_public
        )
        return project

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.post("/{project_id}/archive", response_model=ProjectResponse)
async def archive_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Archive a project.

    Args:
        project_id: Project ID
        current_user: Current user
        db: Database session

    Returns:
        Archived project

    Raises:
        HTTPException: If project not found or access denied
    """
    try:
        project_service = ProjectService(db)
        project = project_service.archive_project(
            project_id=project_id,
            user_id=current_user.id
        )
        return project

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a project.

    Args:
        project_id: Project ID
        current_user: Current user
        db: Database session

    Raises:
        HTTPException: If project not found or access denied
    """
    try:
        project_service = ProjectService(db)
        project_service.delete_project(
            project_id=project_id,
            user_id=current_user.id
        )

    except ProjectNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
