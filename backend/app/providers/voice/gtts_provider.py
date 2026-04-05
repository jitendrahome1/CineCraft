"""
Google Text-to-Speech (gTTS) Voice Provider.
Free TTS provider that doesn't require an API key.
Supports multiple languages including English and Hindi.
"""
from typing import Optional, List, Dict
import io

from app.providers.base.voice_provider import VoiceProvider
from app.core.logging import get_logger
from app.core.errors import AIProviderError

logger = get_logger(__name__)


class GTTSProvider(VoiceProvider):
    """
    Free Google Text-to-Speech provider using gTTS library.
    No API key required. Supports multiple languages.
    """

    # Language mapping for documentary narration
    LANGUAGE_MAP = {
        "english": "en",
        "hindi": "hi",
        "en": "en",
        "hi": "hi",
        "en-US": "en",
        "en-GB": "en",
        "hi-IN": "hi",
    }

    def __init__(self, api_key: str = "", config: Optional[dict] = None):
        """
        Initialize gTTS provider.

        Args:
            api_key: Not required (ignored)
            config: Optional configuration
                - language: Language code (default: "en")
                - slow: Speak slowly (default: False)
                - tld: Top-level domain for Google (default: "com")
        """
        super().__init__(api_key or "free", config)
        self.language = (config or {}).get("language", "en")
        self.slow = (config or {}).get("slow", False)
        self.tld = (config or {}).get("tld", "com")

        logger.info(f"Initialized gTTS provider (language: {self.language})")

    async def generate_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        speed: float = 1.0,
        pitch: float = 1.0
    ) -> bytes:
        """
        Generate speech audio from text using gTTS.

        Args:
            text: Text to convert to speech
            voice_id: Language code override (e.g., "en", "hi")
            speed: Speech speed (uses slow mode if < 0.8)
            pitch: Not supported by gTTS (ignored)

        Returns:
            Audio data as bytes (MP3 format)

        Raises:
            AIProviderError: If generation fails
        """
        try:
            from gtts import gTTS
        except ImportError:
            raise AIProviderError(
                "gTTS library not installed. Run: pip install gTTS"
            )

        try:
            # Determine language
            lang = voice_id or self.language
            lang = self.LANGUAGE_MAP.get(lang, lang)

            # Determine speed
            slow = self.slow or speed < 0.8

            logger.info(f"Generating speech with gTTS (lang: {lang}, {len(text)} chars)")

            # Generate speech
            tts = gTTS(text=text, lang=lang, slow=slow, tld=self.tld)

            # Write to bytes buffer
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)

            audio_bytes = audio_buffer.read()
            logger.info(f"Successfully generated speech ({len(audio_bytes)} bytes)")

            return audio_bytes

        except Exception as e:
            logger.error(f"gTTS speech generation failed: {e}")
            raise AIProviderError(f"Speech generation failed: {str(e)}")

    async def list_available_voices(self) -> list[dict[str, str]]:
        """
        Get list of available voices (languages) for gTTS.

        Returns:
            List of available language configurations
        """
        return [
            {"id": "en", "name": "English", "gender": "neutral", "language": "en"},
            {"id": "hi", "name": "Hindi", "gender": "neutral", "language": "hi"},
            {"id": "en-uk", "name": "English (UK)", "gender": "neutral", "language": "en"},
            {"id": "en-au", "name": "English (Australia)", "gender": "neutral", "language": "en"},
        ]

    def get_estimated_cost(self, character_count: int) -> int:
        """gTTS is free, so cost is always 0."""
        return 0
