"""
Suno Music Provider Stub.
Placeholder implementation for future Suno integration.
"""
from typing import Optional

from app.providers.base.music_provider import MusicProvider
from app.core.logging import get_logger
from app.core.errors import AIProviderError

logger = get_logger(__name__)


class SunoProvider(MusicProvider):
    """
    Stub implementation for Suno music generation.
    This is a placeholder - actual implementation will be added in Phase 7.
    """

    def __init__(self, api_key: str, config: Optional[dict] = None):
        super().__init__(api_key, config)
        logger.warning("SunoProvider is a stub implementation")

    async def generate_music(
        self,
        prompt: str,
        duration: int,
        mood: Optional[str] = None,
        genre: Optional[str] = None
    ) -> bytes:
        """
        Generate background music.

        NOTE: This is a stub implementation.

        Args:
            prompt: Description of desired music
            duration: Duration in seconds
            mood: Optional mood
            genre: Optional genre

        Returns:
            Audio data as bytes

        Raises:
            NotImplementedError: Always (stub implementation)
        """
        raise NotImplementedError(
            "Music generation not yet implemented. "
            "This is a stub for future Suno integration."
        )

    async def get_supported_moods(self) -> list[str]:
        """
        Get list of supported moods.

        Returns:
            List of mock moods
        """
        return [
            "happy",
            "sad",
            "dramatic",
            "mysterious",
            "peaceful",
            "energetic",
            "tense",
            "romantic"
        ]

    async def get_supported_genres(self) -> list[str]:
        """
        Get list of supported genres.

        Returns:
            List of mock genres
        """
        return [
            "orchestral",
            "electronic",
            "acoustic",
            "ambient",
            "cinematic",
            "rock",
            "jazz",
            "folk"
        ]

    async def test_connection(self) -> bool:
        """
        Test connection (stub always returns True).

        Returns:
            True (stub implementation)
        """
        logger.info("SunoProvider stub - connection test skipped")
        return True
