"""
Factory for creating storage provider instances.
Implements Factory Pattern for storage provider selection.
"""
from typing import Dict, Type, Any, Optional

from app.providers.base.storage_provider import StorageProvider
from app.providers.storage.local import LocalStorageProvider
from app.providers.storage.s3 import S3StorageProvider
from app.core.logging import get_logger

logger = get_logger(__name__)


class StorageProviderFactory:
    """
    Factory for creating storage provider instances.

    Supports provider registration and configuration-based instantiation.
    """

    _providers: Dict[str, Type[StorageProvider]] = {
        "local": LocalStorageProvider,
        "s3": S3StorageProvider,
    }

    @classmethod
    def create(
        cls,
        provider_name: str,
        config: Dict[str, Any]
    ) -> StorageProvider:
        """
        Create a storage provider instance.

        Args:
            provider_name: Name of the provider ('local', 's3')
            config: Provider configuration dictionary

        Returns:
            StorageProvider instance

        Raises:
            ValueError: If provider name is unknown
            TypeError: If configuration is invalid
        """
        provider_name = provider_name.lower()

        if provider_name not in cls._providers:
            raise ValueError(
                f"Unknown storage provider: {provider_name}. "
                f"Available providers: {', '.join(cls._providers.keys())}"
            )

        provider_class = cls._providers[provider_name]
        logger.info(f"Creating storage provider: {provider_name}")

        try:
            if provider_name == "local":
                return cls._create_local_provider(config)
            elif provider_name == "s3":
                return cls._create_s3_provider(config)
            else:
                # Generic instantiation
                return provider_class(**config)

        except Exception as e:
            logger.error(f"Failed to create storage provider {provider_name}: {e}")
            raise

    @classmethod
    def _create_local_provider(cls, config: Dict[str, Any]) -> LocalStorageProvider:
        """
        Create local storage provider.

        Args:
            config: Configuration dictionary
                - base_path: Required, local directory path
                - base_url: Optional, base URL for file access

        Returns:
            LocalStorageProvider instance

        Raises:
            ValueError: If required config is missing
        """
        base_path = config.get("base_path")
        if not base_path:
            raise ValueError("Local storage provider requires 'base_path' in config")

        base_url = config.get("base_url")

        return LocalStorageProvider(
            base_path=base_path,
            base_url=base_url
        )

    @classmethod
    def _create_s3_provider(cls, config: Dict[str, Any]) -> S3StorageProvider:
        """
        Create S3 storage provider.

        Args:
            config: Configuration dictionary
                - bucket: Required, S3 bucket name
                - region: Optional, AWS region (default: us-east-1)
                - access_key: Optional, AWS access key ID
                - secret_key: Optional, AWS secret access key
                - endpoint_url: Optional, custom endpoint URL

        Returns:
            S3StorageProvider instance (stub)

        Raises:
            ValueError: If required config is missing
        """
        bucket = config.get("bucket")
        if not bucket:
            raise ValueError("S3 storage provider requires 'bucket' in config")

        region = config.get("region", "us-east-1")
        access_key = config.get("access_key")
        secret_key = config.get("secret_key")
        endpoint_url = config.get("endpoint_url")

        return S3StorageProvider(
            bucket=bucket,
            region=region,
            access_key=access_key,
            secret_key=secret_key,
            endpoint_url=endpoint_url
        )

    @classmethod
    def register_provider(
        cls,
        name: str,
        provider_class: Type[StorageProvider]
    ):
        """
        Register a custom storage provider.

        Args:
            name: Provider name
            provider_class: Provider class (must inherit from StorageProvider)

        Raises:
            TypeError: If provider_class doesn't inherit from StorageProvider
        """
        if not issubclass(provider_class, StorageProvider):
            raise TypeError(
                f"Provider class must inherit from StorageProvider, "
                f"got {provider_class.__name__}"
            )

        cls._providers[name.lower()] = provider_class
        logger.info(f"Registered storage provider: {name}")

    @classmethod
    def get_available_providers(cls) -> list[str]:
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


def get_storage_provider_from_config(
    provider_name: Optional[str] = None,
    config: Optional[Dict[str, Any]] = None
) -> StorageProvider:
    """
    Get storage provider from configuration.

    Convenience function that reads from environment if not provided.

    Args:
        provider_name: Optional provider name (defaults to STORAGE_PROVIDER env var)
        config: Optional provider config (defaults to config from settings)

    Returns:
        StorageProvider instance

    Raises:
        ValueError: If configuration is invalid
    """
    from app.core.config import settings

    # Use provided values or fall back to settings
    provider_name = provider_name or settings.STORAGE_PROVIDER

    if config is None:
        # Build config from settings
        if provider_name.lower() == "local":
            config = {
                "base_path": settings.LOCAL_STORAGE_PATH,
                "base_url": f"{settings.API_BASE_URL}/storage"
            }
        elif provider_name.lower() == "s3":
            config = {
                "bucket": settings.S3_BUCKET,
                "region": settings.S3_REGION,
                "access_key": settings.AWS_ACCESS_KEY_ID,
                "secret_key": settings.AWS_SECRET_ACCESS_KEY,
                "endpoint_url": settings.S3_ENDPOINT_URL
            }
        else:
            raise ValueError(f"Unknown storage provider: {provider_name}")

    return StorageProviderFactory.create(provider_name, config)
