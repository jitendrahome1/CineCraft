"""
Repository for Character model.
Handles data access operations for characters.
"""
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_

from app.repositories.base import BaseRepository
from app.models.character import Character
from app.core.logging import get_logger

logger = get_logger(__name__)


class CharacterRepository(BaseRepository[Character]):
    """Repository for Character CRUD operations."""

    def __init__(self, db: Session):
        super().__init__(Character, db)

    def get_by_project(self, project_id: int) -> List[Character]:
        """
        Get all characters for a project.

        Args:
            project_id: Project ID

        Returns:
            List of characters
        """
        return (
            self.db.query(Character)
            .filter(Character.project_id == project_id)
            .order_by(Character.name)
            .all()
        )

    def get_by_name(self, project_id: int, name: str) -> Optional[Character]:
        """
        Get character by name within a project.

        Args:
            project_id: Project ID
            name: Character name

        Returns:
            Character or None
        """
        return (
            self.db.query(Character)
            .filter(
                and_(
                    Character.project_id == project_id,
                    Character.name == name
                )
            )
            .first()
        )

    def get_by_role(self, project_id: int, role: str) -> List[Character]:
        """
        Get characters by role.

        Args:
            project_id: Project ID
            role: Character role (e.g., "protagonist", "antagonist")

        Returns:
            List of characters with specified role
        """
        return (
            self.db.query(Character)
            .filter(
                and_(
                    Character.project_id == project_id,
                    Character.role == role
                )
            )
            .all()
        )

    def bulk_create(self, project_id: int, characters_data: List[dict]) -> List[Character]:
        """
        Create multiple characters at once.

        Args:
            project_id: Project ID
            characters_data: List of character data dictionaries

        Returns:
            List of created characters
        """
        characters = []
        for char_data in characters_data:
            char_data['project_id'] = project_id
            character = Character(**char_data)
            self.db.add(character)
            characters.append(character)

        self.db.commit()
        logger.info(f"Bulk created {len(characters)} characters for project {project_id}")
        return characters

    def delete_by_project(self, project_id: int) -> int:
        """
        Delete all characters for a project.

        Args:
            project_id: Project ID

        Returns:
            Number of deleted characters
        """
        count = (
            self.db.query(Character)
            .filter(Character.project_id == project_id)
            .delete()
        )
        self.db.commit()
        logger.info(f"Deleted {count} characters for project {project_id}")
        return count

    def update_visual_reference(
        self,
        character_id: int,
        reference_image_url: str = None,
        visual_prompt: str = None
    ) -> Optional[Character]:
        """
        Update character's visual reference.

        Args:
            character_id: Character ID
            reference_image_url: URL of reference image
            visual_prompt: Visual prompt for generation

        Returns:
            Updated character or None
        """
        character = self.get(character_id)
        if character:
            if reference_image_url:
                character.reference_image_url = reference_image_url
            if visual_prompt:
                character.visual_prompt = visual_prompt
            self.db.commit()
            self.db.refresh(character)
            logger.info(f"Updated visual reference for character {character_id}")
        return character

    def get_character_count(self, project_id: int) -> int:
        """
        Get total number of characters in a project.

        Args:
            project_id: Project ID

        Returns:
            Character count
        """
        return self.db.query(Character).filter(Character.project_id == project_id).count()
