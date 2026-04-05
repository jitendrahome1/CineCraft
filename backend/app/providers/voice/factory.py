"""
Voice Provider Factory.
Creates voice provider instances based on configuration.
"""
from typing import Optional, Dict, Any

from app.providers.base.voice_provider import VoiceProvider
from app.providers.voice.gtts_provider import GTTSProvider
from app.core.errors import ConfigurationError
from app.core.logging import get_logger

logger = get_logger(__name__)


class VoiceProviderFactory:
    """Factory for creating voice provider instances."""

    _providers: Dict[str, type[VoiceProvider]] = {
        "gtts": GTTSProvider,
        # ElevenLabs registered dynamically when available
    }

    @classmethod
    def _ensure_elevenlabs(cls):
        """Register ElevenLabs provider if not already registered."""
        if "elevenlabs" not in cls._providers:
            try:
                from app.providers.voice.elevenlabs import ElevenLabsProvider
                cls._providers["elevenlabs"] = ElevenLabsProvider
            except ImportError:
                from app.providers.voice.elevenlabs_stub import ElevenLabsProvider
                cls._providers["elevenlabs"] = ElevenLabsProvider

    @classmethod
    def create(
        cls,
        provider_name: str,
        api_key: str,
        config: Optional[Dict[str, Any]] = None
    ) -> VoiceProvider:
        """
        Create a voice provider instance.

        Args:
            provider_name: Name of the provider
            api_key: API key for the provider
            config: Optional provider configuration

        Returns:
            Initialized voice provider instance

        Raises:
            ConfigurationError: If provider not found
        """
        cls._ensure_elevenlabs()
        provider_name = provider_name.lower()

        if provider_name not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ConfigurationError(
                f"Unknown voice provider: {provider_name}. "
                f"Available: {available}"
            )

        try:
            provider_class = cls._providers[provider_name]
            provider = provider_class(api_key=api_key, config=config)
            logger.info(f"Created voice provider: {provider_name}")
            return provider

        except Exception as e:
            logger.exception(f"Failed to create voice provider {provider_name}")
            raise ConfigurationError(
                f"Failed to initialize voice provider: {str(e)}"
            )

    @classmethod
    def register_provider(cls, name: str, provider_class: type[VoiceProvider]):
        """Register a custom voice provider."""
        if not issubclass(provider_class, VoiceProvider):
            raise ValueError("Provider must inherit from VoiceProvider")

        cls._providers[name.lower()] = provider_class
        logger.info(f"Registered voice provider: {name}")

    @classmethod
    def list_providers(cls) -> list[str]:
        """Get list of available provider names."""
        cls._ensure_elevenlabs()
        return list(cls._providers.keys())


def get_voice_provider_from_config(
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> VoiceProvider:
    """
    Get voice provider from configuration.
    Falls back to gTTS (free) if no API key is configured.
    """
    from app.core.config import settings

    provider_name = provider_name or settings.VOICE_PROVIDER
    api_key = api_key or settings.VOICE_PROVIDER_API_KEY

    # If ElevenLabs is requested but no API key, fall back to gTTS
    if not api_key and provider_name == "elevenlabs":
        logger.warning("No ElevenLabs API key configured, falling back to gTTS (free)")
        provider_name = "gtts"
        api_key = "free"

    # gTTS doesn't need an API key
    if provider_name == "gtts":
        api_key = api_key or "free"

    if not api_key:
        raise ConfigurationError(
            f"No API key configured for voice provider: {provider_name}"
        )

    return VoiceProviderFactory.create(provider_name, api_key, config)
