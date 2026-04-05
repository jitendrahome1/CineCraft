"""
Media generation API endpoints.
Supports two modes controlled by APP_MODE environment variable:
  - testing:    Placeholder images (zero cost, instant, prompt visible on image)
  - production: Real AI images via OpenAI gpt-image-1

In testing mode, TESTING_REAL_IMAGE_LIMIT controls how many scenes
get real AI images (e.g., first 2). The rest get placeholders.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional
import os
import asyncio

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.repositories.scene import SceneRepository
from app.repositories.media_asset import MediaAssetRepository
from app.repositories.project import ProjectRepository
from app.models.media_asset import MediaType
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


def _get_providers_for_mode():
    """
    Get image providers based on APP_MODE.

    Returns:
        (production_provider, placeholder_provider, is_testing, real_image_limit)
    """
    from app.providers.image.factory import (
        get_image_provider_from_config,
        ImageProviderFactory,
        is_testing_mode,
        get_testing_real_image_limit,
    )
    from app.core.config import settings

    testing = is_testing_mode()
    real_limit = get_testing_real_image_limit() if testing else 0

    # Placeholder provider (always available, zero cost)
    placeholder = ImageProviderFactory.create("placeholder", "placeholder")

    # Production provider (only needed in production or for real tests)
    # real_limit: 0 = all placeholders, >0 = first N real, -1 = all real
    production = None
    if not testing or real_limit != 0:
        try:
            production = get_image_provider_from_config()
        except Exception as e:
            if not testing:
                # In production mode, primary provider is required
                raise
            logger.warning(
                f"[TESTING] Could not load production provider for real test: {e}. "
                f"All scenes will use placeholders."
            )

    return production, placeholder, testing, real_limit


@router.post("/projects/{project_id}/generate-placeholder-media")
async def generate_placeholder_media(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate images for all scenes in a project.

    Behavior depends on APP_MODE:
    - testing:    Returns placeholder images with prompt text overlay.
                  Optionally generates real images for the first N scenes
                  (controlled by TESTING_REAL_IMAGE_LIMIT).
    - production: Generates real AI images via OpenAI gpt-image-1 for all scenes.
    """
    # Check project ownership
    project_repo = ProjectRepository(db)
    project = project_repo.get(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )

    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access to project"
        )

    # Get all scenes
    scene_repo = SceneRepository(db)
    scenes = scene_repo.get_by_project(project_id)

    if not scenes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project has no scenes. Generate story first."
        )

    # Determine mode and providers
    try:
        production_provider, placeholder_provider, is_testing, real_limit = _get_providers_for_mode()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Image provider not available: {str(e)}"
        )

    mode_label = "TESTING" if is_testing else "PRODUCTION"
    logger.info(
        f"[{mode_label}] Generating images for project {project_id} "
        f"({len(scenes)} scenes, real_limit={real_limit if is_testing else 'all'})"
    )

    # Generate images for each scene
    asset_repo = MediaAssetRepository(db)
    storage_path = os.path.join("storage", "media", f"project_{project_id}")
    os.makedirs(storage_path, exist_ok=True)

    generated_assets = []
    real_images_generated = 0

    for scene in scenes:
        # Check if scene already has an image
        existing_images = asset_repo.get_by_scene(scene.id, media_type=MediaType.IMAGE)
        if existing_images:
            logger.info(f"Scene {scene.id} already has image, skipping")
            generated_assets.append({
                "scene_id": scene.id,
                "asset_id": existing_images[0].id,
                "status": "exists",
                "mode": mode_label.lower()
            })
            continue

        # Build prompt from scene visual description
        prompt = (
            scene.visual_description
            or scene.narration
            or f"Scene {scene.sequence_number}: {scene.title or 'A cinematic scene'}"
        )

        # Always log the prompt for debugging
        logger.info(
            f"[{mode_label}] Scene {scene.id} (seq={scene.sequence_number}) prompt: {prompt[:150]}..."
        )

        # Decide: real AI image or placeholder?
        # real_limit: 0 = all placeholders, >0 = first N real, -1 = all real
        use_real = False
        if not is_testing:
            # Production: always use real AI
            use_real = True
        elif real_limit == -1 and production_provider:
            # Testing with all real images
            use_real = True
        elif real_limit > 0 and real_images_generated < real_limit and production_provider:
            # Testing with limited real images
            use_real = True

        image_bytes = None
        provider_used = "unknown"

        if use_real:
            # --- Real AI image generation ---
            try:
                image_bytes = await production_provider.generate_image(
                    prompt=prompt,
                    width=1920,
                    height=1080,
                    style="cinematic"
                )
                provider_used = production_provider.__class__.__name__.replace("Provider", "").replace("Image", "").lower()
                if not provider_used:
                    provider_used = "ai"
                real_images_generated += 1
                logger.info(
                    f"[{mode_label}] Real AI image generated for scene {scene.id} "
                    f"(provider={provider_used}, {real_images_generated}/{real_limit if is_testing else 'all'})"
                )
            except Exception as e:
                logger.error(f"[{mode_label}] Real image generation failed for scene {scene.id}: {e}")
                # Fall back to placeholder in both testing and production
                logger.info(f"[{mode_label}] Falling back to placeholder for scene {scene.id}")

        if image_bytes is None:
            # --- Placeholder image ---
            try:
                image_bytes = await placeholder_provider.generate_image(
                    prompt=prompt,
                    width=1920,
                    height=1080,
                    style="cinematic"
                )
                provider_used = "placeholder"
                logger.info(f"[{mode_label}] Placeholder image generated for scene {scene.id}")
            except Exception as e:
                logger.error(f"Placeholder generation failed for scene {scene.id}: {e}")
                generated_assets.append({
                    "scene_id": scene.id,
                    "status": "failed",
                    "error": str(e),
                    "mode": mode_label.lower()
                })
                continue

        # Save image to disk
        try:
            image_filename = f"scene_{scene.id}_ai.jpg"
            image_path = os.path.join(storage_path, image_filename)

            with open(image_path, 'wb') as f:
                f.write(image_bytes)

            logger.info(f"Saved image to {image_path} ({len(image_bytes)} bytes, provider: {provider_used})")

            # Create media asset record
            relative_path = f"media/project_{project_id}/{image_filename}"
            is_ai_generated = provider_used not in ("placeholder", "unsplash", "unsplash_fallback")

            asset_data = {
                "user_id": current_user.id,
                "project_id": project_id,
                "scene_id": scene.id,
                "filename": image_filename,
                "original_filename": image_filename,
                "file_path": relative_path,
                "file_size": os.path.getsize(image_path),
                "mime_type": "image/jpeg",
                "media_type": MediaType.IMAGE.value,
                "storage_provider": "local",
                "url": f"/storage/media/project_{project_id}/{image_filename}",
                "width": 1920,
                "height": 1080,
                "media_metadata": {
                    "type": "ai_generated" if is_ai_generated else "placeholder",
                    "generator": provider_used,
                    "scene_number": scene.sequence_number,
                    "format": "jpeg",
                    "resolution": "1920x1080",
                    "app_mode": mode_label.lower()
                },
                "is_generated": 1 if is_ai_generated else 0,
                "generation_provider": provider_used,
                "generation_prompt": prompt
            }

            asset = asset_repo.create(asset_data)
            logger.info(f"Created media asset {asset.id} for scene {scene.id}")

            # Update scene with image URL
            scene.image_url = asset.url
            db.commit()

            generated_assets.append({
                "scene_id": scene.id,
                "asset_id": asset.id,
                "status": "generated",
                "provider": provider_used,
                "prompt": prompt[:200],
                "mode": mode_label.lower()
            })

            # Cooldown between AI image requests to respect rate limits
            if provider_used not in ("placeholder",) and scene != scenes[-1]:
                cooldown = 10  # seconds between requests
                logger.info(f"Waiting {cooldown}s cooldown before next image request...")
                await asyncio.sleep(cooldown)

        except Exception as e:
            logger.error(f"Failed to save image for scene {scene.id}: {e}")
            generated_assets.append({
                "scene_id": scene.id,
                "status": "failed",
                "error": str(e),
                "mode": mode_label.lower()
            })

    # Summary
    generated_count = len([a for a in generated_assets if a["status"] == "generated"])
    failed_count = len([a for a in generated_assets if a["status"] == "failed"])
    existing_count = len([a for a in generated_assets if a["status"] == "exists"])
    real_count = len([a for a in generated_assets if a.get("provider") not in (None, "placeholder")])
    placeholder_count = len([a for a in generated_assets if a.get("provider") == "placeholder"])

    logger.info(
        f"[{mode_label}] Image generation complete: "
        f"{generated_count} generated ({real_count} real, {placeholder_count} placeholder), "
        f"{existing_count} existing, {failed_count} failed"
    )

    return {
        "project_id": project_id,
        "app_mode": mode_label.lower(),
        "scenes_count": len(scenes),
        "generated_count": generated_count,
        "real_ai_count": real_count,
        "placeholder_count": placeholder_count,
        "existing_count": existing_count,
        "failed_count": failed_count,
        "assets": generated_assets,
        "message": (
            f"[{mode_label}] Images: {generated_count} generated "
            f"({real_count} real AI, {placeholder_count} placeholder), "
            f"{failed_count} failed."
        )
    }


