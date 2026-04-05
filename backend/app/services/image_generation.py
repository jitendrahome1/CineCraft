"""
Image generation service for CineCraft.
Generates images for scenes using AI providers and stores them.
"""
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session

from app.providers.base.image_provider import ImageProvider
from app.services.storage import StorageService
from app.repositories.project import ProjectRepository
from app.repositories.scene import SceneRepository
from app.models.media_asset import MediaAsset, MediaType
from app.models.project import ProjectStatus
from app.core.errors import ValidationError, AIProviderError
from app.core.logging import get_logger

logger = get_logger(__name__)


class ImageGenerationService:
    """
    Service for generating scene images using AI providers.

    Coordinates image generation, storage, and database updates.
    """

    def __init__(
        self,
        db: Session,
        image_provider: ImageProvider,
        storage_service: StorageService
    ):
        """
        Initialize image generation service.

        Args:
            db: Database session
            image_provider: Image generation provider
            storage_service: Storage service for saving images
        """
        self.db = db
        self.image_provider = image_provider
        self.storage_service = storage_service
        self.project_repo = ProjectRepository(db)
        self.scene_repo = SceneRepository(db)

    async def generate_scene_image(
        self,
        scene_id: int,
        user_id: int,
        width: int = 1024,
        height: int = 1024,
        style: Optional[str] = None
    ) -> MediaAsset:
        """
        Generate image for a single scene.

        Args:
            scene_id: Scene ID
            user_id: User ID
            width: Image width
            height: Image height
            style: Optional style hint

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

        # Get visual description from scene
        prompt = scene.visual_description

        if not prompt:
            raise ValidationError(f"Scene {scene_id} has no visual description")

        logger.info(f"Generating image for scene {scene_id}")

        try:
            # Generate image
            image_bytes = await self.image_provider.generate_image(
                prompt=prompt,
                width=width,
                height=height,
                style=style
            )

            # Determine filename
            filename = f"scene_{scene.sequence_number}_image.png"

            # Get cost estimate
            provider_name = self.image_provider.__class__.__name__.replace("Provider", "").lower()
            cost = self.image_provider.get_estimated_cost(width, height)

            # Save to storage
            asset = await self.storage_service.save_generated_asset(
                file_data=image_bytes,
                filename=filename,
                user_id=user_id,
                project_id=scene.project_id,
                scene_id=scene_id,
                media_type=MediaType.IMAGE,
                generation_provider=provider_name,
                generation_prompt=prompt,
                generation_cost=cost,
                metadata={
                    "width": width,
                    "height": height,
                    "style": style or "default"
                }
            )

            # Update asset dimensions
            asset.width = width
            asset.height = height
            self.db.commit()

            logger.info(f"Successfully generated image for scene {scene_id} (asset {asset.id})")
            return asset

        except AIProviderError as e:
            logger.error(f"Image generation failed for scene {scene_id}: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error generating image for scene {scene_id}")
            raise AIProviderError(f"Image generation failed: {str(e)}")

    async def generate_project_images(
        self,
        project_id: int,
        user_id: int,
        width: int = 1024,
        height: int = 1024,
        style: Optional[str] = None
    ) -> List[MediaAsset]:
        """
        Generate images for all scenes in a project.

        Args:
            project_id: Project ID
            user_id: User ID
            width: Image width
            height: Image height
            style: Optional style hint

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

        logger.info(f"Generating images for {len(scenes)} scenes in project {project_id}")

        # Update project status
        self.project_repo.update_status(project_id, ProjectStatus.GENERATING)

        assets = []
        failed_scenes = []

        try:
            for scene in scenes:
                try:
                    asset = await self.generate_scene_image(
                        scene_id=scene.id,
                        user_id=user_id,
                        width=width,
                        height=height,
                        style=style
                    )
                    assets.append(asset)

                except Exception as e:
                    logger.error(f"Failed to generate image for scene {scene.id}: {e}")
                    failed_scenes.append(scene.id)

            if failed_scenes and not assets:
                # All scenes failed
                self.project_repo.update_status(project_id, ProjectStatus.FAILED)
                raise AIProviderError(f"Failed to generate images for all scenes")

            elif failed_scenes:
                # Some scenes failed
                logger.warning(f"Failed to generate images for scenes: {failed_scenes}")

            # Update project status
            self.project_repo.update_status(project_id, ProjectStatus.READY)

            logger.info(
                f"Successfully generated {len(assets)} images for project {project_id} "
                f"({len(failed_scenes)} failed)"
            )

            return assets

        except Exception as e:
            self.project_repo.update_status(project_id, ProjectStatus.FAILED)
            raise

    async def regenerate_scene_image(
        self,
        scene_id: int,
        user_id: int,
        width: int = 1024,
        height: int = 1024,
        style: Optional[str] = None
    ) -> MediaAsset:
        """
        Regenerate image for a scene (deletes old image).

        Args:
            scene_id: Scene ID
            user_id: User ID
            width: Image width
            height: Image height
            style: Optional style hint

        Returns:
            Newly created MediaAsset

        Raises:
            ValidationError: If scene not found or unauthorized
            AIProviderError: If generation fails
        """
        # Delete existing images for this scene
        old_assets = self.storage_service.repository.get_by_scene(
            scene_id=scene_id,
            media_type=MediaType.IMAGE
        )

        for asset in old_assets:
            try:
                await self.storage_service.delete_asset(
                    asset_id=asset.id,
                    user_id=user_id
                )
            except Exception as e:
                logger.warning(f"Failed to delete old image {asset.id}: {e}")

        # Generate new image
        return await self.generate_scene_image(
            scene_id=scene_id,
            user_id=user_id,
            width=width,
            height=height,
            style=style
        )

    def get_scene_images(self, scene_id: int) -> List[MediaAsset]:
        """
        Get all images for a scene.

        Args:
            scene_id: Scene ID

        Returns:
            List of image assets
        """
        return self.storage_service.repository.get_by_scene(
            scene_id=scene_id,
            media_type=MediaType.IMAGE
        )

    def get_project_images(self, project_id: int) -> List[MediaAsset]:
        """
        Get all images for a project.

        Args:
            project_id: Project ID

        Returns:
            List of image assets
        """
        return self.storage_service.repository.get_by_project(
            project_id=project_id,
            media_type=MediaType.IMAGE
        )

    def get_generation_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get image generation statistics for a user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with statistics
        """
        assets = self.storage_service.repository.get_generated_assets(
            user_id=user_id,
            provider="dalle"
        )

        total_cost = sum(asset.generation_cost or 0 for asset in assets)

        return {
            "total_images": len(assets),
            "total_cost_cents": total_cost,
            "total_cost_dollars": round(total_cost / 100, 2),
            "provider": "dalle"
        }
