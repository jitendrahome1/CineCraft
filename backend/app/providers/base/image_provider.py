"""
Base abstract class for image generation providers.
"""
from abc import ABC, abstractmethod
from typing import Optional


class ImageProvider(ABC):
    """
    Abstract base class for image generation providers.
    All image providers must implement these methods.
    """

    def __init__(self, api_key: str, config: Optional[dict] = None):
        """
        Initialize image provider.

        Args:
            api_key: API key for the provider
            config: Optional configuration dict
        """
        self.api_key = api_key
        self.config = config or {}

    @abstractmethod
    async def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        style: Optional[str] = None
    ) -> bytes:
        """
        Generate image from text prompt.

        Args:
            prompt: Text description of image
            width: Image width in pixels
            height: Image height in pixels
            style: Optional style hint (e.g., "cinematic", "artistic")

        Returns:
            Image data as bytes
        """
        pass

    @abstractmethod
    async def get_supported_sizes(self) -> list[tuple[int, int]]:
        """
        Get list of supported image sizes.

        Returns:
            List of (width, height) tuples
        """
        pass
