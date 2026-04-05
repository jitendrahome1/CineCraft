"""
AI Generation API endpoints.
Handles story generation, scene breakdown, and character extraction.
"""
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.services.story_generation import StoryGenerationService
from app.services.ai_orchestration import AIOrchestrationService
from app.schemas.ai import (
    GenerateStoryRequest,
    GenerateStoryResponse,
    StoryOnlyRequest,
    StoryOnlyResponse,
    RegenerateScenesRequest,
    RegenerateScenesResponse,
    RegenerateCharactersRequest,
    RegenerateCharactersResponse,
    GenerateProjectContentRequest,
    GenerateProjectContentResponse,
    ProviderTestResponse,
    ProviderInfoResponse
)
from app.core.errors import ValidationError, AIProviderError
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


async def get_ai_orchestration_service(db: Session = Depends(get_db)) -> AIOrchestrationService:
    """
    Dependency to get AI orchestration service with providers.

    Args:
        db: Database session

    Returns:
        AI orchestration service
    """
    from app.core.providers import get_provider_manager

    provider_manager = get_provider_manager()

    try:
        ai_provider = provider_manager.get_ai_provider()
    except Exception as e:
        logger.error(f"Failed to get AI provider: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service not available. Please check configuration."
        )

    # Get optional providers (stubs for now)
    try:
        image_provider = provider_manager.get_image_provider()
    except Exception:
        image_provider = None

    try:
        voice_provider = provider_manager.get_voice_provider()
    except Exception:
        voice_provider = None

    try:
        music_provider = provider_manager.get_music_provider()
    except Exception:
        music_provider = None

    return AIOrchestrationService(
        db=db,
        ai_provider=ai_provider,
        image_provider=image_provider,
        voice_provider=voice_provider,
        music_provider=music_provider
    )


@router.post("/generate-story", response_model=GenerateStoryResponse)
async def generate_story(
    request: GenerateStoryRequest,
    current_user: User = Depends(get_current_user),
    ai_service: AIOrchestrationService = Depends(get_ai_orchestration_service)
):
    """
    Generate complete story with scenes and characters.

    Args:
        request: Generation request
        current_user: Current user
        ai_service: AI orchestration service

    Returns:
        Generated story with scenes and characters

    Raises:
        HTTPException: If generation fails
    """
    logger.info(f"🚀 Starting story generation for project {request.project_id}")
    try:
        logger.info(f"📝 Calling AI service to generate complete story...")
        result = await ai_service.story_service.generate_complete_story(
            project_id=request.project_id,
            user_id=current_user.id,
            regenerate_scenes=request.regenerate_scenes,
            regenerate_characters=request.regenerate_characters
        )

        logger.info(f"✅ Story generation completed successfully for project {request.project_id}")
        logger.info(f"📊 Result keys: {list(result.keys())}")
        logger.info(f"📏 Story length: {len(result.get('story', ''))} chars")
        logger.info(f"🎬 Scenes: {len(result.get('scenes', []))}")
        logger.info(f"👥 Characters: {len(result.get('characters', []))}")

        return GenerateStoryResponse(**result)

    except ValidationError as e:
        logger.error(f"❌ Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AIProviderError as e:
        logger.error(f"❌ AI Provider error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )
    except Exception as e:
        logger.exception(f"❌ Unexpected error during story generation: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate story: {str(e)}"
        )


@router.post("/generate-story-only", response_model=StoryOnlyResponse)
async def generate_story_only(
    request: StoryOnlyRequest,
    current_user: User = Depends(get_current_user),
    ai_service: AIOrchestrationService = Depends(get_ai_orchestration_service)
):
    """
    Generate story text only (no scenes or characters).

    Args:
        request: Generation request
        current_user: Current user
        ai_service: AI orchestration service

    Returns:
        Generated story text

    Raises:
        HTTPException: If generation fails
    """
    try:
        story = await ai_service.story_service.generate_story_only(
            project_id=request.project_id,
            user_id=current_user.id
        )

        return StoryOnlyResponse(
            project_id=request.project_id,
            story=story,
            story_length=len(story)
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AIProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/regenerate-scenes", response_model=RegenerateScenesResponse)
async def regenerate_scenes(
    request: RegenerateScenesRequest,
    current_user: User = Depends(get_current_user),
    ai_service: AIOrchestrationService = Depends(get_ai_orchestration_service)
):
    """
    Regenerate scenes from existing story.

    Args:
        request: Regeneration request
        current_user: Current user
        ai_service: AI orchestration service

    Returns:
        Generated scenes

    Raises:
        HTTPException: If generation fails
    """
    try:
        scenes = await ai_service.story_service.regenerate_scenes(
            project_id=request.project_id,
            user_id=current_user.id
        )

        scenes_data = [ai_service.story_service._scene_to_dict(s) for s in scenes]

        return RegenerateScenesResponse(
            project_id=request.project_id,
            scenes=scenes_data,
            total=len(scenes_data)
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AIProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/regenerate-characters", response_model=RegenerateCharactersResponse)
async def regenerate_characters(
    request: RegenerateCharactersRequest,
    current_user: User = Depends(get_current_user),
    ai_service: AIOrchestrationService = Depends(get_ai_orchestration_service)
):
    """
    Regenerate characters from existing story.

    Args:
        request: Regeneration request
        current_user: Current user
        ai_service: AI orchestration service

    Returns:
        Extracted characters

    Raises:
        HTTPException: If extraction fails
    """
    try:
        characters = await ai_service.story_service.regenerate_characters(
            project_id=request.project_id,
            user_id=current_user.id
        )

        characters_data = [ai_service.story_service._character_to_dict(c) for c in characters]

        return RegenerateCharactersResponse(
            project_id=request.project_id,
            characters=characters_data,
            total=len(characters_data)
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AIProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.post("/generate-content", response_model=GenerateProjectContentResponse)
async def generate_project_content(
    request: GenerateProjectContentRequest,
    current_user: User = Depends(get_current_user),
    ai_service: AIOrchestrationService = Depends(get_ai_orchestration_service)
):
    """
    Generate all content for a project.

    This endpoint orchestrates generation of story, scenes, characters,
    and optionally images, audio, and music (Phase 7).

    Args:
        request: Content generation request
        current_user: Current user
        ai_service: AI orchestration service

    Returns:
        All generated content

    Raises:
        HTTPException: If generation fails
    """
    try:
        result = await ai_service.generate_project_content(
            project_id=request.project_id,
            user_id=current_user.id,
            include_story=request.include_story,
            include_scenes=request.include_scenes,
            include_characters=request.include_characters,
            include_images=request.include_images,
            include_audio=request.include_audio,
            include_music=request.include_music
        )

        return GenerateProjectContentResponse(**result)

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except AIProviderError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


@router.get("/providers/test", response_model=ProviderTestResponse)
async def test_providers(
    ai_service: AIOrchestrationService = Depends(get_ai_orchestration_service)
):
    """
    Test connections to all AI providers.

    Returns:
        Connection test results for each provider
    """
    try:
        results = await ai_service.test_providers()
        return ProviderTestResponse(**results)

    except Exception as e:
        logger.exception("Provider test failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Provider test failed: {str(e)}"
        )


@router.get("/providers/info", response_model=ProviderInfoResponse)
async def get_providers_info(
    ai_service: AIOrchestrationService = Depends(get_ai_orchestration_service)
):
    """
    Get information about configured providers.

    Returns:
        Provider configuration information
    """
    info = ai_service.get_provider_info()
    return ProviderInfoResponse(**info)