@router.post("/projects/{project_id}/generate-voice")
async def generate_voice_narrations(
    project_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Generate voice narration for all scenes in a project.
    Uses ElevenLabs if API key is configured, falls back to gTTS (free).
    """
    logger.info(f"Generating voice narrations for project {project_id}")

    # Check project ownership
    project_repo = ProjectRepository(db)
    project = project_repo.get(project_id)

    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found"
        )

    if project.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access to project"
        )

    # Get all scenes
    scene_repo = SceneRepository(db)
    scenes = scene_repo.get_by_project(project_id)

    if not scenes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project has no scenes. Generate story first."
        )

    # Get voice provider
    from app.providers.voice.factory import get_voice_provider_from_config

    try:
        # Pass language from project to configure gTTS language
        voice_config = {"language": project.language or "english"}
        voice_provider = get_voice_provider_from_config(config=voice_config)
    except Exception as e:
        logger.error(f"Failed to initialize voice provider: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Voice provider not available: {str(e)}"
        )

    # Generate voice for each scene
    asset_repo = MediaAssetRepository(db)
    storage_path = os.path.join("storage", "media", f"project_{project_id}")
    os.makedirs(storage_path, exist_ok=True)

    generated_assets = []

    # Determine language code for TTS
    lang_map = {"english": "en", "hindi": "hi"}
    lang_code = lang_map.get(project.language or "english", "en")

    for scene in scenes:
        # Check if scene already has voice
        existing_voice = asset_repo.get_by_scene(scene.id, media_type=MediaType.AUDIO)
        if existing_voice:
            logger.info(f"Scene {scene.id} already has voice, skipping")
            generated_assets.append({
                "scene_id": scene.id,
                "asset_id": existing_voice[0].id,
                "status": "exists"
            })
            continue

        # Get narration text
        narration = scene.narration
        if not narration:
            logger.warning(f"Scene {scene.id} has no narration text, skipping")
            generated_assets.append({
                "scene_id": scene.id,
                "status": "skipped",
                "reason": "no narration text"
            })
            continue

        try:
            logger.info(f"Generating voice for scene {scene.id} ({len(narration)} chars)")

            # Generate speech audio
            audio_bytes = await voice_provider.generate_speech(
                text=narration,
                voice_id=lang_code,
                speed=1.0
            )

            # Save audio file
            audio_filename = f"scene_{scene.id}_voice.mp3"
            audio_path = os.path.join(storage_path, audio_filename)

            with open(audio_path, 'wb') as f:
                f.write(audio_bytes)

            logger.info(f"Saved voice to {audio_path} ({len(audio_bytes)} bytes)")

            # Create media asset record
            provider_name = voice_provider.__class__.__name__.replace("Provider", "").lower()
            relative_audio_path = f"media/project_{project_id}/{audio_filename}"
            asset_data = {
                "user_id": current_user.id,
                "project_id": project_id,
                "scene_id": scene.id,
                "filename": audio_filename,
                "original_filename": audio_filename,
                "file_path": relative_audio_path,
                "file_size": os.path.getsize(audio_path),
                "mime_type": "audio/mpeg",
                "media_type": MediaType.AUDIO.value,
                "storage_provider": "local",
                "url": f"/storage/media/project_{project_id}/{audio_filename}",
                "media_metadata": {
                    "type": "ai_generated",
                    "generator": provider_name,
                    "scene_number": scene.sequence_number,
                    "format": "mp3",
                    "language": project.language or "english",
                    "character_count": len(narration)
                },
                "is_generated": 1,
                "generation_provider": provider_name,
                "generation_prompt": narration[:500]
            }

            asset = asset_repo.create(asset_data)
            logger.info(f"Created voice asset {asset.id} for scene {scene.id}")

            # Update scene with voice URL
            scene.voice_url = asset.url
            scene.audio_url = asset.url
            db.commit()

            generated_assets.append({
                "scene_id": scene.id,
                "asset_id": asset.id,
                "status": "generated",
                "provider": provider_name
            })

        except Exception as e:
            logger.error(f"Failed to generate voice for scene {scene.id}: {e}")
            generated_assets.append({
                "scene_id": scene.id,
                "status": "failed",
                "error": str(e)
            })

    generated_count = len([a for a in generated_assets if a["status"] == "generated"])
    failed_count = len([a for a in generated_assets if a["status"] == "failed"])
    skipped_count = len([a for a in generated_assets if a["status"] == "skipped"])

    logger.info(f"Voice generation complete: {generated_count} generated, {failed_count} failed, {skipped_count} skipped")

    return {
        "project_id": project_id,
        "scenes_count": len(scenes),
        "generated_count": generated_count,
        "existing_count": len([a for a in generated_assets if a["status"] == "exists"]),
        "skipped_count": skipped_count,
        "failed_count": failed_count,
        "assets": generated_assets,
        "message": f"Voice narrations: {generated_count} created, {failed_count} failed, {skipped_count} skipped."
    }
