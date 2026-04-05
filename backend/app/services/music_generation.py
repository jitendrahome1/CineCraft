"""
Music generation service for CineCraft.
Generates background music for projects using AI providers and stores them.
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.providers.base.music_provider import MusicProvider
from app.services.storage import StorageService
from app.repositories.project import ProjectRepository
from app.models.media_asset import MediaAsset, MediaType
from app.models.project import ProjectStatus
from app.core.errors import ValidationError, AIProviderError
from app.core.logging import get_logger

logger = get_logger(__name__)


class MusicGenerationService:
    """
    Service for generating background music using AI providers.

    Coordinates music generation, storage, and database updates.
    """

    def __init__(
        self,
        db: Session,
        music_provider: MusicProvider,
        storage_service: StorageService
    ):
        """
        Initialize music generation service.

        Args:
            db: Database session
            music_provider: Music generation provider
            storage_service: Storage service for saving audio
        """
        self.db = db
        self.music_provider = music_provider
        self.storage_service = storage_service
        self.project_repo = ProjectRepository(db)

    async def generate_project_music(
        self,
        project_id: int,
        user_id: int,
        duration: int = 60,
        mood: Optional[str] = None,
        genre: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> MediaAsset:
        """
        Generate background music for a project.

        Args:
            project_id: Project ID
            user_id: User ID
            duration: Desired duration in seconds
            mood: Optional mood
            genre: Optional genre
            prompt: Optional custom prompt (uses project title/description if not provided)

        Returns:
            Created MediaAsset

        Raises:
            ValidationError: If project not found or unauthorized
            AIProviderError: If generation fails
        """
        # Get project
        project = self.project_repo.get(project_id)

        if not project:
            raise ValidationError(f"Project {project_id} not found")

        if project.user_id != user_id:
            raise ValidationError("Unauthorized access to project")

        # Build prompt if not provided
        if not prompt:
            prompt = f"Background music for: {project.title}"
            if project.description:
                prompt += f". {project.description[:200]}"

        logger.info(f"Generating background music for project {project_id}")

        # Update project status
        self.project_repo.update_status(project_id, ProjectStatus.GENERATING)

        try:
            # Generate music
            music_bytes = await self.music_provider.generate_music(
                prompt=prompt,
                duration=duration,
                mood=mood,
                genre=genre
            )

            # Determine filename
            filename = f"project_{project_id}_music.mp3"

            # Get cost estimate
            provider_name = self.music_provider.__class__.__name__.replace("Provider", "").lower()
            cost = self.music_provider.get_estimated_cost(duration)

            # Save to storage
            asset = await self.storage_service.save_generated_asset(
                file_data=music_bytes,
                filename=filename,
                user_id=user_id,
                project_id=project_id,
                scene_id=None,  # Music is project-level
                media_type=MediaType.MUSIC,
                generation_provider=provider_name,
                generation_prompt=prompt,
                generation_cost=cost,
                metadata={
                    "mood": mood or "default",
                    "genre": genre or "default",
                    "requested_duration": duration
                }
            )

            # Update asset duration
            asset.duration = duration
            self.db.commit()

            # Update project status
            self.project_repo.update_status(project_id, ProjectStatus.READY)

            logger.info(f"Successfully generated music for project {project_id} (asset {asset.id})")
            return asset

        except AIProviderError as e:
            logger.error(f"Music generation failed for project {project_id}: {e}")
            self.project_repo.update_status(project_id, ProjectStatus.FAILED)
            raise
        except Exception as e:
            logger.exception(f"Unexpected error generating music for project {project_id}")
            self.project_repo.update_status(project_id, ProjectStatus.FAILED)
            raise AIProviderError(f"Music generation failed: {str(e)}")

    async def regenerate_project_music(
        self,
        project_id: int,
        user_id: int,
        duration: int = 60,
        mood: Optional[str] = None,
        genre: Optional[str] = None,
        prompt: Optional[str] = None
    ) -> MediaAsset:
        """
        Regenerate background music for a project (deletes old music).

        Args:
            project_id: Project ID
            user_id: User ID
            duration: Desired duration in seconds
            mood: Optional mood
            genre: Optional genre
            prompt: Optional custom prompt

        Returns:
            Newly created MediaAsset

        Raises:
            ValidationError: If project not found or unauthorized
            AIProviderError: If generation fails
        """
        # Delete existing music for this project
        old_assets = self.storage_service.repository.get_by_project(
            project_id=project_id,
            media_type=MediaType.MUSIC
        )

        for asset in old_assets:
            try:
                await self.storage_service.delete_asset(
                    asset_id=asset.id,
                    user_id=user_id
                )
            except Exception as e:
                logger.warning(f"Failed to delete old music {asset.id}: {e}")

        # Generate new music
        return await self.generate_project_music(
            project_id=project_id,
            user_id=user_id,
            duration=duration,
            mood=mood,
            genre=genre,
            prompt=prompt
        )

    def get_project_music(self, project_id: int) -> list[MediaAsset]:
        """
        Get all background music for a project.

        Args:
            project_id: Project ID

        Returns:
            List of music assets
        """
        return self.storage_service.repository.get_by_project(
            project_id=project_id,
            media_type=MediaType.MUSIC
        )

    def get_generation_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get music generation statistics for a user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with statistics
        """
        assets = self.storage_service.repository.get_generated_assets(
            user_id=user_id,
            provider="suno"
        )

        total_cost = sum(asset.generation_cost or 0 for asset in assets)
        total_duration = sum(asset.duration or 0 for asset in assets)

        return {
            "total_tracks": len(assets),
            "total_duration_seconds": total_duration,
            "total_duration_minutes": round(total_duration / 60, 1),
            "total_cost_cents": total_cost,
            "total_cost_dollars": round(total_cost / 100, 2),
            "provider": "suno"
        }
