"""
DALL-E Image Provider Stub.
Placeholder implementation for future DALL-E integration.
"""
from typing import Optional

from app.providers.base.image_provider import ImageProvider
from app.core.logging import get_logger
from app.core.errors import AIProviderError

logger = get_logger(__name__)


class DallEProvider(ImageProvider):
    """
    Stub implementation for DALL-E image generation.
    This is a placeholder - actual implementation will be added in Phase 7.
    """

    def __init__(self, api_key: str, config: Optional[dict] = None):
        super().__init__(api_key, config)
        logger.warning("DallEProvider is a stub implementation")

    async def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        style: Optional[str] = None
    ) -> bytes:
        """
        Generate image from text prompt.

        NOTE: This is a stub implementation.

        Args:
            prompt: Text description of image
            width: Image width in pixels
            height: Image height in pixels
            style: Optional style hint

        Returns:
            Image data as bytes

        Raises:
            NotImplementedError: Always (stub implementation)
        """
        raise NotImplementedError(
            "Image generation not yet implemented. "
            "This is a stub for future DALL-E integration."
        )

    async def get_supported_sizes(self) -> list[tuple[int, int]]:
        """
        Get list of supported image sizes.

        Returns:
            List of standard DALL-E sizes
        """
        return [
            (1024, 1024),  # Square
            (1792, 1024),  # Landscape
            (1024, 1792),  # Portrait
        ]

    async def test_connection(self) -> bool:
        """
        Test connection (stub always returns True).

        Returns:
            True (stub implementation)
        """
        logger.info("DallEProvider stub - connection test skipped")
        return True
