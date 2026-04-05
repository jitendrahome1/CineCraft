"""
Base abstract class for all AI providers.
Implements Strategy Pattern for swappable AI providers.
"""
from abc import ABC, abstractmethod
from typing import Optional, Any


class AIProvider(ABC):
    """
    Abstract base class for AI text generation providers.
    All AI providers must implement these methods.
    """

    def __init__(self, api_key: str, config: Optional[dict[str, Any]] = None):
        """
        Initialize AI provider.

        Args:
            api_key: API key for the provider
            config: Optional configuration dict
        """
        self.api_key = api_key
        self.config = config or {}

    @abstractmethod
    async def generate_story(
        self,
        title: str,
        context: Optional[str] = None,
        language: str = "english",
        video_length: str = "short"
    ) -> str:
        """
        Generate a complete story from a title.

        Args:
            title: Story title
            context: Optional additional context
            language: Language for generation ('english' or 'hindi')
            video_length: Video length ('short' or 'long')

        Returns:
            Generated story text
        """
        pass

    @abstractmethod
    async def generate_scene_breakdown(
        self,
        story: str,
        language: str = "english",
        video_length: str = "short",
        characters: Optional[list[dict[str, Any]]] = None
    ) -> list[dict[str, Any]]:
        """
        Break story into scenes with descriptions.

        Args:
            story: Full story text
            language: Language for generation ('english' or 'hindi')
            video_length: Video length ('short' or 'long')
            characters: Optional character list for visual consistency

        Returns:
            List of scene dictionaries with keys:
                - scene_number: int
                - title: str
                - description: str
                - narration: str
                - visual_prompt: str
                - video_prompt: str
                - emotion: str
                - duration: int (seconds)
        """
        pass

    @abstractmethod
    async def generate_image_prompt(
        self,
        narration: str,
        previous_narration: Optional[str] = None
    ) -> str:
        """
        Generate a detailed image prompt for a single scene.

        Args:
            narration: Scene narration text
            previous_narration: Optional previous scene narration for continuity

        Returns:
            A detailed visual prompt string for image generation
        """
        pass

    @abstractmethod
    async def extract_characters(
        self,
        story: str
    ) -> list[dict[str, Any]]:
        """
        Extract character descriptions from story.

        Args:
            story: Full story text

        Returns:
            List of character dictionaries with keys:
                - name: str
                - description: str
                - appearance: str
                - personality: str
        """
        pass

