"""
Music Provider Factory.
Creates music provider instances based on configuration.
"""
from typing import Optional, Dict, Any

from app.providers.base.music_provider import MusicProvider
from app.providers.music.suno_stub import SunoProvider
from app.core.errors import ConfigurationError
from app.core.logging import get_logger

logger = get_logger(__name__)


class MusicProviderFactory:
    """Factory for creating music provider instances."""

    _providers: Dict[str, type[MusicProvider]] = {
        "suno": SunoProvider,
        # Future providers:
        # "mubert": MubertProvider,
        # "aiva": AivaProvider,
    }

    @classmethod
    def create(
        cls,
        provider_name: str,
        api_key: str,
        config: Optional[Dict[str, Any]] = None
    ) -> MusicProvider:
        """
        Create a music provider instance.

        Args:
            provider_name: Name of the provider
            api_key: API key for the provider
            config: Optional provider configuration

        Returns:
            Initialized music provider instance

        Raises:
            ConfigurationError: If provider not found
        """
        provider_name = provider_name.lower()

        if provider_name not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ConfigurationError(
                f"Unknown music provider: {provider_name}. "
                f"Available: {available}"
            )

        try:
            provider_class = cls._providers[provider_name]
            provider = provider_class(api_key=api_key, config=config)
            logger.info(f"Created music provider: {provider_name}")
            return provider

        except Exception as e:
            logger.exception(f"Failed to create music provider {provider_name}")
            raise ConfigurationError(
                f"Failed to initialize music provider: {str(e)}"
            )

    @classmethod
    def register_provider(cls, name: str, provider_class: type[MusicProvider]):
        """Register a custom music provider."""
        if not issubclass(provider_class, MusicProvider):
            raise ValueError("Provider must inherit from MusicProvider")

        cls._providers[name.lower()] = provider_class
        logger.info(f"Registered music provider: {name}")

    @classmethod
    def list_providers(cls) -> list[str]:
        """Get list of available provider names."""
        return list(cls._providers.keys())


def get_music_provider_from_config(
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> MusicProvider:
    """Get music provider from configuration."""
    from app.core.config import settings

    provider_name = provider_name or settings.MUSIC_PROVIDER
    api_key = api_key or settings.MUSIC_PROVIDER_API_KEY

    if not api_key:
        raise ConfigurationError(
            f"No API key configured for music provider: {provider_name}"
        )

    return MusicProviderFactory.create(provider_name, api_key, config)
