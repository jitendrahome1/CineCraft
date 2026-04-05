"""
ElevenLabs Voice Provider Stub.
Placeholder implementation for future ElevenLabs integration.
"""
from typing import Optional

from app.providers.base.voice_provider import VoiceProvider
from app.core.logging import get_logger
from app.core.errors import AIProviderError

logger = get_logger(__name__)


class ElevenLabsProvider(VoiceProvider):
    """
    Stub implementation for ElevenLabs voice generation.
    This is a placeholder - actual implementation will be added in Phase 7.
    """

    def __init__(self, api_key: str, config: Optional[dict] = None):
        super().__init__(api_key, config)
        logger.warning("ElevenLabsProvider is a stub implementation")

    async def generate_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        speed: float = 1.0,
        pitch: float = 1.0
    ) -> bytes:
        """
        Generate speech audio from text.

        NOTE: This is a stub implementation.

        Args:
            text: Text to convert to speech
            voice_id: Optional voice identifier
            speed: Speech speed
            pitch: Voice pitch

        Returns:
            Audio data as bytes

        Raises:
            NotImplementedError: Always (stub implementation)
        """
        raise NotImplementedError(
            "Voice generation not yet implemented. "
            "This is a stub for future ElevenLabs integration."
        )

    async def list_available_voices(self) -> list[dict[str, str]]:
        """
        Get list of available voices.

        Returns:
            List of mock voice configurations
        """
        # Mock data for development
        return [
            {
                "id": "voice_1",
                "name": "Rachel",
                "gender": "female",
                "language": "en-US"
            },
            {
                "id": "voice_2",
                "name": "Adam",
                "gender": "male",
                "language": "en-US"
            },
            {
                "id": "voice_3",
                "name": "Domi",
                "gender": "female",
                "language": "en-US"
            }
        ]

    async def test_connection(self) -> bool:
        """
        Test connection (stub always returns True).

        Returns:
            True (stub implementation)
        """
        logger.info("ElevenLabsProvider stub - connection test skipped")
        return True
