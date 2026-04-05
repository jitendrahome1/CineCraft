"""
OpenAI Image Provider Implementation.
Uses OpenAI's gpt-image-1 (or DALL-E 3) API for image generation.
Used in production mode for high-quality, story-accurate images.
"""
from typing import Optional
import httpx

from app.providers.base.image_provider import ImageProvider
from app.core.logging import get_logger
from app.core.errors import AIProviderError

logger = get_logger(__name__)


class DallEProvider(ImageProvider):
    """
    OpenAI image generation provider (gpt-image-1 / DALL-E 3).

    Uses OpenAI API to generate high-quality, story-accurate images.
    Default model: gpt-image-1 (latest, best prompt adherence).
    """

    def __init__(self, api_key: str, config: Optional[dict] = None):
        """
        Initialize OpenAI image provider.

        Args:
            api_key: OpenAI API key
            config: Optional configuration
                - model: Model to use (default: "gpt-image-1")
                - quality: Image quality "low", "medium", "high", or "auto" (default: "high")
                - style: "vivid" or "natural" (default: "vivid", only for dall-e-3)
        """
        super().__init__(api_key, config)
        self.model = config.get("model", "gpt-image-1") if config else "gpt-image-1"
        self.quality = config.get("quality", "high") if config else "high"
        self.default_style = config.get("style", "vivid") if config else "vivid"
        self.api_base = "https://api.openai.com/v1"

        logger.info(f"Initialized DallEProvider with model {self.model}")

    async def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        style: Optional[str] = None
    ) -> bytes:
        """
        Generate image from text prompt using OpenAI image API.

        Supports both gpt-image-1 and dall-e-3 models.

        Args:
            prompt: Text description of image
            width: Image width in pixels
            height: Image height in pixels
            style: Optional style ("vivid" or "natural", dall-e-3 only)

        Returns:
            Image data as bytes

        Raises:
            AIProviderError: If generation fails
        """
        try:
            size = self._get_size_string(width, height)
            enhanced_prompt = self._enhance_prompt(prompt)

            logger.info(f"[PRODUCTION] Generating image with {self.model}: {enhanced_prompt[:120]}...")

            # Build request body based on model
            request_body = {
                "model": self.model,
                "prompt": enhanced_prompt,
                "size": size,
                "n": 1,
            }

            if self.model == "gpt-image-1":
                # gpt-image-1: quality = low/medium/high/auto, no style param
                # Use b64_json to avoid expiring URLs
                request_body["quality"] = self.quality
                request_body["response_format"] = "b64_json"
            else:
                # dall-e-3: quality = standard/hd, has style param
                request_body["quality"] = self.quality
                request_body["style"] = style or self.default_style
                request_body["response_format"] = "b64_json"

            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    f"{self.api_base}/images/generations",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=request_body
                )

                if response.status_code != 200:
                    error_detail = response.text
                    logger.error(f"OpenAI Image API error ({response.status_code}): {error_detail}")
                    raise AIProviderError(f"Image generation failed: {error_detail}")

                data = response.json()
                image_data = data["data"][0]

                # Decode base64 image
                import base64
                image_bytes = base64.b64decode(image_data["b64_json"])

                logger.info(
                    f"[PRODUCTION] Image generated successfully "
                    f"({len(image_bytes)} bytes, model={self.model})"
                )
                return image_bytes

        except httpx.TimeoutException:
            logger.error(f"{self.model} API request timed out")
            raise AIProviderError("Image generation timed out. Please try again.")
        except httpx.RequestError as e:
            logger.error(f"{self.model} API request error: {e}")
            raise AIProviderError(f"Image generation request failed: {str(e)}")
        except AIProviderError:
            raise
        except Exception as e:
            logger.exception(f"Unexpected error in {self.model} image generation")
            raise AIProviderError(f"Image generation failed: {str(e)}")

    def _get_size_string(self, width: int, height: int) -> str:
        """
        Convert width/height to API size string.

        gpt-image-1 supports: 1024x1024, 1536x1024, 1024x1536, auto
        dall-e-3 supports: 1024x1024, 1792x1024, 1024x1792
        """
        if self.model == "gpt-image-1":
            if width == height:
                return "1024x1024"
            elif width > height:
                return "1536x1024"  # Landscape
            else:
                return "1024x1536"  # Portrait
        else:
            # dall-e-3
            if width == height:
                return "1024x1024"
            elif width > height:
                return "1792x1024"
            else:
                return "1024x1792"

    def _enhance_prompt(self, prompt: str) -> str:
        """
        Enhance prompt for better DALL-E results.

        Args:
            prompt: Original prompt

        Returns:
            Enhanced prompt
        """
        # Add cinematic quality descriptors if not present
        quality_terms = [
            "cinematic", "high quality", "detailed",
            "professional", "4k", "hd"
        ]

        has_quality = any(term in prompt.lower() for term in quality_terms)

        if not has_quality:
            # Add cinematic quality prefix
            prompt = f"Cinematic, high quality: {prompt}"

        # Ensure it's not too long (DALL-E has 4000 char limit)
        if len(prompt) > 4000:
            prompt = prompt[:3997] + "..."

        return prompt

    async def get_supported_sizes(self) -> list[tuple[int, int]]:
        """
        Get list of supported image sizes for DALL-E 3.

        Returns:
            List of (width, height) tuples
        """
        return [
            (1024, 1024),  # Square
            (1792, 1024),  # Landscape
            (1024, 1792),  # Portrait
        ]

    async def test_connection(self) -> bool:
        """
        Test connection to OpenAI API.

        Returns:
            True if connection successful

        Raises:
            AIProviderError: If connection fails
        """
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(
                    f"{self.api_base}/models",
                    headers={
                        "Authorization": f"Bearer {self.api_key}"
                    }
                )

                if response.status_code == 200:
                    logger.info("DALL-E provider connection test successful")
                    return True
                else:
                    logger.error(f"DALL-E connection test failed: {response.status_code}")
                    return False

        except Exception as e:
            logger.error(f"DALL-E connection test error: {e}")
            return False

    def get_estimated_cost(self, width: int, height: int) -> int:
        """
        Get estimated cost in cents for image generation.

        Args:
            width: Image width
            height: Image height

        Returns:
            Estimated cost in cents
        """
        # DALL-E 3 pricing (as of 2024):
        # Standard quality: $0.040 per image (1024x1024)
        # Standard quality: $0.080 per image (1024x1792 or 1792x1024)
        # HD quality: $0.080 per image (1024x1024)
        # HD quality: $0.120 per image (1024x1792 or 1792x1024)

        if self.quality == "hd":
            if width != height:
                return 12  # $0.12 = 12 cents
            return 8  # $0.08 = 8 cents
        else:  # standard
            if width != height:
                return 8  # $0.08 = 8 cents
            return 4  # $0.04 = 4 cents
