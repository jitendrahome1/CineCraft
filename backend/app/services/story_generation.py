"""
Story Generation Service.
Handles AI-powered story generation from user prompts.
"""
from typing import Optional, Dict, Any, List
from sqlalchemy.orm import Session
from datetime import datetime

from app.providers.base.ai_provider import AIProvider
from app.models.project import Project, ProjectStatus
from app.models.scene import Scene
from app.models.character import Character
from app.repositories.project import ProjectRepository
from app.repositories.scene import SceneRepository
from app.repositories.character import CharacterRepository
from app.core.logging import get_logger
from app.core.errors import AIProviderError, ValidationError

logger = get_logger(__name__)


class StoryGenerationService:
    """
    Service for generating stories using AI providers.
    Orchestrates story generation, scene breakdown, and character extraction.
    """

    def __init__(self, db: Session, ai_provider: AIProvider):
        self.db = db
        self.ai_provider = ai_provider
        self.project_repo = ProjectRepository(db)
        self.scene_repo = SceneRepository(db)
        self.character_repo = CharacterRepository(db)

    async def generate_complete_story(
        self,
        project_id: int,
        user_id: int,
        regenerate_scenes: bool = True,
        regenerate_characters: bool = True
    ) -> Dict[str, Any]:
        """
        Generate complete story with scenes and characters.
        3-step flow: 1) Generate cinematic story 2) Extract characters 3) Scene breakdown

        Args:
            project_id: Project ID
            user_id: User ID (for permission check)
            regenerate_scenes: Whether to regenerate scenes
            regenerate_characters: Whether to regenerate characters

        Returns:
            Dict with story, scenes, and characters
        """
        # Get project
        logger.info(f"[STEP 1/7] Fetching project {project_id}")
        project = self.project_repo.get(project_id)
        if not project:
            raise ValidationError(f"Project {project_id} not found")

        if project.user_id != user_id:
            raise ValidationError("You don't have permission to generate story for this project")

        logger.info(f"Project found: '{project.title}'")

        # Update status
        logger.info(f"[STEP 2/7] Updating project status to GENERATING")
        self.project_repo.update_status(project_id, ProjectStatus.GENERATING)

        # Read project settings
        language = getattr(project, 'language', 'english') or 'english'
        video_length = getattr(project, 'video_length', 'short') or 'short'

        try:
            # Step 1: Generate cinematic story (plain text, line-by-line narration)
            logger.info(f"[STEP 3/7] Generating cinematic story (language={language}, video_length={video_length})")
            story = await self._generate_story(project, language, video_length)

            # Save story to project
            logger.info(f"Saving story to database ({len(story)} chars)")
            project.story = story
            project.story_generated_at = datetime.utcnow()
            self.db.commit()
            self.db.refresh(project)

            # Step 2: Extract characters (needed for visual consistency in scenes)
            characters = []
            characters_data = []
            if regenerate_characters:
                logger.info(f"[STEP 4/7] Extracting characters from story")
                # Delete existing characters
                self.character_repo.delete_by_project(project_id)
                characters = await self._extract_and_save_characters(project, story)
                characters_data = [self._character_to_dict(c) for c in characters]
                logger.info(f"Extracted {len(characters)} characters")
            else:
                logger.info(f"[STEP 4/7] Skipping character extraction")
                if project.characters:
                    characters_data = [self._character_to_dict(c) for c in project.characters]

            # Step 3: Generate scene breakdown (with character data for visual consistency)
            scenes = []
            if regenerate_scenes:
                logger.info(f"[STEP 5/7] Generating scene breakdown with character consistency")
                # Delete existing scenes
                self.scene_repo.delete_by_project(project_id)
                scenes = await self._generate_and_save_scenes(
                    project, story, language, video_length, characters_data
                )
                logger.info(f"Generated {len(scenes)} scenes")
            else:
                logger.info(f"[STEP 5/7] Skipping scene generation")

            # Step 4 (new): Generate image prompts for each scene
            if scenes:
                logger.info(f"[STEP 6/7] Generating image prompts for {len(scenes)} scenes")
                await self._generate_image_prompts_for_scenes(scenes)
                logger.info(f"Image prompts generated for all scenes")
            else:
                logger.info(f"[STEP 6/7] Skipping image prompt generation (no scenes)")

            # Update project status
            logger.info(f"[STEP 7/7] Updating project status to READY")
            self.project_repo.update_status(project_id, ProjectStatus.READY)

            result = {
                "project_id": project_id,
                "story": story,
                "story_length": len(story),
                "scenes": [self._scene_to_dict(s) for s in scenes],
                "characters": [self._character_to_dict(c) for c in characters],
                "status": "completed"
            }

            logger.info(f"Generation completed: {len(scenes)} scenes, {len(characters)} characters")
            return result

        except Exception as e:
            logger.exception(f"Story generation failed for project {project_id}")
            self.project_repo.update_status(project_id, ProjectStatus.FAILED)
            raise AIProviderError(f"Story generation failed: {str(e)}")

    async def generate_story_only(
        self,
        project_id: int,
        user_id: int
    ) -> str:
        """
        Generate story text only (no scenes or characters).

        Args:
            project_id: Project ID
            user_id: User ID

        Returns:
            Generated story text

        Raises:
            ValidationError: If project not found or permission denied
            AIProviderError: If generation fails
        """
        project = self.project_repo.get(project_id)
        if not project:
            raise ValidationError(f"Project {project_id} not found")

        if project.user_id != user_id:
            raise ValidationError("You don't have permission to access this project")

        logger.info(f"Generating story for project {project_id}")
        story = await self._generate_story(project)

        # Update project
        project.story = story
        project.story_generated_at = datetime.utcnow()
        self.db.commit()

        logger.info(f"Story generated ({len(story)} chars)")
        return story

    async def regenerate_scenes(
        self,
        project_id: int,
        user_id: int
    ) -> List[Scene]:
        """
        Regenerate scenes from existing story.

        Args:
            project_id: Project ID
            user_id: User ID

        Returns:
            List of generated scenes

        Raises:
            ValidationError: If project not found or has no story
        """
        project = self.project_repo.get(project_id)
        if not project:
            raise ValidationError(f"Project {project_id} not found")

        if project.user_id != user_id:
            raise ValidationError("You don't have permission to access this project")

        if not project.story:
            raise ValidationError("Project has no story. Generate story first.")

        logger.info(f"Regenerating scenes for project {project_id}")

        language = getattr(project, 'language', 'english') or 'english'
        video_length = getattr(project, 'video_length', 'short') or 'short'

        # Get existing characters for consistency
        characters_data = []
        if project.characters:
            characters_data = [self._character_to_dict(c) for c in project.characters]

        # Delete existing scenes
        self.scene_repo.delete_by_project(project_id)

        # Generate new scenes
        scenes = await self._generate_and_save_scenes(
            project, project.story, language, video_length, characters_data
        )

        # Generate image prompts for the new scenes
        if scenes:
            logger.info(f"Generating image prompts for {len(scenes)} regenerated scenes")
            await self._generate_image_prompts_for_scenes(scenes)

        logger.info(f"Regenerated {len(scenes)} scenes")
        return scenes

    async def regenerate_characters(
        self,
        project_id: int,
        user_id: int
    ) -> List[Character]:
        """
        Regenerate characters from existing story.

        Args:
            project_id: Project ID
            user_id: User ID

        Returns:
            List of extracted characters

        Raises:
            ValidationError: If project not found or has no story
        """
        project = self.project_repo.get(project_id)
        if not project:
            raise ValidationError(f"Project {project_id} not found")

        if project.user_id != user_id:
            raise ValidationError("You don't have permission to access this project")

        if not project.story:
            raise ValidationError("Project has no story. Generate story first.")

        logger.info(f"Regenerating characters for project {project_id}")

        # Delete existing characters
        self.character_repo.delete_by_project(project_id)

        # Generate new characters
        characters = await self._extract_and_save_characters(project, project.story)

        logger.info(f"Regenerated {len(characters)} characters")
        return characters

    async def _generate_story(
        self,
        project: Project,
        language: str = "english",
        video_length: str = "short"
    ) -> str:
        """
        Generate story using AI provider.

        Args:
            project: Project instance
            language: Language for generation
            video_length: Video length setting

        Returns:
            Generated story text
        """
        title = project.title
        context = project.story_prompt or project.description

        story = await self.ai_provider.generate_story(
            title=title,
            context=context,
            language=language,
            video_length=video_length
        )

        return story

    async def _generate_and_save_scenes(
        self,
        project: Project,
        story: str,
        language: str = "english",
        video_length: str = "short",
        characters_data: Optional[List[Dict[str, Any]]] = None
    ) -> List[Scene]:
        """
        Generate scenes and save to database.

        Args:
            project: Project instance
            story: Story text
            language: Language for generation
            video_length: Video length setting
            characters_data: Optional character data for visual consistency

        Returns:
            List of created scenes
        """
        # Generate scene breakdown
        scenes_data = await self.ai_provider.generate_scene_breakdown(
            story,
            language=language,
            video_length=video_length,
            characters=characters_data
        )

        # Create scene objects
        scenes = []
        for scene_data in scenes_data:
            scene = Scene(
                project_id=project.id,
                sequence_number=scene_data.get("scene_number", len(scenes) + 1),
                title=scene_data.get("title"),
                description=scene_data.get("description", ""),
                narration=scene_data.get("narration"),
                visual_description=scene_data.get("visual_prompt") or scene_data.get("visual_description"),
                video_prompt=scene_data.get("video_prompt"),
                emotion=scene_data.get("emotion"),
                duration=float(scene_data.get("duration", 10)),
                metadata=scene_data.get("metadata", {})
            )
            self.db.add(scene)
            scenes.append(scene)

        self.db.commit()

        # Update project timestamp
        project.scenes_generated_at = datetime.utcnow()
        self.db.commit()

        return scenes

    async def _generate_image_prompts_for_scenes(
        self,
        scenes: List[Scene]
    ) -> None:
        """
        Generate image prompts for each scene using AI provider.
        Each scene gets a visual_description based on its narration
        and the previous scene's narration for continuity.

        Args:
            scenes: List of Scene objects (must have narration set)
        """
        sorted_scenes = sorted(scenes, key=lambda s: s.sequence_number)

        for i, scene in enumerate(sorted_scenes):
            if not scene.narration:
                continue

            previous_narration = None
            if i > 0 and sorted_scenes[i - 1].narration:
                previous_narration = sorted_scenes[i - 1].narration

            logger.info(f"Generating image prompt for scene {scene.sequence_number}")
            visual_prompt = await self.ai_provider.generate_image_prompt(
                narration=scene.narration,
                previous_narration=previous_narration
            )

            scene.visual_description = visual_prompt

        self.db.commit()

    async def _extract_and_save_characters(
        self,
        project: Project,
        story: str
    ) -> List[Character]:
        """
        Extract characters and save to database.

        Args:
            project: Project instance
            story: Story text

        Returns:
            List of created characters
        """
        # Extract characters
        characters_data = await self.ai_provider.extract_characters(story)

        # Create character objects
        characters = []
        for char_data in characters_data:
            character = Character(
                project_id=project.id,
                name=char_data.get("name", "Unknown"),
                role=char_data.get("role"),
                description=char_data.get("description") or char_data.get("style_reference"),
                appearance=char_data.get("appearance"),
                personality=char_data.get("personality"),
                metadata={
                    "age": char_data.get("age"),
                    "clothing": char_data.get("clothing"),
                    "style_reference": char_data.get("style_reference"),
                    **(char_data.get("metadata") or {})
                }
            )
            self.db.add(character)
            characters.append(character)

        self.db.commit()

        return characters

    def _scene_to_dict(self, scene: Scene) -> Dict[str, Any]:
        """Convert scene to dict for response."""
        return {
            "id": scene.id,
            "sequence_number": scene.sequence_number,
            "title": scene.title,
            "description": scene.description,
            "narration": scene.narration,
            "visual_description": scene.visual_description,
            "video_prompt": scene.video_prompt,
            "emotion": scene.emotion,
            "duration": scene.duration,
            "metadata": scene.metadata
        }

    def _character_to_dict(self, character: Character) -> Dict[str, Any]:
        """Convert character to dict for response."""
        metadata = character.metadata or {}
        return {
            "id": character.id,
            "name": character.name,
            "role": character.role,
            "description": character.description,
            "appearance": character.appearance,
            "clothing": metadata.get("clothing", ""),
            "style_reference": metadata.get("style_reference", ""),
            "personality": character.personality,
            "metadata": metadata
        }
