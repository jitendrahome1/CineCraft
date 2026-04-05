"""
Voice generation service for CineCraft.
Generates voice narration for scenes using AI providers and stores them.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.providers.base.voice_provider import VoiceProvider
from app.services.storage import StorageService
from app.repositories.project import ProjectRepository
from app.repositories.scene import SceneRepository
from app.models.media_asset import MediaAsset, MediaType
from app.models.project import ProjectStatus
from app.core.errors import ValidationError, AIProviderError
from app.core.logging import get_logger

logger = get_logger(__name__)


class VoiceGenerationService:
    """
    Service for generating voice narration using AI providers.

    Coordinates voice generation, storage, and database updates.
    """

    def __init__(
        self,
        db: Session,
        voice_provider: VoiceProvider,
        storage_service: StorageService
    ):
        """
        Initialize voice generation service.

        Args:
            db: Database session
            voice_provider: Voice generation provider
            storage_service: Storage service for saving audio
        """
        self.db = db
        self.voice_provider = voice_provider
        self.storage_service = storage_service
        self.project_repo = ProjectRepository(db)
        self.scene_repo = SceneRepository(db)

    async def generate_scene_narration(
        self,
        scene_id: int,
        user_id: int,
        voice_id: Optional[str] = None,
        speed: float = 1.0
    ) -> MediaAsset:
        """
        Generate voice narration for a single scene.

        Args:
            scene_id: Scene ID
            user_id: User ID
            voice_id: Optional voice ID
            speed: Speech speed multiplier

        Returns:
            Created MediaAsset

        Raises:
            ValidationError: If scene not found or unauthorized
            AIProviderError: If generation fails
        """
        # Get scene
        scene = self.scene_repo.get(scene_id)

        if not scene:
            raise ValidationError(f"Scene {scene_id} not found")

        # Verify ownership
        project = self.project_repo.get(scene.project_id)
        if not project or project.user_id != user_id:
            raise ValidationError("Unauthorized access to scene")

        # Get narration text from scene
        text = scene.narration

        if not text:
            raise ValidationError(f"Scene {scene_id} has no narration text")

        logger.info(f"Generating narration for scene {scene_id}")

        try:
            # Generate speech
            audio_bytes = await self.voice_provider.generate_speech(
                text=text,
                voice_id=voice_id,
                speed=speed
            )

            # Determine filename
            filename = f"scene_{scene.sequence_number}_narration.mp3"

            # Get cost estimate
            provider_name = self.voice_provider.__class__.__name__.replace("Provider", "").lower()
            cost = self.voice_provider.get_estimated_cost(len(text))

            # Save to storage
            asset = await self.storage_service.save_generated_asset(
                file_data=audio_bytes,
                filename=filename,
                user_id=user_id,
                project_id=scene.project_id,
                scene_id=scene_id,
                media_type=MediaType.AUDIO,
                generation_provider=provider_name,
                generation_prompt=text,
                generation_cost=cost,
                metadata={
                    "voice_id": voice_id or "default",
                    "speed": speed,
                    "character_count": len(text),
                    "duration_estimate": self._estimate_duration(text, speed)
                }
            )

            # Update asset duration
            asset.duration = self._estimate_duration(text, speed)
            self.db.commit()

            logger.info(f"Successfully generated narration for scene {scene_id} (asset {asset.id})")
            return asset

        except AIProviderError as e:
            logger.error(f"Voice generation failed for scene {scene_id}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error generating narration for scene {scene_id}")
            raise AIProviderError(f"Voice generation failed: {str(e)}")

    async def generate_project_narrations(
        self,
        project_id: int,
        user_id: int,
        voice_id: Optional[str] = None,
        speed: float = 1.0
    ) -> List[MediaAsset]:
        """
        Generate voice narrations for all scenes in a project.

        Args:
            project_id: Project ID
            user_id: User ID
            voice_id: Optional voice ID
            speed: Speech speed multiplier

        Returns:
            List of created MediaAssets

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

        # Get all scenes
        scenes = self.scene_repo.get_by_project(project_id)

        if not scenes:
            raise ValidationError(f"Project {project_id} has no scenes")

        logger.info(f"Generating narrations for {len(scenes)} scenes in project {project_id}")

        # Update project status
        self.project_repo.update_status(project_id, ProjectStatus.GENERATING)

        assets = []
        failed_scenes = []

        try:
            for scene in scenes:
                try:
                    asset = await self.generate_scene_narration(
                        scene_id=scene.id,
                        user_id=user_id,
                        voice_id=voice_id,
                        speed=speed
                    )
                    assets.append(asset)

                except Exception as e:
                    logger.error(f"Failed to generate narration for scene {scene.id}: {e}")
                    failed_scenes.append(scene.id)

            if failed_scenes and not assets:
                # All scenes failed
                self.project_repo.update_status(project_id, ProjectStatus.FAILED)
                raise AIProviderError(f"Failed to generate narrations for all scenes")

            elif failed_scenes:
                # Some scenes failed
                logger.warning(f"Failed to generate narrations for scenes: {failed_scenes}")

            # Update project status
            self.project_repo.update_status(project_id, ProjectStatus.READY)

            logger.info(
                f"Successfully generated {len(assets)} narrations for project {project_id} "
                f"({len(failed_scenes)} failed)"
            )

            return assets

        except Exception as e:
            self.project_repo.update_status(project_id, ProjectStatus.FAILED)
            raise

    async def regenerate_scene_narration(
        self,
        scene_id: int,
        user_id: int,
        voice_id: Optional[str] = None,
        speed: float = 1.0
    ) -> MediaAsset:
        """
        Regenerate narration for a scene (deletes old narration).

        Args:
            scene_id: Scene ID
            user_id: User ID
            voice_id: Optional voice ID
            speed: Speech speed multiplier

        Returns:
            Newly created MediaAsset

        Raises:
            ValidationError: If scene not found or unauthorized
            AIProviderError: If generation fails
        """
        # Delete existing narrations for this scene
        old_assets = self.storage_service.repository.get_by_scene(
            scene_id=scene_id,
            media_type=MediaType.AUDIO
        )

        for asset in old_assets:
            try:
                await self.storage_service.delete_asset(
                    asset_id=asset.id,
                    user_id=user_id
                )
            except Exception as e:
                logger.warning(f"Failed to delete old narration {asset.id}: {e}")

        # Generate new narration
        return await self.generate_scene_narration(
            scene_id=scene_id,
            user_id=user_id,
            voice_id=voice_id,
            speed=speed
        )

    def _estimate_duration(self, text: str, speed: float = 1.0) -> int:
        """
        Estimate audio duration based on text length.

        Args:
            text: Text to convert to speech
            speed: Speech speed multiplier

        Returns:
            Estimated duration in seconds
        """
        # Average reading speed: ~150 words per minute
        # = 2.5 words per second
        # Average word length: ~5 characters
        # = ~12.5 characters per second at normal speed

        chars_per_second = 12.5 * speed
        duration = len(text) / chars_per_second

        return max(1, int(duration))

    def get_scene_narrations(self, scene_id: int) -> List[MediaAsset]:
        """
        Get all narrations for a scene.

        Args:
            scene_id: Scene ID

        Returns:
            List of audio assets
        """
        return self.storage_service.repository.get_by_scene(
            scene_id=scene_id,
            media_type=MediaType.AUDIO
        )

    def get_project_narrations(self, project_id: int) -> List[MediaAsset]:
        """
        Get all narrations for a project.

        Args:
            project_id: Project ID

        Returns:
            List of audio assets
        """
        return self.storage_service.repository.get_by_project(
            project_id=project_id,
            media_type=MediaType.AUDIO
        )

    def get_generation_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get voice generation statistics for a user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with statistics
        """
        assets = self.storage_service.repository.get_generated_assets(
            user_id=user_id,
            provider="elevenlabs"
        )

        total_cost = sum(asset.generation_cost or 0 for asset in assets)
        total_chars = sum(len(asset.generation_prompt or "") for asset in assets)

        return {
            "total_narrations": len(assets),
            "total_characters": total_chars,
            "total_cost_cents": total_cost,
            "total_cost_dollars": round(total_cost / 100, 2),
            "provider": "elevenlabs"
        }
