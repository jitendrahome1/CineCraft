"""
ElevenLabs Voice Provider Implementation.
Uses ElevenLabs API for text-to-speech generation.
"""
from typing import Optional, List, Dict, Any
import httpx

from app.providers.base.voice_provider import VoiceProvider
from app.core.logging import get_logger
from app.core.errors import AIProviderError

logger = get_logger(__name__)


class ElevenLabsProvider(VoiceProvider):
    """
    ElevenLabs text-to-speech provider.

    Uses ElevenLabs API to generate natural-sounding voice narration.
    """

    def __init__(self, api_key: str, config: Optional[dict] = None):
        """
        Initialize ElevenLabs provider.

        Args:
            api_key: ElevenLabs API key
            config: Optional configuration
                - model: Model to use (default: "eleven_monolingual_v1")
                - voice_id: Default voice ID
                - stability: Voice stability 0-1 (default: 0.5)
                - similarity_boost: Similarity boost 0-1 (default: 0.75)
        """
        super().__init__(api_key, config)
        self.model = config.get("model", "eleven_monolingual_v1") if config else "eleven_monolingual_v1"
        self.default_voice_id = config.get("voice_id") if config else None
        self.stability = config.get("stability", 0.5) if config else 0.5
        self.similarity_boost = config.get("similarity_boost", 0.75) if config else 0.75
        self.api_base = "https://api.elevenlabs.io/v1"

        logger.info(f"Initialized ElevenLabsProvider with model {self.model}")

    async def generate_speech(
        self,
        text: str,
        voice_id: Optional[str] = None,
        speed: float = 1.0
    ) -> bytes:
        """
        Generate speech from text using ElevenLabs.

        Args:
            text: Text to convert to speech
            voice_id: Optional voice ID (uses default if not provided)
            speed: Speech speed multiplier (not directly supported, for interface compatibility)

        Returns:
            Audio data as bytes (MP3 format)

        Raises:
            AIProviderError: If generation fails
        """
        try:
            # Use provided voice_id or default
            selected_voice = voice_id or self.default_voice_id

            if not selected_voice:
                # Get first available voice if no default set
                voices = await self.get_voices()
                if not voices:
                    raise AIProviderError("No voices available")
                selected_voice = voices[0]["voice_id"]

            logger.info(f"Generating speech with ElevenLabs (voice: {selected_voice})")

            # Call ElevenLabs API
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{self.api_base}/text-to-speech/{selected_voice}",
                    headers={
                        "xi-api-key": self.api_key,
                        "Content-Type": "application/json"
                    },
                    json={
                        "text": text,
                        "model_id": self.model,
                        "voice_settings": {
                            "stability": self.stability,
                            "similarity_boost": self.similarity_boost
                        }
                    }
                )

                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(f"ElevenLabs API error: {error_detail}")
                    raise AIProviderError(f"Speech generation failed: {error_detail}")

                audio_bytes = response.content
                logger.info(f"Successfully generated speech ({len(audio_bytes)} bytes)")

                return audio_bytes

        except httpx.TimeoutException:
            logger.error("ElevenLabs API request timed out")
            raise AIProviderError("Speech generation timed out. Please try again.")
        except httpx.RequestError as e:
            logger.error(f"ElevenLabs API request error: {e}")
            raise AIProviderError(f"Speech generation request failed: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error in speech generation")
            raise AIProviderError(f"Speech generation failed: {str(e)}")

    async def get_voices(self) -> List[Dict[str, Any]]:
        """
        Get list of available voices from ElevenLabs.

        Returns:
            List of voice dictionaries with id, name, and metadata

        Raises:
            AIProviderError: If retrieval fails
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.api_base}/voices",
                    headers={
                        "xi-api-key": self.api_key
                    }
                )

                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(f"ElevenLabs voices API error: {error_detail}")
                    raise AIProviderError(f"Failed to get voices: {error_detail}")

                data = response.json()
                voices = data.get("voices", [])

                # Transform to simplified format
                voice_list = []
                for voice in voices:
                    voice_list.append({
                        "voice_id": voice["voice_id"],
                        "name": voice["name"],
                        "category": voice.get("category", "unknown"),
                        "labels": voice.get("labels", {}),
                        "description": voice.get("description", "")
                    })

                logger.info(f"Retrieved {len(voice_list)} voices from ElevenLabs")
                return voice_list

        except httpx.RequestError as e:
            logger.error(f"ElevenLabs voices request error: {e}")
            raise AIProviderError(f"Failed to get voices: {str(e)}")
        except Exception as e:
            logger.exception("Unexpected error getting voices")
            raise AIProviderError(f"Failed to get voices: {str(e)}")

    async def test_connection(self) -> bool:
        """
        Test connection to ElevenLabs API.

        Returns:
            True if connection successful

        Raises:
            AIProviderError: If connection fails
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.api_base}/user",
                    headers={
                        "xi-api-key": self.api_key
                    }
                )

                if response.status_code == 200:
                    logger.info("ElevenLabs provider connection test successful")
                    return True
                else:
                    logger.error(f"ElevenLabs connection test failed: {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"ElevenLabs connection test error: {e}")
            return False

    async def get_voice_by_name(self, name: str) -> Optional[str]:
        """
        Get voice ID by voice name.

        Args:
            name: Voice name to search for

        Returns:
            Voice ID if found, None otherwise
        """
        voices = await self.get_voices()

        for voice in voices:
            if voice["name"].lower() == name.lower():
                return voice["voice_id"]

        return None

    def get_estimated_cost(self, character_count: int) -> int:
        """
        Get estimated cost in cents for speech generation.

        Args:
            character_count: Number of characters to convert

        Returns:
            Estimated cost in cents
        """
        # ElevenLabs pricing (as of 2024):
        # Starter tier: 30,000 characters/month free
        # Creator tier: $5/month for 100,000 characters
        # Pro tier: $22/month for 500,000 characters
        # Scale tier: $99/month for 2,000,000 characters
        #
        # Approximate cost: $0.30 per 1,000 characters for pay-as-you-go
        # = 0.03 cents per character

        cost_per_char = 0.03  # cents
        total_cost = int(character_count * cost_per_char)

        # Minimum charge of 1 cent
        return max(1, total_cost)

    def get_recommended_voices(self) -> Dict[str, str]:
        """
        Get recommended voice IDs for different use cases.

        Returns:
            Dictionary mapping use case to voice ID
        """
        # These are example voice IDs - actual IDs depend on ElevenLabs account
        return {
            "male_narrator": "21m00Tcm4TlvDq8ikWAM",  # Rachel (default female)
            "female_narrator": "EXAVITQu4vr4xnSDxMaL",  # Bella
            "male_young": "VR6AewLTigWG4xSOukaG",  # Arnold
            "female_young": "jBpfuIE2acCO8z3wKNLl",  # Gigi
            "male_old": "N2lVS1w4EtoT3dr4eOWO",  # Callum
            "female_old": "IKne3meq5aSn9XLyUdCD"  # Freya
        }
