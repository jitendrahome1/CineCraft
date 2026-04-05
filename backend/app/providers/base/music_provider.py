"""
Base abstract class for music generation providers.
"""
from abc import ABC, abstractmethod
from typing import Optional


class MusicProvider(ABC):
    """
    Abstract base class for music generation providers.
    All music providers must implement these methods.
    """

    def __init__(self, api_key: str, config: Optional[dict] = None):
        """
        Initialize music provider.

        Args:
            api_key: API key for the provider
            config: Optional configuration dict
        """
        self.api_key = api_key
        self.config = config or {}

    @abstractmethod
    async def generate_music(
        self,
        prompt: str,
        duration: int,
        mood: Optional[str] = None,
        genre: Optional[str] = None
    ) -> bytes:
        """
        Generate background music.

        Args:
            prompt: Description of desired music
            duration: Duration in seconds
            mood: Optional mood (e.g., "happy", "sad", "dramatic")
            genre: Optional genre (e.g., "orchestral", "electronic")

        Returns:
            Audio data as bytes (MP3 format)
        """
        pass

    @abstractmethod
    async def get_supported_moods(self) -> list[str]:
        """
        Get list of supported moods.

        Returns:
            List of mood strings
        """
        pass

    @abstractmethod
    async def get_supported_genres(self) -> list[str]:
        """
        Get list of supported genres.

        Returns:
            List of genre strings
        """
        pass
