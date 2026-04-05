"""
Video rendering service for CineCraft.
Orchestrates the complete video pipeline: images → video → audio → subtitles.
"""
from typing import List, Optional, Dict, Any
from pathlib import Path
import os
from datetime import datetime
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.logging import get_logger
from app.core.errors import CineCraftException
from app.repositories.project import ProjectRepository
from app.repositories.scene import SceneRepository
from app.repositories.media_asset import MediaAssetRepository
from app.repositories.render_job import RenderJobRepository
from app.models.media_asset import MediaType
from app.models.render_job import JobStatus
from app.utils.video import (
    create_video_from_images,
    mix_audio,
    add_subtitles,
    get_audio_duration,
    FFmpegError
)
from app.utils.subtitle import (
    generate_scene_subtitles,
    create_srt_file
)
from app.services.storage import StorageService

logger = get_logger(__name__)


class RenderingService:
    """Service for rendering complete videos from project assets."""

    def __init__(self, db: Session):
        self.db = db
        self.project_repo = ProjectRepository(db)
        self.scene_repo = SceneRepository(db)
        self.asset_repo = MediaAssetRepository(db)
        self.job_repo = RenderJobRepository(db)
        self.storage_service = StorageService(db)

    async def render_project_video(
        self,
        project_id: int,
        user_id: int,
        job_id: int,
        width: int = 1920,
        height: int = 1080,
        fps: int = 30,
        enable_ken_burns: bool = True,
        music_volume: float = 0.3,
        enable_ducking: bool = True,
        enable_subtitles: bool = True,
        progress_callback: Optional[callable] = None
    ) -> Dict[str, Any]:
        """
        Render complete video from project assets.

        Args:
            project_id: Project ID
            user_id: User ID
            job_id: Render job ID for progress tracking
            width: Video width
            height: Video height
            fps: Frames per second
            enable_ken_burns: Apply Ken Burns effect to images
            music_volume: Background music volume (0.0-1.0)
            enable_ducking: Enable audio ducking
            enable_subtitles: Add subtitles to video
            progress_callback: Optional callback for progress updates

        Returns:
            Dictionary with output_path, duration, and metadata

        Raises:
            CineCraftException: If rendering fails
        """
        try:
            # Get render job
            job = self.job_repo.get(job_id)
            if not job:
                raise CineCraftException(
                    code="JOB_NOT_FOUND",
                    message=f"Render job {job_id} not found"
                )

            # Update job status
            job.start()
            self.db.commit()

            # Stage 1: Validate project and collect assets (10%)
            await self._update_progress(job, 10, "Validating project", progress_callback)
            project = self.project_repo.get(project_id)
            if not project:
                raise CineCraftException(
                    code="PROJECT_NOT_FOUND",
                    message=f"Project {project_id} not found"
                )

            if project.user_id != user_id:
                raise CineCraftException(
                    code="UNAUTHORIZED",
                    message="Unauthorized access to project"
                )

            # Get all scenes in order
            scenes = self.scene_repo.get_by_project(project_id)
            if not scenes:
                raise CineCraftException(
                    code="NO_SCENES",
                    message="Project has no scenes"
                )

            logger.info(f"Rendering video for project {project_id} with {len(scenes)} scenes")

            # Stage 2: Collect and validate assets (20%)
            await self._update_progress(job, 20, "Collecting assets", progress_callback)

            # Get image assets for each scene
            image_paths = []
            scene_durations = []

            for scene in scenes:
                # Get scene image
                image_asset = self.asset_repo.get_by_scene(
                    scene_id=scene.id,
                    media_type=MediaType.IMAGE
                )

                if not image_asset:
                    raise CineCraftException(
                        code="MISSING_IMAGE",
                        message=f"Scene {scene.id} has no image"
                    )

                # Download image to temp location
                image_data = await self.storage_service.get_file(
                    asset_id=image_asset[0].id,
                    user_id=user_id
                )

                temp_image_path = f"/tmp/cinecraft_scene_{scene.id}.png"
                with open(temp_image_path, 'wb') as f:
                    f.write(image_data)

                image_paths.append(temp_image_path)

                # Calculate scene duration from voice narration
                voice_asset = self.asset_repo.get_by_scene(
                    scene_id=scene.id,
                    media_type=MediaType.AUDIO
                )

                if voice_asset:
                    voice_data = await self.storage_service.get_file(
                        asset_id=voice_asset[0].id,
                        user_id=user_id
                    )
                    temp_voice_path = f"/tmp/cinecraft_voice_{scene.id}.mp3"
                    with open(temp_voice_path, 'wb') as f:
                        f.write(voice_data)
                    duration = get_audio_duration(temp_voice_path)
                    scene_durations.append(int(duration) + 1)  # Add 1 second buffer
                else:
                    # Default duration if no voice
                    scene_durations.append(5)

            # Stage 3: Create video from images (40%)
            await self._update_progress(job, 40, "Creating video from images", progress_callback)

            temp_dir = Path(f"/tmp/cinecraft_render_{job_id}")
            temp_dir.mkdir(exist_ok=True)

            video_no_audio_path = str(temp_dir / "video_no_audio.mp4")

            create_video_from_images(
                image_paths=image_paths,
                output_path=video_no_audio_path,
                durations=scene_durations,
                width=width,
                height=height,
                fps=fps,
                ken_burns=enable_ken_burns
            )

            logger.info(f"Created video from {len(image_paths)} images")

            # Stage 4: Mix audio (60%)
            await self._update_progress(job, 60, "Mixing audio", progress_callback)

            # Concatenate voice narrations
            voice_concat_path = str(temp_dir / "voice_concat.mp3")
            await self._concatenate_audio_files(scenes, user_id, voice_concat_path)

            # Get background music
            music_path = None
            music_assets = self.asset_repo.get_by_project(
                project_id=project_id,
                media_type=MediaType.MUSIC
            )

            if music_assets:
                music_data = await self.storage_service.get_file(
                    asset_id=music_assets[0].id,
                    user_id=user_id
                )
                music_path = str(temp_dir / "music.mp3")
                with open(music_path, 'wb') as f:
                    f.write(music_data)

            # Mix audio
            video_with_audio_path = str(temp_dir / "video_with_audio.mp4")

            if music_path and os.path.exists(voice_concat_path):
                mix_audio(
                    video_path=video_no_audio_path,
                    voice_path=voice_concat_path,
                    music_path=music_path,
                    output_path=video_with_audio_path,
                    music_volume=music_volume,
                    enable_ducking=enable_ducking
                )
            elif os.path.exists(voice_concat_path):
                # Only voice, no music — simply add voice track to video
                from app.utils.video import run_ffmpeg
                run_ffmpeg([
                    "-i", video_no_audio_path,
                    "-i", voice_concat_path,
                    "-map", "0:v",
                    "-map", "1:a",
                    "-c:v", "copy",
                    "-c:a", "aac",
                    "-shortest",
                    video_with_audio_path
                ])
            else:
                # No audio at all
                import shutil
                shutil.copy(video_no_audio_path, video_with_audio_path)

            logger.info("Mixed audio tracks")

            # Stage 5: Add subtitles (80%)
            if enable_subtitles:
                await self._update_progress(job, 80, "Adding subtitles", progress_callback)

                # Generate subtitles from scenes
                scene_dicts = [
                    {"narration": scene.narration or ""}
                    for scene in scenes
                ]

                subtitles = generate_scene_subtitles(scene_dicts, scene_durations)

                # Create SRT file
                srt_path = str(temp_dir / "subtitles.srt")
                create_srt_file(subtitles, srt_path)

                # Add subtitles to video
                final_output_path = str(temp_dir / "final_video.mp4")
                add_subtitles(
                    video_path=video_with_audio_path,
                    subtitle_path=srt_path,
                    output_path=final_output_path
                )
            else:
                final_output_path = video_with_audio_path

            logger.info("Added subtitles to video")

            # Stage 6: Upload final video (90%)
            await self._update_progress(job, 90, "Uploading video", progress_callback)

            # Read final video
            with open(final_output_path, 'rb') as f:
                video_data = f.read()

            # Save to storage
            video_filename = f"project_{project_id}_render_{job_id}.mp4"
            video_asset = await self.storage_service.save_generated_asset(
                file_data=video_data,
                filename=video_filename,
                user_id=user_id,
                project_id=project_id,
                scene_id=None,
                media_type=MediaType.VIDEO,
                generation_provider="ffmpeg",
                generation_cost=0
            )

            # Calculate total duration
            total_duration = sum(scene_durations)

            # Clean up temp files
            await self._cleanup_temp_files(temp_dir, image_paths)

            # Update job with results
            job.complete(
                output_path=video_asset.file_path,
                output_url=video_asset.url,
                result_data={
                    "video_asset_id": video_asset.id,
                    "duration_seconds": total_duration,
                    "scene_count": len(scenes),
                    "resolution": f"{width}x{height}",
                    "fps": fps,
                    "ken_burns": enable_ken_burns,
                    "subtitles": enable_subtitles
                }
            )
            self.db.commit()

            await self._update_progress(job, 100, "Complete", progress_callback)

            # Update project with video URL and mark as completed
            from app.models.project import ProjectStatus
            project.video_url = video_asset.url
            project.video_duration = total_duration
            project.status = ProjectStatus.COMPLETED
            project.rendered_at = datetime.utcnow()
            self.db.commit()

            # Broadcast completion via WebSocket (best-effort)
            try:
                from app.core.websocket import manager
                await manager.broadcast_completion(
                    job_id=job.id,
                    result_data={
                        "video_asset_id": video_asset.id,
                        "output_url": video_asset.url,
                        "duration_seconds": total_duration,
                        "file_size": video_asset.file_size,
                        "scene_count": len(scenes),
                        "resolution": f"{width}x{height}"
                    }
                )
            except Exception as e:
                logger.debug(f"WebSocket broadcast failed (non-critical): {e}")

            logger.info(f"Video rendering complete for project {project_id}")

            return {
                "video_asset_id": video_asset.id,
                "output_path": video_asset.file_path,
                "output_url": video_asset.url,
                "duration_seconds": total_duration,
                "file_size": video_asset.file_size,
                "scene_count": len(scenes)
            }

        except FFmpegError as e:
            logger.exception(f"FFmpeg error rendering project {project_id}")
            job.fail(error_message=f"FFmpeg error: {str(e)}")
            self.db.commit()

            try:
                from app.core.websocket import manager
                await manager.broadcast_error(
                    job_id=job.id,
                    error_message=f"FFmpeg error: {str(e)}"
                )
            except Exception:
                pass

            raise CineCraftException(
                code="RENDERING_ERROR",
                message=f"Video rendering failed: {str(e)}"
            )

        except Exception as e:
            logger.exception(f"Error rendering project {project_id}")
            if job:
                job.fail(error_message=str(e))
                self.db.commit()

                try:
                    from app.core.websocket import manager
                    await manager.broadcast_error(
                        job_id=job.id,
                        error_message=str(e)
                    )
                except Exception:
                    pass

            raise CineCraftException(
                code="RENDERING_ERROR",
                message=f"Video rendering failed: {str(e)}"
            )

    async def _concatenate_audio_files(
        self,
        scenes: List,
        user_id: int,
        output_path: str
    ):
        """
        Concatenate voice audio files from all scenes.

        Args:
            scenes: List of scene objects
            user_id: User ID
            output_path: Output file path for concatenated audio
        """
        from app.utils.video import concatenate_videos

        audio_paths = []

        for scene in scenes:
            voice_asset = self.asset_repo.get_by_scene(
                scene_id=scene.id,
                media_type=MediaType.AUDIO
            )

            if voice_asset:
                voice_data = await self.storage_service.get_file(
                    asset_id=voice_asset[0].id,
                    user_id=user_id
                )
                temp_path = f"/tmp/cinecraft_voice_{scene.id}.mp3"
                with open(temp_path, 'wb') as f:
                    f.write(voice_data)
                audio_paths.append(temp_path)

        if audio_paths:
            if len(audio_paths) == 1:
                import shutil
                shutil.copy(audio_paths[0], output_path)
            else:
                # Use FFmpeg to concatenate audio files
                from app.utils.video import run_ffmpeg

                # Create concat file
                concat_file = output_path + ".concat.txt"
                with open(concat_file, 'w') as f:
                    for audio_path in audio_paths:
                        f.write(f"file '{os.path.abspath(audio_path)}'\n")

                try:
                    args = [
                        "-f", "concat",
                        "-safe", "0",
                        "-i", concat_file,
                        "-c", "copy",
                        output_path
                    ]
                    run_ffmpeg(args)
                finally:
                    if os.path.exists(concat_file):
                        os.remove(concat_file)

    async def _cleanup_temp_files(self, temp_dir: Path, image_paths: List[str]):
        """
        Clean up temporary files.

        Args:
            temp_dir: Temporary directory
            image_paths: List of temporary image paths
        """
        import shutil

        try:
            # Remove temp images
            for image_path in image_paths:
                if os.path.exists(image_path):
                    os.remove(image_path)

            # Remove temp directory
            if temp_dir.exists():
                shutil.rmtree(temp_dir)

            logger.info("Cleaned up temporary files")
        except Exception as e:
            logger.warning(f"Failed to clean up temp files: {e}")

    async def _update_progress(
        self,
        job,
        progress: float,
        stage: str,
        callback: Optional[callable] = None
    ):
        """
        Update job progress.

        Args:
            job: RenderJob instance
            progress: Progress percentage (0-100)
            stage: Current stage description
            callback: Optional callback function
        """
        job.update_progress(progress, stage)
        self.db.commit()

        # Broadcast via WebSocket (best-effort, don't fail on WS errors)
        try:
            from app.core.websocket import manager
            await manager.broadcast_progress(
                job_id=job.id,
                progress=progress,
                stage=stage,
                status=job.status.value
            )
        except Exception as e:
            logger.debug(f"WebSocket broadcast failed (non-critical): {e}")

        if callback:
            # Support both sync and async callbacks
            import asyncio
            if asyncio.iscoroutinefunction(callback):
                await callback(job.id, progress, stage)
            else:
                callback(job.id, progress, stage)

    def get_render_status(self, job_id: int, user_id: int) -> Dict[str, Any]:
        """
        Get render job status.

        Args:
            job_id: Job ID
            user_id: User ID

        Returns:
            Dictionary with job status

        Raises:
            CineCraftException: If job not found or unauthorized
        """
        job = self.job_repo.get(job_id)

        if not job:
            raise CineCraftException(
                code="JOB_NOT_FOUND",
                message=f"Job {job_id} not found"
            )

        if job.user_id != user_id:
            raise CineCraftException(
                code="UNAUTHORIZED",
                message="Unauthorized access to job"
            )

        return {
            "job_id": job.id,
            "status": job.status.value,
            "progress": job.progress,
            "current_stage": job.current_stage,
            "stages_completed": job.stages_completed,
            "output_url": job.output_url,
            "error_message": job.error_message,
            "started_at": job.started_at,
            "completed_at": job.completed_at,
            "duration_seconds": job.duration_seconds
        }

    def cancel_render(self, job_id: int, user_id: int) -> bool:
        """
        Cancel a render job.

        Args:
            job_id: Job ID
            user_id: User ID

        Returns:
            True if cancelled successfully

        Raises:
            CineCraftException: If job not found or cannot be cancelled
        """
        job = self.job_repo.get(job_id)

        if not job:
            raise CineCraftException(
                code="JOB_NOT_FOUND",
                message=f"Job {job_id} not found"
            )

        if job.user_id != user_id:
            raise CineCraftException(
                code="UNAUTHORIZED",
                message="Unauthorized access to job"
            )

        if job.is_finished:
            raise CineCraftException(
                code="CANNOT_CANCEL",
                message="Cannot cancel finished job"
            )

        job.cancel()
        self.db.commit()

        logger.info(f"Cancelled render job {job_id}")

        return True
