"""
AI Orchestration Service.
Coordinates all AI generation operations across different providers.
"""
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

from app.providers.base.ai_provider import AIProvider
from app.providers.base.image_provider import ImageProvider
from app.providers.base.voice_provider import VoiceProvider
from app.providers.base.music_provider import MusicProvider
from app.services.story_generation import StoryGenerationService
from app.core.logging import get_logger

logger = get_logger(__name__)


class AIOrchestrationService:
    """
    Orchestrates all AI operations.
    Central coordination point for story, image, voice, and music generation.
    """

    def __init__(
        self,
        db: Session,
        ai_provider: AIProvider,
        image_provider: Optional[ImageProvider] = None,
        voice_provider: Optional[VoiceProvider] = None,
        music_provider: Optional[MusicProvider] = None
    ):
        """
        Initialize AI orchestration service.

        Args:
            db: Database session
            ai_provider: AI provider for story/text generation
            image_provider: Optional image provider
            voice_provider: Optional voice provider
            music_provider: Optional music provider
        """
        self.db = db
        self.ai_provider = ai_provider
        self.image_provider = image_provider
        self.voice_provider = voice_provider
        self.music_provider = music_provider

        # Initialize sub-services
        self.story_service = StoryGenerationService(db, ai_provider)

    async def generate_project_content(
        self,
        project_id: int,
        user_id: int,
        include_story: bool = True,
        include_scenes: bool = True,
        include_characters: bool = True,
        include_images: bool = False,
        include_audio: bool = False,
        include_music: bool = False
    ) -> Dict[str, Any]:
        """
        Generate all content for a project.

        Args:
            project_id: Project ID
            user_id: User ID
            include_story: Generate story
            include_scenes: Generate scenes
            include_characters: Extract characters
            include_images: Generate scene images (requires image_provider)
            include_audio: Generate scene audio (requires voice_provider)
            include_music: Generate background music (requires music_provider)

        Returns:
            Dict with all generated content

        Raises:
            ValidationError: If project not found
            AIProviderError: If generation fails
        """
        result = {
            "project_id": project_id,
            "generated": {}
        }

        # Step 1: Generate story with scenes and characters
        if include_story:
            logger.info(f"Generating story content for project {project_id}")

            story_result = await self.story_service.generate_complete_story(
                project_id=project_id,
                user_id=user_id,
                regenerate_scenes=include_scenes,
                regenerate_characters=include_characters
            )

            result["generated"]["story"] = story_result["story"]
            result["generated"]["scenes"] = story_result["scenes"]
            result["generated"]["characters"] = story_result["characters"]

        # Step 2: Generate images (Phase 7 - not implemented yet)
        if include_images:
            if not self.image_provider:
                logger.warning("Image generation requested but no provider configured")
                result["generated"]["images"] = {
                    "status": "skipped",
                    "reason": "Image provider not configured"
                }
            else:
                # Will be implemented in Phase 7
                logger.warning("Image generation not yet implemented")
                result["generated"]["images"] = {
                    "status": "skipped",
                    "reason": "Not yet implemented"
                }

        # Step 3: Generate audio (Phase 7 - not implemented yet)
        if include_audio:
            if not self.voice_provider:
                logger.warning("Audio generation requested but no provider configured")
                result["generated"]["audio"] = {
                    "status": "skipped",
                    "reason": "Voice provider not configured"
                }
            else:
                # Will be implemented in Phase 7
                logger.warning("Audio generation not yet implemented")
                result["generated"]["audio"] = {
                    "status": "skipped",
                    "reason": "Not yet implemented"
                }

        # Step 4: Generate music (Phase 7 - not implemented yet)
        if include_music:
            if not self.music_provider:
                logger.warning("Music generation requested but no provider configured")
                result["generated"]["music"] = {
                    "status": "skipped",
                    "reason": "Music provider not configured"
                }
            else:
                # Will be implemented in Phase 7
                logger.warning("Music generation not yet implemented")
                result["generated"]["music"] = {
                    "status": "skipped",
                    "reason": "Not yet implemented"
                }

        return result

    async def test_providers(self) -> Dict[str, bool]:
        """
        Test all configured providers.

        Returns:
            Dict mapping provider type to connection status
        """
        results = {}

        # Test AI provider
        if self.ai_provider and hasattr(self.ai_provider, 'test_connection'):
            try:
                results['ai'] = await self.ai_provider.test_connection()
            except Exception as e:
                logger.error(f"AI provider test failed: {str(e)}")
                results['ai'] = False
        else:
            results['ai'] = self.ai_provider is not None

        # Test Image provider
        if self.image_provider and hasattr(self.image_provider, 'test_connection'):
            try:
                results['image'] = await self.image_provider.test_connection()
            except Exception as e:
                logger.error(f"Image provider test failed: {str(e)}")
                results['image'] = False
        else:
            results['image'] = self.image_provider is not None

        # Test Voice provider
        if self.voice_provider and hasattr(self.voice_provider, 'test_connection'):
            try:
                results['voice'] = await self.voice_provider.test_connection()
            except Exception as e:
                logger.error(f"Voice provider test failed: {str(e)}")
                results['voice'] = False
        else:
            results['voice'] = self.voice_provider is not None

        # Test Music provider
        if self.music_provider and hasattr(self.music_provider, 'test_connection'):
            try:
                results['music'] = await self.music_provider.test_connection()
            except Exception as e:
                logger.error(f"Music provider test failed: {str(e)}")
                results['music'] = False
        else:
            results['music'] = self.music_provider is not None

        return results

    def get_provider_info(self) -> Dict[str, Any]:
        """
        Get information about configured providers.

        Returns:
            Dict with provider information
        """
        return {
            "ai": {
                "configured": self.ai_provider is not None,
                "type": self.ai_provider.__class__.__name__ if self.ai_provider else None
            },
            "image": {
                "configured": self.image_provider is not None,
                "type": self.image_provider.__class__.__name__ if self.image_provider else None
            },
            "voice": {
                "configured": self.voice_provider is not None,
                "type": self.voice_provider.__class__.__name__ if self.voice_provider else None
            },
            "music": {
                "configured": self.music_provider is not None,
                "type": self.music_provider.__class__.__name__ if self.music_provider else None
            }
        }
