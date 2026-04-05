"""
OpenRouter Image Provider Implementation.
Uses OpenRouter API with Gemini image models for image generation.
"""
from typing import Optional
import io
import base64
import httpx

from app.providers.base.image_provider import ImageProvider
from app.core.logging import get_logger
from app.core.errors import AIProviderError

logger = get_logger(__name__)

# OpenRouter image-capable models in order of preference
OPENROUTER_IMAGE_MODELS = [
    "sourceful/riverflow-v2-pro",
    "google/gemini-3.1-flash-image-preview",
    "google/gemini-2.5-flash-image",
]

OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterImageProvider(ImageProvider):
    """
    OpenRouter image generation provider.

    Routes image generation through OpenRouter API to Gemini image models.
    """

    def __init__(self, api_key: str, config: Optional[dict] = None):
        super().__init__(api_key, config)
        self.model = (config or {}).get("model", OPENROUTER_IMAGE_MODELS[0])
        self.api_key = api_key
        logger.info(f"Initialized OpenRouterImageProvider with model {self.model}")

    async def generate_image(
        self,
        prompt: str,
        width: int = 1920,
        height: int = 1080,
        style: Optional[str] = None
    ) -> bytes:
        """Generate image via OpenRouter API."""
        enhanced_prompt = self._enhance_prompt(prompt, style)
        logger.info(f"Generating image via OpenRouter: {enhanced_prompt[:100]}...")

        # Determine aspect ratio from dimensions
        aspect_ratio = self._get_aspect_ratio(width, height)

        models_to_try = [self.model] + [m for m in OPENROUTER_IMAGE_MODELS if m != self.model]
        last_error = None

        for model in models_to_try:
            try:
                logger.info(f"Trying OpenRouter model: {model}")

                async with httpx.AsyncClient(timeout=120) as client:
                    response = await client.post(
                        OPENROUTER_API_URL,
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "Content-Type": "application/json",
                        },
                        json={
                            "model": model,
                            "messages": [
                                {"role": "user", "content": enhanced_prompt}
                            ],
                            "modalities": ["image", "text"],
                            "image_config": {
                                "aspect_ratio": aspect_ratio,
                                "image_size": "1K",
                            },
                        },
                    )

                if response.status_code != 200:
                    error_data = response.json()
                    error_msg = error_data.get("error", {}).get("message", str(response.status_code))
                    raise Exception(f"OpenRouter API error ({response.status_code}): {error_msg}")

                data = response.json()
                choices = data.get("choices", [])
                if not choices:
                    logger.warning(f"Model {model}: no choices in response")
                    continue

                msg = choices[0].get("message", {})
                images = msg.get("images", [])

                if not images:
                    logger.warning(f"Model {model}: no images in response")
                    continue

                # Extract base64 image from data URL
                image_url = images[0].get("image_url", {}).get("url", "")
                if not image_url.startswith("data:"):
                    logger.warning(f"Model {model}: unexpected image format")
                    continue

                # Parse data URI: data:image/jpeg;base64,<data>
                _, b64_data = image_url.split(",", 1)
                image_bytes = base64.b64decode(b64_data)

                # Resize if needed
                from PIL import Image as PILImage
                img = PILImage.open(io.BytesIO(image_bytes))
                if img.size != (width, height):
                    img = img.resize((width, height), PILImage.LANCZOS)

                output = io.BytesIO()
                img = img.convert("RGB")
                img.save(output, format="JPEG", quality=95)
                result_bytes = output.getvalue()

                logger.info(f"Successfully generated image via OpenRouter/{model} ({len(result_bytes)} bytes)")
                return result_bytes

            except Exception as e:
                last_error = e
                error_str = str(e)
                if "429" in error_str or "rate" in error_str.lower():
                    logger.warning(f"Model {model} rate-limited, trying next...")
                    continue
                elif "invalid model" in error_str.lower() or "not found" in error_str.lower():
                    logger.warning(f"Model {model} not available, trying next...")
                    continue
                else:
                    logger.error(f"OpenRouter model {model} failed: {error_str}")
                    # Try next model instead of failing immediately
                    continue

        raise AIProviderError(
            f"All OpenRouter image models failed. Last error: {last_error}"
        )

    def _enhance_prompt(self, prompt: str, style: Optional[str] = None) -> str:
        """Enhance prompt for better image results."""
        quality_terms = ["cinematic", "high quality", "detailed", "professional", "4k", "hd"]
        has_quality = any(term in prompt.lower() for term in quality_terms)

        if style:
            prompt = f"{style} style, {prompt}"

        if not has_quality:
            prompt = f"Generate a cinematic, high quality, detailed, photorealistic image: {prompt}"

        return prompt

    def _get_aspect_ratio(self, width: int, height: int) -> str:
        """Convert dimensions to aspect ratio string."""
        ratio = width / height
        if abs(ratio - 16 / 9) < 0.1:
            return "16:9"
        elif abs(ratio - 1) < 0.1:
            return "1:1"
        elif abs(ratio - 9 / 16) < 0.1:
            return "9:16"
        elif abs(ratio - 21 / 9) < 0.1:
            return "21:9"
        return "16:9"  # default

    async def get_supported_sizes(self) -> list[tuple[int, int]]:
        """Get list of supported image sizes."""
        return [
            (1024, 1024),
            (1920, 1080),
            (1080, 1920),
        ]

    async def test_connection(self) -> bool:
        """Test connection to OpenRouter API."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    "https://openrouter.ai/api/v1/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                )
                return response.status_code == 200
        except Exception as e:
            logger.error(f"OpenRouter connection test error: {e}")
            return False
