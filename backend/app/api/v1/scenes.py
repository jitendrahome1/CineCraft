"""
Scene API endpoints.
Handles scene CRUD operations.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.scene import SceneService
from app.schemas.scene import (
    SceneCreateRequest,
    SceneUpdateRequest,
    SceneResponse,
    SceneBulkCreateRequest,
    SceneReorderRequest,
    SceneListResponse
)
from app.core.errors import SceneNotFoundError, ProjectNotFoundError, AuthorizationError, ValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/projects/{project_id}/scenes", response_model=SceneResponse, status_code=status.HTTP_201_CREATED)
async def create_scene(
    project_id: int,
    request: SceneCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create a new scene in a project.

    Args:
        project_id: Project ID
        request: Scene creation data
        current_user: Current user
        db: Database session

    Returns:
        Created scene

    Raises:
        HTTPException: If creation fails
    """
    try:
        scene_service = SceneService(db)
        scene = scene_service.create_scene(
            project_id=project_id,
            user_id=current_user.id,
            description=request.description,
            narration=request.narration,
            visual_description=request.visual_description,
            title=request.title,
            metadata=request.metadata
        )
        return scene

    except SceneNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/projects/{project_id}/scenes/bulk", response_model=List[SceneResponse], status_code=status.HTTP_201_CREATED)
async def bulk_create_scenes(
    project_id: int,
    request: SceneBulkCreateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Create multiple scenes at once.

    Args:
        project_id: Project ID
        request: Bulk creation data
        current_user: Current user
        db: Database session

    Returns:
        List of created scenes

    Raises:
        HTTPException: If creation fails
    """
    try:
        scene_service = SceneService(db)
        scenes_data = [scene.model_dump() for scene in request.scenes]
        scenes = scene_service.bulk_create_scenes(
            project_id=project_id,
            user_id=current_user.id,
            scenes_data=scenes_data
        )
        return scenes

    except SceneNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.get("/projects/{project_id}/scenes", response_model=SceneListResponse)
async def list_project_scenes(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List all scenes for a project.

    Args:
        project_id: Project ID
        current_user: Current user
        db: Database session

    Returns:
        List of scenes

    Raises:
        HTTPException: If project not found or access denied
    """
    try:
        scene_service = SceneService(db)
        scenes = scene_service.list_project_scenes(
            project_id=project_id,
            user_id=current_user.id
        )
        # Convert scenes to dicts to avoid metadata attribute conflict
        scenes_data = []
        for scene in scenes:
            scene_dict = {
                "id": scene.id,
                "project_id": scene.project_id,
                "sequence_number": scene.sequence_number,
                "title": scene.title,
                "description": scene.description,
                "narration": scene.narration,
                "visual_description": scene.visual_description,
                "metadata": scene.scene_metadata if hasattr(scene, 'scene_metadata') else {},
                "duration": scene.duration,
                "start_time": scene.start_time,
                "end_time": scene.end_time,
                "image_url": scene.image_url,
                "image_prompt": scene.image_prompt,
                "audio_url": scene.audio_url,
                "audio_duration": scene.audio_duration,
                "subtitle_text": scene.subtitle_text,
                "subtitle_start_time": scene.subtitle_start_time,
                "subtitle_end_time": scene.subtitle_end_time,
                "image_generated_at": scene.image_generated_at,
                "audio_generated_at": scene.audio_generated_at,
                "is_complete": scene.is_complete,
                "has_image": scene.has_image,
                "has_audio": scene.has_audio,
                "created_at": scene.created_at,
                "updated_at": scene.updated_at,
            }
            scenes_data.append(scene_dict)
        return SceneListResponse(scenes=scenes_data, total=len(scenes_data))

    except SceneNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.get("/projects/{project_id}/scenes/incomplete", response_model=List[SceneResponse])
async def list_incomplete_scenes(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    List scenes that need media generation.

    Args:
        project_id: Project ID
        current_user: Current user
        db: Database session

    Returns:
        List of incomplete scenes

    Raises:
        HTTPException: If project not found or access denied
    """
    try:
        scene_service = SceneService(db)
        scenes = scene_service.get_incomplete_scenes(
            project_id=project_id,
            user_id=current_user.id
        )
        return scenes

    except SceneNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.get("/scenes/{scene_id}", response_model=SceneResponse)
async def get_scene(
    scene_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific scene.

    Args:
        scene_id: Scene ID
        current_user: Current user
        db: Database session

    Returns:
        Scene details

    Raises:
        HTTPException: If scene not found or access denied
    """
    try:
        scene_service = SceneService(db)
        scene = scene_service.get_scene(
            scene_id=scene_id,
            user_id=current_user.id
        )
        return scene

    except SceneNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.put("/scenes/{scene_id}", response_model=SceneResponse)
async def update_scene(
    scene_id: int,
    request: SceneUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update a scene.

    Args:
        scene_id: Scene ID
        request: Update data
        current_user: Current user
        db: Database session

    Returns:
        Updated scene

    Raises:
        HTTPException: If scene not found or access denied
    """
    try:
        scene_service = SceneService(db)
        scene = scene_service.update_scene(
            scene_id=scene_id,
            user_id=current_user.id,
            **request.model_dump(exclude_unset=True)
        )
        return scene

    except SceneNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.post("/projects/{project_id}/scenes/reorder", response_model=List[SceneResponse])
async def reorder_scenes(
    project_id: int,
    request: SceneReorderRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Reorder scenes in a project.

    Args:
        project_id: Project ID
        request: Scene order
        current_user: Current user
        db: Database session

    Returns:
        Reordered scenes

    Raises:
        HTTPException: If project not found or access denied
    """
    try:
        scene_service = SceneService(db)
        scenes = scene_service.reorder_scenes(
            project_id=project_id,
            user_id=current_user.id,
            scene_order=request.scene_order
        )
        return scenes

    except SceneNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.delete("/scenes/{scene_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_scene(
    scene_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete a scene.

    Args:
        scene_id: Scene ID
        current_user: Current user
        db: Database session

    Raises:
        HTTPException: If scene not found or access denied
    """
    try:
        scene_service = SceneService(db)
        scene_service.delete_scene(
            scene_id=scene_id,
            user_id=current_user.id
        )

    except SceneNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except PermissionError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )
