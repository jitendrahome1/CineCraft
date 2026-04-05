"""
OpenRouter AI provider implementation.
Provides unified access to multiple AI models through OpenRouter API.
"""
from typing import Optional, Any
import json
from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from app.providers.base.ai_provider import AIProvider
from app.providers.ai.prompts import (
    build_documentary_story_prompt,
    build_documentary_scene_prompt,
    build_documentary_character_prompt,
    build_image_prompt_generation_prompt,
)
from app.core.logging import get_logger
from app.core.errors import AIProviderError

logger = get_logger(__name__)


class OpenRouterProvider(AIProvider):
    """
    OpenRouter implementation of AIProvider.
    Provides unified access to multiple AI models (Claude, GPT-4, Gemini, etc).
    """

    def __init__(self, api_key: str, config: Optional[dict[str, Any]] = None):
        super().__init__(api_key, config)

        # Configuration
        config = config or {}
        self.base_url = config.get("base_url", "https://openrouter.ai/api/v1")
        self.story_model = config.get("story_model", "anthropic/claude-3.5-sonnet")
        self.scene_model = config.get("scene_model", "anthropic/claude-3.5-sonnet")
        self.character_model = config.get("character_model", "anthropic/claude-3.5-sonnet")
        self.max_tokens = config.get("max_tokens", 4096)
        self.temperature = config.get("temperature", 1.0)

        # Initialize OpenAI client (OpenRouter is OpenAI-compatible)
        # Use only basic headers to match curl command format
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=self.base_url
        )

    async def generate_story(
        self,
        title: str,
        context: Optional[str] = None,
        language: str = "english",
        video_length: str = "short"
    ) -> str:
        """
        Generate a documentary-style story from a title using OpenRouter.

        Args:
            title: Story title
            context: Optional additional context
            language: Language for generation ('english' or 'hindi')
            video_length: Video length ('short' or 'long')

        Returns:
            Generated story text

        Raises:
            AIProviderError: If generation fails
        """
        try:
            prompt = build_documentary_story_prompt(title, context, language, video_length)

            logger.info(f"Generating story for title: {title} using model: {self.story_model}")

            response = await self.client.chat.completions.create(
                model=self.story_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=self.max_tokens,
                temperature=1.0  # Creative for story generation
            )

            story = response.choices[0].message.content
            logger.info(f"Story generated successfully ({len(story)} chars)")
            return story

        except Exception as e:
            logger.exception(f"Error generating story: {str(e)}")
            raise AIProviderError(f"Failed to generate story: {str(e)}")

    async def generate_scene_breakdown(
        self,
        story: str,
        language: str = "english",
        video_length: str = "short",
        characters: Optional[list[dict[str, Any]]] = None
    ) -> list[dict[str, Any]]:
        """
        Break story into scenes with descriptions using OpenRouter.

        Args:
            story: Full story text
            language: Language for generation
            video_length: Video length
            characters: Optional character list for visual consistency

        Returns:
            List of scene dictionaries

        Raises:
            AIProviderError: If generation fails
        """
        try:
            prompt = build_documentary_scene_prompt(story, language, video_length, characters)

            logger.info(f"Generating scene breakdown using model: {self.scene_model}")

            response = await self.client.chat.completions.create(
                model=self.scene_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=8192,
                temperature=0.7  # Balanced for structured output
            )

            # Parse JSON response — new format is {"scenes": [...]}
            scenes_json = response.choices[0].message.content
            parsed = self._parse_json_response(scenes_json)
            if isinstance(parsed, dict) and "scenes" in parsed:
                scenes = parsed["scenes"]
            elif isinstance(parsed, list):
                scenes = parsed
            else:
                scenes = parsed

            logger.info(f"Generated {len(scenes)} scenes")
            return scenes

        except Exception as e:
            logger.exception(f"Error generating scene breakdown: {str(e)}")
            raise AIProviderError(f"Failed to generate scene breakdown: {str(e)}")

    async def generate_image_prompt(
        self,
        narration: str,
        previous_narration: Optional[str] = None
    ) -> str:
        """
        Generate a detailed image prompt for a scene using OpenRouter.

        Args:
            narration: Scene narration text
            previous_narration: Optional previous scene narration for continuity

        Returns:
            A detailed visual prompt string

        Raises:
            AIProviderError: If generation fails
        """
        try:
            prompt = build_image_prompt_generation_prompt(narration, previous_narration)

            logger.info("Generating image prompt for scene")

            response = await self.client.chat.completions.create(
                model=self.scene_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=1024,
                temperature=0.7
            )

            result_json = response.choices[0].message.content
            parsed = self._parse_json_response(result_json)

            if isinstance(parsed, dict) and "visual_prompt" in parsed:
                visual_prompt = parsed["visual_prompt"]
            else:
                visual_prompt = str(parsed)

            logger.info(f"Image prompt generated ({len(visual_prompt)} chars)")
            return visual_prompt

        except Exception as e:
            logger.exception(f"Error generating image prompt: {str(e)}")
            raise AIProviderError(f"Failed to generate image prompt: {str(e)}")

    async def extract_characters(
        self,
        story: str
    ) -> list[dict[str, Any]]:
        """
        Extract character descriptions from story using OpenRouter.

        Args:
            story: Full story text

        Returns:
            List of character dictionaries

        Raises:
            AIProviderError: If extraction fails
        """
        try:
            prompt = build_documentary_character_prompt(story)

            logger.info(f"Extracting characters using model: {self.character_model}")

            response = await self.client.chat.completions.create(
                model=self.character_model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=2048,
                temperature=0.5  # Precise for extraction
            )

            # Parse JSON response
            characters_json = response.choices[0].message.content
            characters = self._parse_json_response(characters_json)

            logger.info(f"Extracted {len(characters)} characters")
            return characters

        except Exception as e:
            logger.exception(f"Error extracting characters: {str(e)}")
            raise AIProviderError(f"Failed to extract characters: {str(e)}")

    def _parse_json_response(self, response_text: str) -> Any:
        """
        Parse JSON from model response.
        Handles preamble text, markdown code blocks, and other wrapping.
        Returns parsed JSON (list or dict).
        """
        try:
            text = response_text.strip()

            # Remove markdown code blocks if present
            if "```json" in text:
                text = text.split("```json", 1)[1]
                if "```" in text:
                    text = text.split("```", 1)[0]
            elif "```" in text:
                parts = text.split("```")
                if len(parts) >= 3:
                    text = parts[1]
                elif len(parts) == 2:
                    text = parts[1] if parts[1].strip().startswith(("[", "{")) else parts[0]

            text = text.strip()

            # Try direct parse first
            try:
                data = json.loads(text)
                if isinstance(data, (list, dict)):
                    return data
            except json.JSONDecodeError:
                pass

            # Find JSON object or array in the text
            brace_start = text.find("{")
            bracket_start = text.find("[")

            # Try object first if it appears before array
            if brace_start != -1 and (bracket_start == -1 or brace_start < bracket_start):
                brace_end = text.rfind("}")
                if brace_end > brace_start:
                    json_text = text[brace_start:brace_end + 1]
                    data = json.loads(json_text)
                    if isinstance(data, dict):
                        return data

            # Try array
            if bracket_start != -1:
                bracket_end = text.rfind("]")
                if bracket_end > bracket_start:
                    json_text = text[bracket_start:bracket_end + 1]
                    data = json.loads(json_text)
                    if isinstance(data, list):
                        return data

            raise ValueError("Could not find valid JSON in response")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {response_text[:300]}")
            raise AIProviderError(f"Invalid JSON response from AI: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing response: {str(e)}")
            raise AIProviderError(f"Failed to parse AI response: {str(e)}")

    async def test_connection(self) -> bool:
        """
        Test connection to OpenRouter API.

        Returns:
            True if connection successful
        """
        try:
            response = await self.client.chat.completions.create(
                model=self.story_model,
                messages=[
                    {"role": "user", "content": "Hello"}
                ],
                max_tokens=10
            )
            logger.info(f"OpenRouter connection test successful with model: {self.story_model}")
            return True
        except Exception as e:
            logger.error(f"OpenRouter connection test failed: {str(e)}")
            return False
