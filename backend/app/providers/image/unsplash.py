"""
Unsplash Image Provider Implementation.
Uses Unsplash Source API for free, keyword-based stock images.
WARNING: This is a fallback provider — stock photos cannot match
story-specific AI-generated prompts accurately.
No API key required.
"""
from typing import Optional
import io
import re
import httpx

from app.providers.base.image_provider import ImageProvider
from app.core.logging import get_logger
from app.core.errors import AIProviderError

logger = get_logger(__name__)


class UnsplashImageProvider(ImageProvider):
    """
    Free image provider using Unsplash Source API.
    Fetches stock images based on scene keywords.
    No API key required.

    WARNING: Stock photos are a last-resort fallback.
    They will NOT accurately represent story scenes.
    Use a real AI image generator (DALL-E, Gemini) as the primary provider.
    """

    def __init__(self, api_key: str = "", config: Optional[dict] = None):
        super().__init__(api_key or "free", config)
        logger.info("Initialized UnsplashImageProvider (free, stock photos only)")

    def _extract_keywords(self, prompt: str) -> str:
        """
        Extract meaningful keywords from a scene description.
        Prioritizes nouns and adjectives that describe the scene subject.
        """
        # Remove common filler words and AI-prompt-specific jargon
        stop_words = {
            'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall',
            'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in',
            'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
            'through', 'during', 'before', 'after', 'above', 'below',
            'between', 'under', 'and', 'but', 'or', 'nor', 'not', 'so',
            'yet', 'both', 'either', 'neither', 'each', 'every', 'all',
            'any', 'few', 'more', 'most', 'other', 'some', 'such', 'no',
            'only', 'own', 'same', 'than', 'too', 'very', 'just', 'because',
            # AI prompt jargon that hurts stock photo search
            'generate', 'image', 'cinematic', 'high', 'quality', 'detailed',
            'photorealistic', 'style', 'scene', 'showing', 'depicts',
            'featuring', 'where', 'which', 'that', 'this', 'those', 'these',
            'shot', 'wide', 'angle', 'close', 'medium', 'lighting',
            'warm', 'soft', 'dramatic', 'color', 'grading', 'film',
            'like', 'aspect', 'ratio', 'composition', 'resolution',
            'nostalgic', 'capturing', 'evoking', 'creating', 'enhancing',
            'reflecting', 'casting', 'emphasizing', 'filled', 'setting',
            'visual', 'prompt', 'format', 'render', 'realistic',
        }

        # Clean and extract words
        words = re.findall(r'[a-zA-Z]+', prompt.lower())
        keywords = [w for w in words if w not in stop_words and len(w) > 2]

        # Take top 5 most descriptive keywords
        selected = keywords[:5]
        result = ','.join(selected)
        logger.info(f"Extracted keywords from prompt: {result}")
        return result

    async def generate_image(
        self,
        prompt: str,
        width: int = 1920,
        height: int = 1080,
        style: Optional[str] = None
    ) -> bytes:
        """
        Fetch a stock image from Unsplash based on prompt keywords.

        WARNING: Stock photos are approximate matches based on keywords.
        They will NOT match detailed scene descriptions accurately.
        """
        keywords = self._extract_keywords(prompt)
        logger.warning(
            f"Using Unsplash STOCK PHOTOS (fallback). "
            f"Images may not match story accurately. Keywords: {keywords}"
        )

        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as client:
            # Try Unsplash Source API
            unsplash_url = f"https://source.unsplash.com/{width}x{height}/?{keywords}"
            try:
                response = await client.get(unsplash_url)
                ct = response.headers.get('content-type', '')
                if response.status_code == 200 and 'image' in ct and len(response.content) > 5000:
                    logger.info(f"Got Unsplash stock image ({len(response.content)} bytes)")
                    return self._ensure_size(response.content, width, height)
                else:
                    logger.warning(
                        f"Unsplash returned non-image response "
                        f"(status={response.status_code}, content-type={ct}, size={len(response.content)})"
                    )
            except Exception as e:
                logger.warning(f"Unsplash request failed: {e}")

        # DO NOT fall back to Picsum (random images completely unrelated to story).
        # It's better to fail clearly than to serve a random tulip photo
        # for a "schoolyard with students" prompt.
        raise AIProviderError(
            "Unsplash stock photo fallback failed. "
            "Please configure a real AI image provider (DALL-E or Gemini) "
            "in your .env file for accurate story-matched images. "
            "Set IMAGE_PROVIDER=dalle with OPENAI_API_KEY, "
            "or IMAGE_PROVIDER=gemini with GEMINI_API_KEY."
        )

    def _ensure_size(self, image_bytes: bytes, width: int, height: int) -> bytes:
        """Ensure image is the correct size."""
        from PIL import Image as PILImage
        img = PILImage.open(io.BytesIO(image_bytes))
        if img.size != (width, height):
            img = img.resize((width, height), PILImage.LANCZOS)
        output = io.BytesIO()
        img = img.convert("RGB")
        img.save(output, format="JPEG", quality=95)
        return output.getvalue()

    async def get_supported_sizes(self) -> list[tuple[int, int]]:
        return [
            (1024, 1024),
            (1920, 1080),
            (1080, 1920),
            (1792, 1024),
            (1024, 1792),
        ]

    async def test_connection(self) -> bool:
        try:
            async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                response = await client.get(
                    "https://source.unsplash.com/100x100/?nature"
                )
                return response.status_code == 200
        except Exception:
            return False
