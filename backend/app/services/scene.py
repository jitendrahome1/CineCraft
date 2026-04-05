"""
Scene service for business logic.
Handles scene management operations.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.repositories.scene import SceneRepository
from app.repositories.project import ProjectRepository
from app.models.scene import Scene
from app.core.errors import (
    SceneNotFoundError,
    AuthorizationError,
    ValidationError
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class SceneService:
    """Service for scene management."""

    def __init__(self, db: Session):
        self.db = db
        self.scene_repo = SceneRepository(db)
        self.project_repo = ProjectRepository(db)

    def create_scene(
        self,
        project_id: int,
        user_id: int,
        description: str,
        narration: Optional[str] = None,
        visual_description: Optional[str] = None,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Scene:
        """
        Create a new scene.

        Args:
            project_id: Project ID
            user_id: User ID (for permission check)
            description: Scene description
            narration: Optional narration text
            visual_description: Optional visual description
            title: Optional scene title
            metadata: Optional metadata

        Returns:
            Created scene

        Raises:
            SceneNotFoundError: If project not found
            AuthorizationError: If user doesn't own project
            ValidationError: If validation fails
        """
        # Check project exists and user owns it
        project = self.project_repo.get(project_id)
        if not project:
            raise SceneNotFoundError(f"Project {project_id} not found")

        if project.user_id != user_id:
            raise AuthorizationError("You don't have permission to add scenes to this project")

        if not description or len(description.strip()) == 0:
            raise ValidationError("Scene description cannot be empty")

        # Get next sequence number
        sequence_number = self.scene_repo.get_next_sequence_number(project_id)

        scene_data = {
            "project_id": project_id,
            "sequence_number": sequence_number,
            "description": description.strip(),
            "narration": narration,
            "visual_description": visual_description,
            "title": title,
            "metadata": metadata or {}
        }

        scene = self.scene_repo.create(scene_data)
        logger.info(f"Created scene {scene.id} for project {project_id}")
        return scene

    def get_scene(self, scene_id: int, user_id: Optional[int] = None) -> Scene:
        """
        Get a scene by ID.

        Args:
            scene_id: Scene ID
            user_id: Optional user ID for permission check

        Returns:
            Scene

        Raises:
            SceneNotFoundError: If scene not found
            AuthorizationError: If user doesn't have access
        """
        scene = self.scene_repo.get(scene_id)

        if not scene:
            raise SceneNotFoundError(f"Scene {scene_id} not found")

        # Check permissions if user_id provided
        if user_id is not None:
            project = self.project_repo.get(scene.project_id)
            if project and project.user_id != user_id and not project.is_public:
                raise AuthorizationError("You don't have permission to access this scene")

        return scene

    def list_project_scenes(self, project_id: int, user_id: Optional[int] = None) -> List[Scene]:
        """
        List all scenes for a project.

        Args:
            project_id: Project ID
            user_id: Optional user ID for permission check

        Returns:
            List of scenes ordered by sequence

        Raises:
            SceneNotFoundError: If project not found
            AuthorizationError: If user doesn't have access
        """
        # Check project exists and permissions
        project = self.project_repo.get(project_id)
        if not project:
            raise SceneNotFoundError(f"Project {project_id} not found")

        if user_id is not None and project.user_id != user_id and not project.is_public:
            raise AuthorizationError("You don't have permission to access this project")

        return self.scene_repo.get_by_project(project_id)

    def update_scene(
        self,
        scene_id: int,
        user_id: int,
        **update_data
    ) -> Scene:
        """
        Update a scene.

        Args:
            scene_id: Scene ID
            user_id: User ID (for permission check)
            **update_data: Fields to update

        Returns:
            Updated scene

        Raises:
            SceneNotFoundError: If scene not found
            AuthorizationError: If user doesn't own project
        """
        scene = self.get_scene(scene_id, user_id)

        # Check project ownership
        project = self.project_repo.get(scene.project_id)
        if project.user_id != user_id:
            raise AuthorizationError("You don't have permission to update this scene")

        # Filter allowed fields
        allowed_fields = [
            'title', 'description', 'narration', 'visual_description',
            'metadata', 'duration', 'subtitle_text'
        ]
        filtered_data = {k: v for k, v in update_data.items() if k in allowed_fields}

        updated_scene = self.scene_repo.update(scene, filtered_data)
        logger.info(f"Updated scene {scene_id}")
        return updated_scene

    def delete_scene(self, scene_id: int, user_id: int) -> bool:
        """
        Delete a scene.

        Args:
            scene_id: Scene ID
            user_id: User ID (for permission check)

        Returns:
            True if deleted

        Raises:
            SceneNotFoundError: If scene not found
            AuthorizationError: If user doesn't own project
        """
        scene = self.get_scene(scene_id, user_id)

        # Check project ownership
        project = self.project_repo.get(scene.project_id)
        if project.user_id != user_id:
            raise AuthorizationError("You don't have permission to delete this scene")

        self.scene_repo.delete(scene_id)
        logger.info(f"Deleted scene {scene_id}")
        return True

    def reorder_scenes(
        self,
        project_id: int,
        user_id: int,
        scene_order: List[int]
    ) -> List[Scene]:
        """
        Reorder scenes in a project.

        Args:
            project_id: Project ID
            user_id: User ID (for permission check)
            scene_order: List of scene IDs in desired order

        Returns:
            List of reordered scenes

        Raises:
            SceneNotFoundError: If project not found
            AuthorizationError: If user doesn't own project
        """
        # Check project ownership
        project = self.project_repo.get(project_id)
        if not project:
            raise SceneNotFoundError(f"Project {project_id} not found")

        if project.user_id != user_id:
            raise AuthorizationError("You don't have permission to reorder scenes")

        scenes = self.scene_repo.reorder_scenes(project_id, scene_order)
        logger.info(f"Reordered scenes for project {project_id}")
        return scenes

    def bulk_create_scenes(
        self,
        project_id: int,
        user_id: int,
        scenes_data: List[Dict[str, Any]]
    ) -> List[Scene]:
        """
        Create multiple scenes at once.

        Args:
            project_id: Project ID
            user_id: User ID (for permission check)
            scenes_data: List of scene data dictionaries

        Returns:
            List of created scenes

        Raises:
            SceneNotFoundError: If project not found
            AuthorizationError: If user doesn't own project
        """
        # Check project ownership
        project = self.project_repo.get(project_id)
        if not project:
            raise SceneNotFoundError(f"Project {project_id} not found")

        if project.user_id != user_id:
            raise AuthorizationError("You don't have permission to add scenes to this project")

        scenes = self.scene_repo.bulk_create(project_id, scenes_data)
        logger.info(f"Bulk created {len(scenes)} scenes for project {project_id}")
        return scenes

    def get_incomplete_scenes(self, project_id: int, user_id: int) -> List[Scene]:
        """
        Get scenes that need media generation.

        Args:
            project_id: Project ID
            user_id: User ID (for permission check)

        Returns:
            List of incomplete scenes

        Raises:
            SceneNotFoundError: If project not found
            AuthorizationError: If user doesn't have access
        """
        # Check project ownership
        project = self.project_repo.get(project_id)
        if not project:
            raise SceneNotFoundError(f"Project {project_id} not found")

        if project.user_id != user_id:
            raise AuthorizationError("You don't have permission to access this project")

        return self.scene_repo.get_incomplete_scenes(project_id)

    def mark_scene_image_generated(
        self,
        scene_id: int,
        image_url: str,
        prompt: Optional[str] = None
    ) -> Scene:
        """
        Mark scene image as generated.

        Args:
            scene_id: Scene ID
            image_url: URL of generated image
            prompt: Optional prompt used

        Returns:
            Updated scene
        """
        scene = self.scene_repo.get(scene_id)
        if not scene:
            raise SceneNotFoundError(f"Scene {scene_id} not found")

        scene.mark_image_generated(image_url, prompt)
        self.db.commit()
        logger.info(f"Marked image generated for scene {scene_id}")
        return scene

    def mark_scene_audio_generated(
        self,
        scene_id: int,
        audio_url: str,
        duration: Optional[float] = None
    ) -> Scene:
        """
        Mark scene audio as generated.

        Args:
            scene_id: Scene ID
            audio_url: URL of generated audio
            duration: Optional audio duration

        Returns:
            Updated scene
        """
        scene = self.scene_repo.get(scene_id)
        if not scene:
            raise SceneNotFoundError(f"Scene {scene_id} not found")

        scene.mark_audio_generated(audio_url, duration)
        self.db.commit()
        logger.info(f"Marked audio generated for scene {scene_id}")
        return scene

    def set_scene_timing(
        self,
        scene_id: int,
        start_time: float,
        duration: float
    ) -> Scene:
        """
        Set scene timing in final video.

        Args:
            scene_id: Scene ID
            start_time: Start time in seconds
            duration: Duration in seconds

        Returns:
            Updated scene
        """
        scene = self.scene_repo.get(scene_id)
        if not scene:
            raise SceneNotFoundError(f"Scene {scene_id} not found")

        scene.set_timing(start_time, duration)
        self.db.commit()
        logger.info(f"Set timing for scene {scene_id}")
        return scene
