"""
Celery tasks for AI generation operations.
Handles async story, image, voice, and music generation.
"""
from celery import Task
from typing import Optional

from app.tasks.celery_app import celery_app
from app.db.session import SessionLocal
from app.models.render_job import JobStatus, JobType
from app.repositories.render_job import RenderJobRepository
from app.core.providers import get_provider_manager
from app.providers.storage.factory import get_storage_provider_from_config
from app.services.storage import StorageService
from app.services.story_generation import StoryGenerationService
from app.services.image_generation import ImageGenerationService
from app.services.voice_generation import VoiceGenerationService
from app.services.music_generation import MusicGenerationService
from app.core.logging import get_logger

logger = get_logger(__name__)


class DatabaseTask(Task):
    """Base task class that provides database session."""

    _db = None

    @property
    def db(self):
        """Get database session."""
        if self._db is None:
            self._db = SessionLocal()
        return self._db

    def after_return(self, *args, **kwargs):
        """Close database session after task completion."""
        if self._db is not None:
            self._db.close()
            self._db = None


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.ai_generation.generate_complete_story")
def generate_complete_story(
    self,
    job_id: int,
    project_id: int,
    user_id: int,
    regenerate_scenes: bool = True,
    regenerate_characters: bool = True
):
    """
    Generate complete story with scenes and characters.

    Args:
        job_id: RenderJob ID
        project_id: Project ID
        user_id: User ID
        regenerate_scenes: Whether to regenerate scenes
        regenerate_characters: Whether to regenerate characters
    """
    job_repo = RenderJobRepository(self.db)
    job = job_repo.get(job_id)

    if not job:
        logger.error(f"Job {job_id} not found")
        return

    try:
        # Update job status
        job.start()
        job.update_progress(10, "Initializing AI provider")
        self.db.commit()

        # Get AI provider
        provider_manager = get_provider_manager()
        ai_provider = provider_manager.get_ai_provider()

        # Create story generation service
        story_service = StoryGenerationService(self.db, ai_provider)

        # Generate story
        job.update_progress(30, "Generating story")
        self.db.commit()

        result = story_service.generate_complete_story_sync(
            project_id=project_id,
            user_id=user_id,
            regenerate_scenes=regenerate_scenes,
            regenerate_characters=regenerate_characters
        )

        # Complete job
        job.complete(result_data=result)
        self.db.commit()

        logger.info(f"Completed story generation for job {job_id}")

    except Exception as e:
        logger.exception(f"Story generation failed for job {job_id}")
        job.fail(str(e), {"exception": type(e).__name__})
        self.db.commit()
        raise


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.ai_generation.generate_project_images")
def generate_project_images(
    self,
    job_id: int,
    project_id: int,
    user_id: int,
    width: int = 1024,
    height: int = 1024,
    style: Optional[str] = None
):
    """
    Generate images for all scenes in a project.

    Args:
        job_id: RenderJob ID
        project_id: Project ID
        user_id: User ID
        width: Image width
        height: Image height
        style: Optional image style
    """
    job_repo = RenderJobRepository(self.db)
    job = job_repo.get(job_id)

    if not job:
        logger.error(f"Job {job_id} not found")
        return

    try:
        # Update job status
        job.start()
        job.update_progress(10, "Initializing image provider")
        self.db.commit()

        # Get providers
        provider_manager = get_provider_manager()
        image_provider = provider_manager.get_image_provider()
        storage_provider = get_storage_provider_from_config()

        # Create services
        storage_service = StorageService(self.db, storage_provider)
        image_service = ImageGenerationService(self.db, image_provider, storage_service)

        # Generate images
        job.update_progress(30, "Generating scene images")
        self.db.commit()

        # Use sync version (Celery tasks should be sync)
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        assets = loop.run_until_complete(
            image_service.generate_project_images(
                project_id=project_id,
                user_id=user_id,
                width=width,
                height=height,
                style=style
            )
        )

        loop.close()

        # Complete job
        result = {
            "images_generated": len(assets),
            "asset_ids": [asset.id for asset in assets]
        }
        job.complete(result_data=result)
        self.db.commit()

        logger.info(f"Completed image generation for job {job_id}")

    except Exception as e:
        logger.exception(f"Image generation failed for job {job_id}")
        job.fail(str(e), {"exception": type(e).__name__})
        self.db.commit()
        raise


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.ai_generation.generate_project_voices")
def generate_project_voices(
    self,
    job_id: int,
    project_id: int,
    user_id: int,
    voice_id: Optional[str] = None,
    speed: float = 1.0
):
    """
    Generate voice narrations for all scenes in a project.

    Args:
        job_id: RenderJob ID
        project_id: Project ID
        user_id: User ID
        voice_id: Optional voice ID
        speed: Speech speed
    """
    job_repo = RenderJobRepository(self.db)
    job = job_repo.get(job_id)

    if not job:
        logger.error(f"Job {job_id} not found")
        return

    try:
        # Update job status
        job.start()
        job.update_progress(10, "Initializing voice provider")
        self.db.commit()

        # Get providers
        provider_manager = get_provider_manager()
        voice_provider = provider_manager.get_voice_provider()
        storage_provider = get_storage_provider_from_config()

        # Create services
        storage_service = StorageService(self.db, storage_provider)
        voice_service = VoiceGenerationService(self.db, voice_provider, storage_service)

        # Generate narrations
        job.update_progress(30, "Generating voice narrations")
        self.db.commit()

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        assets = loop.run_until_complete(
            voice_service.generate_project_narrations(
                project_id=project_id,
                user_id=user_id,
                voice_id=voice_id,
                speed=speed
            )
        )

        loop.close()

        # Complete job
        result = {
            "narrations_generated": len(assets),
            "asset_ids": [asset.id for asset in assets]
        }
        job.complete(result_data=result)
        self.db.commit()

        logger.info(f"Completed voice generation for job {job_id}")

    except Exception as e:
        logger.exception(f"Voice generation failed for job {job_id}")
        job.fail(str(e), {"exception": type(e).__name__})
        self.db.commit()
        raise


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.ai_generation.generate_project_music")
def generate_project_music(
    self,
    job_id: int,
    project_id: int,
    user_id: int,
    duration: int = 60,
    mood: Optional[str] = None,
    genre: Optional[str] = None,
    prompt: Optional[str] = None
):
    """
    Generate background music for a project.

    Args:
        job_id: RenderJob ID
        project_id: Project ID
        user_id: User ID
        duration: Music duration in seconds
        mood: Optional mood
        genre: Optional genre
        prompt: Optional custom prompt
    """
    job_repo = RenderJobRepository(self.db)
    job = job_repo.get(job_id)

    if not job:
        logger.error(f"Job {job_id} not found")
        return

    try:
        # Update job status
        job.start()
        job.update_progress(10, "Initializing music provider")
        self.db.commit()

        # Get providers
        provider_manager = get_provider_manager()
        music_provider = provider_manager.get_music_provider()
        storage_provider = get_storage_provider_from_config()

        # Create services
        storage_service = StorageService(self.db, storage_provider)
        music_service = MusicGenerationService(self.db, music_provider, storage_service)

        # Generate music
        job.update_progress(30, "Generating background music")
        self.db.commit()

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        asset = loop.run_until_complete(
            music_service.generate_project_music(
                project_id=project_id,
                user_id=user_id,
                duration=duration,
                mood=mood,
                genre=genre,
                prompt=prompt
            )
        )

        loop.close()

        # Complete job
        result = {
            "music_generated": True,
            "asset_id": asset.id,
            "duration": asset.duration
        }
        job.complete(result_data=result)
        self.db.commit()

        logger.info(f"Completed music generation for job {job_id}")

    except Exception as e:
        logger.exception(f"Music generation failed for job {job_id}")
        job.fail(str(e), {"exception": type(e).__name__})
        self.db.commit()
        raise


@celery_app.task(bind=True, base=DatabaseTask, name="app.tasks.ai_generation.cleanup_expired_assets")
def cleanup_expired_assets(self):
    """Periodic task to clean up expired media assets."""
    try:
        logger.info("Starting expired assets cleanup")

        storage_provider = get_storage_provider_from_config()
        storage_service = StorageService(self.db, storage_provider)

        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        deleted_count = loop.run_until_complete(
            storage_service.delete_expired_assets()
        )

        loop.close()

        logger.info(f"Cleaned up {deleted_count} expired assets")
        return {"deleted_count": deleted_count}

    except Exception as e:
        logger.exception("Expired assets cleanup failed")
        raise
