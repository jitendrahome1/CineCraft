"""
Repository for Scene model.
Handles data access operations for scenes.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.repositories.base import BaseRepository
from app.models.scene import Scene
from app.core.logging import get_logger

logger = get_logger(__name__)


class SceneRepository(BaseRepository[Scene]):
    """Repository for Scene CRUD operations."""

    def __init__(self, db: Session):
        super().__init__(Scene, db)

    def get_by_project(self, project_id: int) -> List[Scene]:
        """
        Get all scenes for a project, ordered by sequence.

        Args:
            project_id: Project ID

        Returns:
            List of scenes ordered by sequence_number
        """
        return (
            self.db.query(Scene)
            .filter(Scene.project_id == project_id)
            .order_by(Scene.sequence_number)
            .all()
        )

    def get_by_project_and_sequence(
        self,
        project_id: int,
        sequence_number: int
    ) -> Optional[Scene]:
        """
        Get a specific scene by project and sequence number.

        Args:
            project_id: Project ID
            sequence_number: Scene sequence number

        Returns:
            Scene or None
        """
        return (
            self.db.query(Scene)
            .filter(
                and_(
                    Scene.project_id == project_id,
                    Scene.sequence_number == sequence_number
                )
            )
            .first()
        )

    def get_incomplete_scenes(self, project_id: int) -> List[Scene]:
        """
        Get scenes that don't have all media generated.

        Args:
            project_id: Project ID

        Returns:
            List of incomplete scenes
        """
        return (
            self.db.query(Scene)
            .filter(
                and_(
                    Scene.project_id == project_id,
                    or_(
                        Scene.image_url == None,
                        Scene.audio_url == None
                    )
                )
            )
            .order_by(Scene.sequence_number)
            .all()
        )

    def get_scenes_without_images(self, project_id: int) -> List[Scene]:
        """
        Get scenes that need image generation.

        Args:
            project_id: Project ID

        Returns:
            List of scenes without images
        """
        return (
            self.db.query(Scene)
            .filter(
                and_(
                    Scene.project_id == project_id,
                    Scene.image_url == None
                )
            )
            .order_by(Scene.sequence_number)
            .all()
        )

    def get_scenes_without_audio(self, project_id: int) -> List[Scene]:
        """
        Get scenes that need audio generation.

        Args:
            project_id: Project ID

        Returns:
            List of scenes without audio
        """
        return (
            self.db.query(Scene)
            .filter(
                and_(
                    Scene.project_id == project_id,
                    Scene.audio_url == None
                )
            )
            .order_by(Scene.sequence_number)
            .all()
        )

    def get_next_sequence_number(self, project_id: int) -> int:
        """
        Get the next sequence number for a new scene.

        Args:
            project_id: Project ID

        Returns:
            Next available sequence number
        """
        max_seq = (
            self.db.query(Scene.sequence_number)
            .filter(Scene.project_id == project_id)
            .order_by(Scene.sequence_number.desc())
            .first()
        )
        return (max_seq[0] + 1) if max_seq else 1

    def reorder_scenes(self, project_id: int, scene_order: List[int]) -> List[Scene]:
        """
        Reorder scenes based on new sequence.

        Args:
            project_id: Project ID
            scene_order: List of scene IDs in desired order

        Returns:
            List of reordered scenes
        """
        scenes = []
        for index, scene_id in enumerate(scene_order, start=1):
            scene = self.get(scene_id)
            if scene and scene.project_id == project_id:
                scene.sequence_number = index
                self.db.add(scene)
                scenes.append(scene)

        self.db.commit()
        logger.info(f"Reordered {len(scenes)} scenes for project {project_id}")
        return scenes

    def bulk_create(self, project_id: int, scenes_data: List[dict]) -> List[Scene]:
        """
        Create multiple scenes at once.

        Args:
            project_id: Project ID
            scenes_data: List of scene data dictionaries

        Returns:
            List of created scenes
        """
        scenes = []
        for index, scene_data in enumerate(scenes_data, start=1):
            scene_data['project_id'] = project_id
            scene_data['sequence_number'] = index
            scene = Scene(**scene_data)
            self.db.add(scene)
            scenes.append(scene)

        self.db.commit()
        logger.info(f"Bulk created {len(scenes)} scenes for project {project_id}")
        return scenes

    def delete_by_project(self, project_id: int) -> int:
        """
        Delete all scenes for a project.

        Args:
            project_id: Project ID

        Returns:
            Number of deleted scenes
        """
        count = (
            self.db.query(Scene)
            .filter(Scene.project_id == project_id)
            .delete()
        )
        self.db.commit()
        logger.info(f"Deleted {count} scenes for project {project_id}")
        return count

    def get_scene_count(self, project_id: int) -> int:
        """
        Get total number of scenes in a project.

        Args:
            project_id: Project ID

        Returns:
            Scene count
        """
        return self.db.query(Scene).filter(Scene.project_id == project_id).count()


# Need to add or_ import
from sqlalchemy import or_
