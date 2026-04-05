"""
Gemini Image Provider Implementation.
Uses Google's Gemini API for image generation.
"""
from typing import Optional
import io
import time
import re

from google import genai
from google.genai import types

from app.providers.base.image_provider import ImageProvider
from app.core.logging import get_logger
from app.core.errors import AIProviderError

logger = get_logger(__name__)

# Models to try in order of preference (verified available models)
FALLBACK_MODELS = [
    "gemini-2.5-flash-image",
    "gemini-3.1-flash-image-preview",
    "gemini-3-pro-image-preview",
]

# Retry config for rate limits
MAX_RETRIES = 3
RATE_LIMIT_WAIT_SECONDS = 60


class GeminiImageProvider(ImageProvider):
    """
    Gemini image generation provider.

    Uses Google's Gemini API to generate images from text prompts.
    Retries with delay when rate-limited, then falls back to alternative models.
    """

    def __init__(self, api_key: str, config: Optional[dict] = None):
        super().__init__(api_key, config)
        self.model = config.get("model", FALLBACK_MODELS[0]) if config else FALLBACK_MODELS[0]
        self.client = genai.Client(api_key=api_key)
        logger.info(f"Initialized GeminiImageProvider with model {self.model}")

    def _extract_retry_delay(self, error_str: str) -> int:
        """Extract retry delay from error message, default to RATE_LIMIT_WAIT_SECONDS."""
        match = re.search(r'retry in (\d+)', error_str, re.IGNORECASE)
        if match:
            return int(match.group(1)) + 5  # add 5s buffer
        return RATE_LIMIT_WAIT_SECONDS

    def _try_generate(self, model: str, enhanced_prompt: str) -> Optional[bytes]:
        """Single attempt to generate image with a model. Returns raw image bytes or None."""
        response = self.client.models.generate_content(
            model=model,
            contents=[enhanced_prompt],
            config=types.GenerateContentConfig(
                response_modalities=["TEXT", "IMAGE"],
            ),
        )

        if response.candidates and response.candidates[0].content and response.candidates[0].content.parts:
            for part in response.candidates[0].content.parts:
                if part.inline_data is not None:
                    return part.inline_data.data

        return None

    def generate_image_sync(
        self,
        prompt: str,
        width: int = 1920,
        height: int = 1080,
        style: Optional[str] = None
    ) -> bytes:
        """
        Synchronous image generation with retry and model fallback.

        On rate limit (429): waits and retries the same model up to MAX_RETRIES times.
        If all retries fail, moves to the next model.
        """
        enhanced_prompt = self._enhance_prompt(prompt, style)
        logger.info(f"Generating image with Gemini: {enhanced_prompt[:100]}...")

        # Build list of models to try
        models_to_try = [self.model] + [m for m in FALLBACK_MODELS if m != self.model]
        last_error = None

        for model in models_to_try:
            for attempt in range(1, MAX_RETRIES + 1):
                try:
                    logger.info(f"Trying model: {model} (attempt {attempt}/{MAX_RETRIES})")

                    raw_bytes = self._try_generate(model, enhanced_prompt)

                    if raw_bytes is None:
                        logger.warning(f"Model {model} returned no image data")
                        break  # move to next model

                    # Process image
                    from PIL import Image as PILImage
                    img = PILImage.open(io.BytesIO(raw_bytes))

                    if img.size != (width, height):
                        img = img.resize((width, height), PILImage.LANCZOS)

                    output = io.BytesIO()
                    img = img.convert("RGB")
                    img.save(output, format="JPEG", quality=95)
                    result_bytes = output.getvalue()

                    logger.info(f"Successfully generated image with {model} ({len(result_bytes)} bytes)")
                    return result_bytes

                except Exception as e:
                    error_str = str(e)
                    last_error = e

                    if "429" in error_str or "RESOURCE_EXHAUSTED" in error_str:
                        wait_time = self._extract_retry_delay(error_str)
                        logger.warning(
                            f"Model {model} rate-limited (attempt {attempt}/{MAX_RETRIES}). "
                            f"Waiting {wait_time}s before retry..."
                        )
                        if attempt < MAX_RETRIES:
                            time.sleep(wait_time)
                            continue
                        else:
                            logger.warning(f"Model {model} exhausted all retries, trying next model...")
                            break  # move to next model
                    elif "404" in error_str or "NOT_FOUND" in error_str:
                        logger.warning(f"Model {model} not found, trying next...")
                        break  # move to next model
                    else:
                        logger.error(f"Model {model} failed: {error_str}")
                        raise AIProviderError(f"Image generation failed: {error_str}")

        # All models and retries exhausted
        raise AIProviderError(
            f"All Gemini image models failed after retries. "
            f"Rate limit quota may be exhausted. "
            f"Please wait a few minutes and try again, or enable billing on your Google Cloud project. "
            f"Last error: {last_error}"
        )

    async def generate_image(
        self,
        prompt: str,
        width: int = 1920,
        height: int = 1080,
        style: Optional[str] = None
    ) -> bytes:
        """Generate image asynchronously by running sync call in executor."""
        import asyncio
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.generate_image_sync, prompt, width, height, style
        )

    def _enhance_prompt(self, prompt: str, style: Optional[str] = None) -> str:
        """Enhance prompt for better Gemini image results."""
        quality_terms = [
            "cinematic", "high quality", "detailed",
            "professional", "4k", "hd"
        ]
        has_quality = any(term in prompt.lower() for term in quality_terms)

        if style:
            prompt = f"{style} style, {prompt}"

        if not has_quality:
            prompt = f"Generate a cinematic, high quality, detailed, photorealistic image: {prompt}"

        return prompt

    async def get_supported_sizes(self) -> list[tuple[int, int]]:
        """Get list of supported image sizes."""
        return [
            (1024, 1024),
            (1920, 1080),
            (1080, 1920),
            (1792, 1024),
            (1024, 1792),
        ]

    async def test_connection(self) -> bool:
        """Test connection to Gemini API."""
        try:
            self.client.models.get(model=self.model)
            logger.info("Gemini provider connection test successful")
            return True
        except Exception as e:
            logger.error(f"Gemini connection test error: {e}")
            return False
