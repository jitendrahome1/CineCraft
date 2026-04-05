"""
Placeholder Image Provider for Testing Mode.
Returns a generated placeholder image with the prompt text burned in,
so developers can visually verify which prompt was used for each scene.
Zero API cost, instant response.
"""
from typing import Optional
import io

from app.providers.base.image_provider import ImageProvider
from app.core.logging import get_logger

logger = get_logger(__name__)


class PlaceholderImageProvider(ImageProvider):
    """
    Testing-mode image provider.
    Generates a local placeholder image with prompt text overlay.
    No external API calls, zero cost, instant response.
    """

    def __init__(self, api_key: str = "", config: Optional[dict] = None):
        super().__init__(api_key or "placeholder", config)
        logger.info("Initialized PlaceholderImageProvider (testing mode)")

    async def generate_image(
        self,
        prompt: str,
        width: int = 1920,
        height: int = 1080,
        style: Optional[str] = None
    ) -> bytes:
        """
        Generate a placeholder image with prompt text overlay.
        Uses Pillow to create a simple image locally.

        Args:
            prompt: The image generation prompt (displayed on the image)
            width: Image width
            height: Image height
            style: Ignored in testing mode

        Returns:
            JPEG image bytes with prompt text burned in
        """
        logger.info(f"[TESTING MODE] Placeholder image for prompt: {prompt[:100]}...")

        from PIL import Image, ImageDraw, ImageFont

        # Create image with dark cinematic background
        img = Image.new("RGB", (width, height), color=(30, 30, 40))
        draw = ImageDraw.Draw(img)

        # Try to load a readable font, fall back to default
        try:
            font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
            font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
            font_label = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
        except (OSError, IOError):
            try:
                font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 36)
                font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 22)
                font_label = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 28)
            except (OSError, IOError):
                font_large = ImageFont.load_default()
                font_small = font_large
                font_label = font_large

        # Draw "TESTING MODE" banner at top
        banner_height = 60
        draw.rectangle([(0, 0), (width, banner_height)], fill=(200, 60, 60))
        draw.text(
            (width // 2, banner_height // 2),
            "TESTING MODE - PLACEHOLDER IMAGE",
            fill=(255, 255, 255),
            font=font_large,
            anchor="mm"
        )

        # Draw prompt label
        y_offset = banner_height + 40
        draw.text(
            (40, y_offset),
            "IMAGE PROMPT:",
            fill=(100, 180, 255),
            font=font_label
        )
        y_offset += 45

        # Word-wrap and draw the prompt text
        max_chars_per_line = width // 14  # Approximate chars per line
        words = prompt.split()
        lines = []
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if len(test_line) <= max_chars_per_line:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)

        # Limit to lines that fit on screen
        max_lines = (height - y_offset - 100) // 32
        for i, line in enumerate(lines[:max_lines]):
            draw.text(
                (40, y_offset + i * 32),
                line,
                fill=(220, 220, 220),
                font=font_small
            )

        if len(lines) > max_lines:
            draw.text(
                (40, y_offset + max_lines * 32),
                f"... ({len(lines) - max_lines} more lines)",
                fill=(150, 150, 150),
                font=font_small
            )

        # Draw dimensions info at bottom
        info_text = f"{width}x{height} | Style: {style or 'default'} | Provider: placeholder"
        draw.text(
            (width // 2, height - 30),
            info_text,
            fill=(120, 120, 120),
            font=font_small,
            anchor="mm"
        )

        # Save as JPEG
        output = io.BytesIO()
        img.save(output, format="JPEG", quality=85)
        result_bytes = output.getvalue()

        logger.info(f"[TESTING MODE] Generated placeholder ({len(result_bytes)} bytes)")
        return result_bytes

    async def get_supported_sizes(self) -> list[tuple[int, int]]:
        """Placeholder supports any size."""
        return [
            (1024, 1024),
            (1920, 1080),
            (1080, 1920),
            (1792, 1024),
            (1024, 1792),
        ]

    async def test_connection(self) -> bool:
        """Always available — no external dependency."""
        return True
