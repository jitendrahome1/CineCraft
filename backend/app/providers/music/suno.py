"""
Suno Music Provider Implementation.
Uses Suno API for AI music generation.
"""
from typing import Optional, List
import httpx
import asyncio

from app.providers.base.music_provider import MusicProvider
from app.core.logging import get_logger
from app.core.errors import AIProviderError

logger = get_logger(__name__)


class SunoProvider(MusicProvider):
    """
    Suno AI music generation provider.

    Uses Suno API to generate background music for videos.
    """

    def __init__(self, api_key: str, config: Optional[dict] = None):
        """
        Initialize Suno provider.

        Args:
            api_key: Suno API key
            config: Optional configuration
                - api_base: Custom API base URL
                - model: Model to use (default: "chirp-v3")
                - poll_interval: Polling interval in seconds (default: 5)
                - max_wait_time: Maximum wait time in seconds (default: 300)
        """
        super().__init__(api_key, config)
        self.api_base = config.get("api_base", "https://api.suno.ai/v1") if config else "https://api.suno.ai/v1"
        self.model = config.get("model", "chirp-v3") if config else "chirp-v3"
        self.poll_interval = config.get("poll_interval", 5) if config else 5
        self.max_wait_time = config.get("max_wait_time", 300) if config else 300

        logger.info(f"Initialized SunoProvider with model {self.model}")

    async def generate_music(
        self,
        prompt: str,
        duration: int = 30,
        mood: Optional[str] = None,
        genre: Optional[str] = None
    ) -> bytes:
        """
        Generate background music using Suno.

        Args:
            prompt: Text description of desired music
            duration: Desired duration in seconds (15-300)
            mood: Optional mood (e.g., "upbeat", "calm", "dramatic")
            genre: Optional genre (e.g., "orchestral", "electronic", "ambient")

        Returns:
            Audio data as bytes (MP3 format)

        Raises:
            AIProviderError: If generation fails
        """
        try:
            # Enhance prompt with mood and genre
            full_prompt = self._build_prompt(prompt, mood, genre)

            # Clamp duration to valid range
            duration = max(15, min(300, duration))

            logger.info(f"Generating music with Suno: {full_prompt[:100]}...")

            # Start generation
            generation_id = await self._start_generation(full_prompt, duration)

            # Poll for completion
            audio_url = await self._poll_generation(generation_id)

            # Download audio
            audio_bytes = await self._download_audio(audio_url)

            logger.info(f"Successfully generated music ({len(audio_bytes)} bytes)")
            return audio_bytes

        except Exception as e:
            logger.exception("Error in music generation")
            raise AIProviderError(f"Music generation failed: {str(e)}")

    async def _start_generation(self, prompt: str, duration: int) -> str:
        """
        Start music generation task.

        Args:
            prompt: Full prompt
            duration: Duration in seconds

        Returns:
            Generation ID

        Raises:
            AIProviderError: If request fails
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{self.api_base}/generate",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "prompt": prompt,
                        "duration": duration,
                        "model": self.model
                    }
                )

                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(f"Suno API error: {error_detail}")
                    raise AIProviderError(f"Failed to start music generation: {error_detail}")

                data = response.json()
                generation_id = data.get("id")

                if not generation_id:
                    raise AIProviderError("No generation ID returned")

                logger.info(f"Started music generation: {generation_id}")
                return generation_id

        except httpx.RequestError as e:
            logger.error(f"Suno API request error: {e}")
            raise AIProviderError(f"Music generation request failed: {str(e)}")

    async def _poll_generation(self, generation_id: str) -> str:
        """
        Poll for generation completion.

        Args:
            generation_id: Generation ID

        Returns:
            URL to generated audio

        Raises:
            AIProviderError: If polling fails or times out
        """
        elapsed_time = 0

        async with httpx.AsyncClient(timeout=10.0) as client:
            while elapsed_time < self.max_wait_time:
                try:
                    response = await client.get(
                        f"{self.api_base}/generate/{generation_id}",
                        headers={
                            "Authorization": f"Bearer {self.api_key}"
                        }
                    )

                    if response.status_code != 200:
                        logger.error(f"Polling error: {response.text}")
                        raise AIProviderError("Failed to check generation status")

                    data = response.json()
                    status = data.get("status")

                    if status == "completed":
                        audio_url = data.get("audio_url")
                        if not audio_url:
                            raise AIProviderError("No audio URL in completed generation")
                        logger.info(f"Music generation completed: {audio_url}")
                        return audio_url

                    elif status == "failed":
                        error = data.get("error", "Unknown error")
                        raise AIProviderError(f"Music generation failed: {error}")

                    # Still processing
                    logger.debug(f"Generation {generation_id} still processing...")
                    await asyncio.sleep(self.poll_interval)
                    elapsed_time += self.poll_interval

                except httpx.RequestError as e:
                    logger.warning(f"Polling request error: {e}")
                    await asyncio.sleep(self.poll_interval)
                    elapsed_time += self.poll_interval

            raise AIProviderError(f"Music generation timed out after {self.max_wait_time}s")

    async def _download_audio(self, audio_url: str) -> bytes:
        """
        Download generated audio file.

        Args:
            audio_url: URL to audio file

        Returns:
            Audio bytes

        Raises:
            AIProviderError: If download fails
        """
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(audio_url)

                if response.status_code != 200:
                    raise AIProviderError("Failed to download audio file")

                return response.content

        except httpx.RequestError as e:
            logger.error(f"Audio download error: {e}")
            raise AIProviderError(f"Failed to download audio: {str(e)}")

    def _build_prompt(
        self,
        prompt: str,
        mood: Optional[str],
        genre: Optional[str]
    ) -> str:
        """
        Build full prompt with mood and genre.

        Args:
            prompt: Base prompt
            mood: Optional mood
            genre: Optional genre

        Returns:
            Enhanced prompt
        """
        parts = []

        if genre:
            parts.append(f"{genre} music")

        if mood:
            parts.append(f"{mood} mood")

        parts.append(prompt)

        return ", ".join(parts)

    async def get_supported_moods(self) -> List[str]:
        """
        Get list of supported moods.

        Returns:
            List of mood strings
        """
        return [
            "upbeat",
            "calm",
            "dramatic",
            "mysterious",
            "joyful",
            "melancholic",
            "energetic",
            "peaceful",
            "tense",
            "romantic"
        ]

    async def get_supported_genres(self) -> List[str]:
        """
        Get list of supported genres.

        Returns:
            List of genre strings
        """
        return [
            "orchestral",
            "electronic",
            "ambient",
            "cinematic",
            "piano",
            "guitar",
            "synthwave",
            "classical",
            "jazz",
            "lo-fi"
        ]

    async def test_connection(self) -> bool:
        """
        Test connection to Suno API.

        Returns:
            True if connection successful
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.api_base}/health",
                    headers={
                        "Authorization": f"Bearer {self.api_key}"
                    }
                )

                if response.status_code == 200:
                    logger.info("Suno provider connection test successful")
                    return True
                else:
                    logger.error(f"Suno connection test failed: {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"Suno connection test error: {e}")
            return False

    def get_estimated_cost(self, duration: int) -> int:
        """
        Get estimated cost in cents for music generation.

        Args:
            duration: Duration in seconds

        Returns:
            Estimated cost in cents
        """
        # Suno pricing (estimated):
        # ~$0.10 per 30 seconds of generated music
        # = ~0.33 cents per second

        cost_per_second = 0.33  # cents
        total_cost = int(duration * cost_per_second)

        # Minimum charge of 5 cents
        return max(5, total_cost)
