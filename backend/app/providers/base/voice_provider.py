"""
Base abstract class for voice/speech generation providers.
"""
from abc import ABC, abstractmethod
from typing import Optional


class VoiceProvider(ABC):
    """
    Abstract base class for voice generation providers.
    All voice providers must implement these methods.
    """

    def __init__(self, api_key: str, config: Optional[dict] = None):
        """
        Initialize voice provider.

        Args:
            api_key: API key for the provider
            config: Optional configuration dict
        """
        self.api_key = api_key
        self.config = config or {}

    @abstractmethod
    async def generate_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        speed: float = 1.0,
        pitch: float = 1.0
    ) -> bytes:
        """
        Generate speech audio from text.

        Args:
            text: Text to convert to speech
            voice_id: Optional voice identifier
            speed: Speech speed (0.5 to 2.0)
            pitch: Voice pitch (0.5 to 2.0)

        Returns:
            Audio data as bytes (MP3 format)
        """
        pass

    @abstractmethod
    async def list_available_voices(self) -> list[dict[str, str]]:
        """
        Get list of available voices.

        Returns:
            List of dicts with keys:
                - id: Voice identifier
                - name: Voice name
                - gender: Voice gender
                - language: Language code
        """
        pass
