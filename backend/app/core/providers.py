"""
Provider configuration and management.
Centralized system for managing all AI providers.
"""
from typing import Optional, Dict, Any
from dataclasses import dataclass

from app.providers.base.ai_provider import AIProvider
from app.providers.base.image_provider import ImageProvider
from app.providers.base.voice_provider import VoiceProvider
from app.providers.base.music_provider import MusicProvider
from app.providers.ai.factory import get_ai_provider_from_config
from app.providers.image.factory import get_image_provider_from_config
from app.providers.voice.factory import get_voice_provider_from_config
from app.providers.music.factory import get_music_provider_from_config
from app.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ProviderConfig:
    """Configuration for a provider."""
    name: str
    api_key: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    enabled: bool = True


class ProviderManager:
    """
    Manages all provider instances.
    Implements lazy loading and caching of providers.
    """

    def __init__(self):
        self._ai_provider: Optional[AIProvider] = None
        self._image_provider: Optional[ImageProvider] = None
        self._voice_provider: Optional[VoiceProvider] = None
        self._music_provider: Optional[MusicProvider] = None

    def get_ai_provider(
        self,
        provider_name: Optional[str] = None,
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        force_new: bool = False
    ) -> AIProvider:
        """
        Get AI provider instance.

        Args:
            provider_name: Provider name (defaults to config)
            api_key: API key (defaults to config)
            config: Optional configuration
            force_new: Force create new instance

        Returns:
            AI provider instance
        """
        if self._ai_provider is None or force_new:
            self._ai_provider = get_ai_provider_from_config(
                provider_name, api_key, config
            )
        return self._ai_provider

    def get_image_provider(
        self,
        provider_name: Optional[str] = None,
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        force_new: bool = False
    ) -> ImageProvider:
        """
        Get image provider instance.

        Args:
            provider_name: Provider name (defaults to config)
            api_key: API key (defaults to config)
            config: Optional configuration
            force_new: Force create new instance

        Returns:
            Image provider instance
        """
        if self._image_provider is None or force_new:
            self._image_provider = get_image_provider_from_config(
                provider_name, api_key, config
            )
        return self._image_provider

    def get_voice_provider(
        self,
        provider_name: Optional[str] = None,
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        force_new: bool = False
    ) -> VoiceProvider:
        """
        Get voice provider instance.

        Args:
            provider_name: Provider name (defaults to config)
            api_key: API key (defaults to config)
            config: Optional configuration
            force_new: Force create new instance

        Returns:
            Voice provider instance
        """
        if self._voice_provider is None or force_new:
            self._voice_provider = get_voice_provider_from_config(
                provider_name, api_key, config
            )
        return self._voice_provider

    def get_music_provider(
        self,
        provider_name: Optional[str] = None,
        api_key: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
        force_new: bool = False
    ) -> MusicProvider:
        """
        Get music provider instance.

        Args:
            provider_name: Provider name (defaults to config)
            api_key: API key (defaults to config)
            config: Optional configuration
            force_new: Force create new instance

        Returns:
            Music provider instance
        """
        if self._music_provider is None or force_new:
            self._music_provider = get_music_provider_from_config(
                provider_name, api_key, config
            )
        return self._music_provider

    async def test_all_connections(self) -> Dict[str, bool]:
        """
        Test connections to all providers.

        Returns:
            Dict mapping provider type to connection status
        """
        results = {}

        # Test AI provider
        try:
            ai_provider = self.get_ai_provider()
            if hasattr(ai_provider, 'test_connection'):
                results['ai'] = await ai_provider.test_connection()
            else:
                results['ai'] = True  # Assume working if no test method
        except Exception as e:
            logger.error(f"AI provider test failed: {str(e)}")
            results['ai'] = False

        # Test Image provider
        try:
            image_provider = self.get_image_provider()
            if hasattr(image_provider, 'test_connection'):
                results['image'] = await image_provider.test_connection()
            else:
                results['image'] = True
        except Exception as e:
            logger.error(f"Image provider test failed: {str(e)}")
            results['image'] = False

        # Test Voice provider
        try:
            voice_provider = self.get_voice_provider()
            if hasattr(voice_provider, 'test_connection'):
                results['voice'] = await voice_provider.test_connection()
            else:
                results['voice'] = True
        except Exception as e:
            logger.error(f"Voice provider test failed: {str(e)}")
            results['voice'] = False

        # Test Music provider
        try:
            music_provider = self.get_music_provider()
            if hasattr(music_provider, 'test_connection'):
                results['music'] = await music_provider.test_connection()
            else:
                results['music'] = True
        except Exception as e:
            logger.error(f"Music provider test failed: {str(e)}")
            results['music'] = False

        return results

    def get_provider_info(self) -> Dict[str, Dict[str, Any]]:
        """
        Get information about configured providers.

        Returns:
            Dict with provider information
        """
        from app.core.config import settings

        return {
            "ai": {
                "provider": settings.AI_PROVIDER,
                "configured": bool(settings.ANTHROPIC_API_KEY)
            },
            "image": {
                "provider": settings.IMAGE_PROVIDER,
                "configured": bool(settings.IMAGE_PROVIDER_API_KEY)
            },
            "voice": {
                "provider": settings.VOICE_PROVIDER,
                "configured": bool(settings.VOICE_PROVIDER_API_KEY)
            },
            "music": {
                "provider": settings.MUSIC_PROVIDER,
                "configured": bool(settings.MUSIC_PROVIDER_API_KEY)
            }
        }


# Global provider manager instance
_provider_manager: Optional[ProviderManager] = None


def get_provider_manager() -> ProviderManager:
    """
    Get global provider manager instance.

    Returns:
        Provider manager singleton
    """
    global _provider_manager
    if _provider_manager is None:
        _provider_manager = ProviderManager()
    return _provider_manager
