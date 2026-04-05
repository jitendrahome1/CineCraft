"""
AI Provider Factory.
Creates AI provider instances based on configuration.
"""
from typing import Optional, Dict, Any

from app.providers.base.ai_provider import AIProvider
from app.providers.ai.anthropic import AnthropicProvider
from app.providers.ai.openrouter import OpenRouterProvider
from app.providers.ai.openai_provider import OpenAIProvider
from app.core.errors import ConfigurationError
from app.core.logging import get_logger

logger = get_logger(__name__)


class AIProviderFactory:
    """
    Factory for creating AI provider instances.
    Implements dependency injection for swappable providers.
    """

    # Registry of available providers
    _providers: Dict[str, type[AIProvider]] = {
        "anthropic": AnthropicProvider,
        "openrouter": OpenRouterProvider,
        "openai": OpenAIProvider,
        # Future providers can be added here:
        # "google": GoogleProvider,
    }

    @classmethod
    def create(
        cls,
        provider_name: str,
        api_key: str,
        config: Optional[Dict[str, Any]] = None
    ) -> AIProvider:
        """
        Create an AI provider instance.

        Args:
            provider_name: Name of the provider ("anthropic", etc.)
            api_key: API key for the provider
            config: Optional provider configuration

        Returns:
            Initialized AI provider instance

        Raises:
            ConfigurationError: If provider not found or initialization fails
        """
        provider_name = provider_name.lower()

        if provider_name not in cls._providers:
            available = ", ".join(cls._providers.keys())
            raise ConfigurationError(
                f"Unknown AI provider: {provider_name}. "
                f"Available providers: {available}"
            )

        try:
            provider_class = cls._providers[provider_name]
            provider = provider_class(api_key=api_key, config=config)
            logger.info(f"Created AI provider: {provider_name}")
            return provider

        except Exception as e:
            logger.exception(f"Failed to create AI provider {provider_name}: {str(e)}")
            raise ConfigurationError(
                f"Failed to initialize AI provider {provider_name}: {str(e)}"
            )

    @classmethod
    def register_provider(cls, name: str, provider_class: type[AIProvider]):
        """
        Register a custom AI provider.

        Args:
            name: Provider name
            provider_class: Provider class (must inherit from AIProvider)
        """
        if not issubclass(provider_class, AIProvider):
            raise ValueError(
                f"Provider class must inherit from AIProvider, got {provider_class}"
            )

        cls._providers[name.lower()] = provider_class
        logger.info(f"Registered AI provider: {name}")

    @classmethod
    def list_providers(cls) -> list[str]:
        """
        Get list of available provider names.

        Returns:
            List of provider names
        """
        return list(cls._providers.keys())

    @classmethod
    def is_provider_available(cls, provider_name: str) -> bool:
        """
        Check if a provider is available.

        Args:
            provider_name: Provider name

        Returns:
            True if provider is available
        """
        return provider_name.lower() in cls._providers


def get_ai_provider_from_config(
    provider_name: Optional[str] = None,
    api_key: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> AIProvider:
    """
    Get AI provider from configuration.

    Args:
        provider_name: Provider name (defaults to env AI_PROVIDER)
        api_key: API key (defaults to env ANTHROPIC_API_KEY)
        config: Optional configuration

    Returns:
        Initialized AI provider

    Raises:
        ConfigurationError: If configuration is invalid
    """
    from app.core.config import settings

    # Use defaults from settings
    provider_name = provider_name or settings.AI_PROVIDER

    # Get API key based on provider
    if not api_key:
        if provider_name == "anthropic":
            api_key = settings.ANTHROPIC_API_KEY
        elif provider_name == "openrouter":
            api_key = settings.OPENROUTER_API_KEY
            # Build OpenRouter-specific config if not provided
            if not config:
                config = {
                    "story_model": settings.OPENROUTER_STORY_MODEL,
                    "scene_model": settings.OPENROUTER_SCENE_MODEL,
                    "character_model": settings.OPENROUTER_CHARACTER_MODEL,
                    "base_url": settings.OPENROUTER_BASE_URL,
                    "max_tokens": 4096,
                }
        elif provider_name == "openai":
            api_key = settings.OPENAI_API_KEY
            # Build OpenAI-specific config if not provided
            if not config:
                config = {
                    "model": "gpt-4-turbo-preview",
                    "max_tokens": 4096,
                }

    if not api_key:
        raise ConfigurationError(
            f"No API key configured for AI provider: {provider_name}"
        )

    return AIProviderFactory.create(provider_name, api_key, config)
