"""
Image Provider Factory.
Creates image provider instances based on configuration and APP_MODE.
"""
from typing import Optional, Dict, Any

from app.providers.base.image_provider import ImageProvider
from app.providers.image.dalle import DallEProvider
from app.providers.image.gemini import GeminiImageProvider
from app.providers.image.unsplash import UnsplashImageProvider
from app.providers.image.placeholder import PlaceholderImageProvider
from app.core.errors import ConfigurationError
from app.core.logging import get_logger

logger = get_logger(__name__)


class ImageProviderFactory:
    """Factory for creating image provider instances."""

    _providers: Dict[str, type[ImageProvider]] = {
        "dalle": DallEProvider,
        "gemini": GeminiImageProvider,
        "unsplash": UnsplashImageProvider,
        "placeholder": PlaceholderImageProvider,
    }

    @classmethod
    def create(
        cls,
        provider_name: str,
        api_key: str,
        config: Optional[Dict[str, Any]] = None
    ) -> ImageProvider:
        """Create an image provider instance."""
        provider_name = provider_name.lower()

        if provider_name not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ConfigurationError(
                f"Unknown image provider: {provider_name}. "
                f"Available: {available}"
            )

        try:
            provider_class = cls._providers[provider_name]
            provider = provider_class(api_key=api_key, config=config)
            logger.info(f"Created image provider: {provider_name}")
            return provider

        except Exception as e:
            logger.exception(f"Failed to create image provider {provider_name}")
            raise ConfigurationError(
                f"Failed to initialize image provider: {str(e)}"
            )

    @classmethod
    def register_provider(cls, name: str, provider_class: type[ImageProvider]):
        """Register a custom image provider."""
        if not issubclass(provider_class, ImageProvider):
            raise ValueError("Provider must inherit from ImageProvider")
        cls._providers[name.lower()] = provider_class
        logger.info(f"Registered image provider: {name}")

    @classmethod
    def list_providers(cls) -> list[str]:
        """Get list of available provider names."""
        return list(cls._providers.keys())


def get_image_provider_from_config(
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> ImageProvider:
    """Get image provider from configuration."""
    from app.core.config import settings

    provider_name = provider_name or settings.IMAGE_PROVIDER

    # Placeholder and Unsplash don't need an API key
    if provider_name == "unsplash":
        return ImageProviderFactory.create(provider_name, "free", config)

    if provider_name == "placeholder":
        return ImageProviderFactory.create(provider_name, "placeholder", config)

    # Resolve API key based on provider
    if not api_key:
        if provider_name == "gemini":
            api_key = settings.GEMINI_API_KEY
        elif provider_name == "dalle":
            api_key = settings.OPENAI_API_KEY or settings.IMAGE_PROVIDER_API_KEY
        else:
            api_key = settings.IMAGE_PROVIDER_API_KEY

    if not api_key:
        raise ConfigurationError(
            f"No API key configured for image provider: {provider_name}"
        )

    return ImageProviderFactory.create(provider_name, api_key, config)


def is_testing_mode() -> bool:
    """Check if the application is in testing mode."""
    from app.core.config import settings
    return settings.APP_MODE.lower() == "testing"


def get_testing_real_image_limit() -> int:
    """Get the number of scenes that should get real images in testing mode."""
    from app.core.config import settings
    return settings.TESTING_REAL_IMAGE_LIMIT
