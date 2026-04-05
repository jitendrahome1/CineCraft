"""
Video utility functions for CineCraft.
FFmpeg wrapper for video processing, effects, and rendering.
"""
import subprocess
import os
from typing import List, Optional, Tuple
from pathlib import Path

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class FFmpegError(Exception):
    """FFmpeg execution error."""
    pass


def run_ffmpeg(args: List[str], timeout: int = 3600) -> Tuple[str, str]:
    """
    Run FFmpeg command.

    Args:
        args: FFmpeg command arguments
        timeout: Command timeout in seconds

    Returns:
        Tuple of (stdout, stderr)

    Raises:
        FFmpegError: If command fails
    """
    cmd = ["ffmpeg", "-y"] + args  # -y = overwrite output files

    logger.info(f"Running FFmpeg: {' '.join(cmd)}")

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=True
        )

        return result.stdout, result.stderr

    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg failed: {e.stderr}")
        raise FFmpegError(f"FFmpeg command failed: {e.stderr}")
    except subprocess.TimeoutExpired:
        logger.error(f"FFmpeg timed out after {timeout}s")
        raise FFmpegError(f"FFmpeg timed out after {timeout}s")


def get_video_info(video_path: str) -> dict:
    """
    Get video information using ffprobe.

    Args:
        video_path: Path to video file

    Returns:
        Dictionary with video information
    """
    cmd = [
        "ffprobe",
        "-v", "quiet",
        "-print_format", "json",
        "-show_format",
        "-show_streams",
        video_path
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        import json
        return json.loads(result.stdout)
    except Exception as e:
        logger.error(f"Failed to get video info: {e}")
        return {}


def create_ken_burns_video(
    image_path: str,
    output_path: str,
    duration: int,
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
    zoom_direction: str = "in"
) -> str:
    """
    Create video with Ken Burns effect (pan and zoom) from static image.

    Args:
        image_path: Path to input image
        output_path: Path to output video
        duration: Duration in seconds
        width: Output width
        height: Output height
        fps: Frames per second
        zoom_direction: 'in' for zoom in, 'out' for zoom out

    Returns:
        Path to output video

    Raises:
        FFmpegError: If rendering fails
    """
    # Ken Burns effect parameters
    if zoom_direction == "in":
        # Zoom in: start at 1.0x, end at 1.1x
        zoom_start = 1.0
        zoom_end = 1.1
    else:
        # Zoom out: start at 1.1x, end at 1.0x
        zoom_start = 1.1
        zoom_end = 1.0

    # Build zoompan filter
    zoompan_filter = (
        f"zoompan="
        f"z='min(zoom+0.0015,{zoom_end})':d={duration * fps}:"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':"
        f"s={width}x{height}:fps={fps}"
    )

    args = [
        "-loop", "1",
        "-i", image_path,
        "-vf", zoompan_filter,
        "-t", str(duration),
        "-pix_fmt", "yuv420p",
        "-c:v", "libx264",
        "-preset", settings.FFMPEG_PRESET,
        "-threads", str(settings.FFMPEG_THREADS),
        output_path
    ]

    run_ffmpeg(args)
    logger.info(f"Created Ken Burns video: {output_path}")

    return output_path


def add_fade_transition(
    input_path: str,
    output_path: str,
    fade_in: float = 0.5,
    fade_out: float = 0.5
) -> str:
    """
    Add fade in/out transitions to video.

    Args:
        input_path: Input video path
        output_path: Output video path
        fade_in: Fade in duration in seconds
        fade_out: Fade out duration in seconds

    Returns:
        Path to output video
    """
    # Get video duration
    info = get_video_info(input_path)
    duration = float(info.get("format", {}).get("duration", 0))

    if duration == 0:
        raise FFmpegError("Could not determine video duration")

    fade_out_start = duration - fade_out

    filter_complex = (
        f"fade=t=in:st=0:d={fade_in},"
        f"fade=t=out:st={fade_out_start}:d={fade_out}"
    )

    args = [
        "-i", input_path,
        "-vf", filter_complex,
        "-c:a", "copy",
        output_path
    ]

    run_ffmpeg(args)
    return output_path


def concatenate_videos(
    video_paths: List[str],
    output_path: str,
    transition_duration: float = 0.5
) -> str:
    """
    Concatenate multiple videos with crossfade transitions.

    Args:
        video_paths: List of video file paths
        output_path: Output video path
        transition_duration: Transition duration in seconds

    Returns:
        Path to output video
    """
    if len(video_paths) == 0:
        raise ValueError("No videos to concatenate")

    if len(video_paths) == 1:
        # Just copy if only one video
        import shutil
        shutil.copy(video_paths[0], output_path)
        return output_path

    # Create concat file
    concat_file = output_path + ".concat.txt"
    with open(concat_file, 'w') as f:
        for video_path in video_paths:
            f.write(f"file '{os.path.abspath(video_path)}'\n")

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
        # Clean up concat file
        if os.path.exists(concat_file):
            os.remove(concat_file)

    return output_path


def mix_audio(
    video_path: str,
    voice_path: str,
    music_path: str,
    output_path: str,
    voice_volume: float = 1.0,
    music_volume: float = 0.3,
    enable_ducking: bool = True
) -> str:
    """
    Mix voice narration and background music into video.

    Args:
        video_path: Input video path (without audio)
        voice_path: Voice narration audio path
        music_path: Background music audio path
        output_path: Output video path
        voice_volume: Voice volume (0.0-1.0)
        music_volume: Music volume (0.0-1.0)
        enable_ducking: Enable audio ducking (lower music when voice plays)

    Returns:
        Path to output video
    """
    if enable_ducking:
        # Sidechained ducking: reduce music volume when voice is present
        filter_complex = (
            f"[1:a]volume={voice_volume}[voice];"
            f"[2:a]volume={music_volume}[music];"
            f"[music][voice]sidechaincompress=threshold=0.1:ratio=4:attack=200:release=1000[mixed]"
        )
    else:
        # Simple mix without ducking
        filter_complex = (
            f"[1:a]volume={voice_volume}[voice];"
            f"[2:a]volume={music_volume}[music];"
            f"[voice][music]amix=inputs=2:duration=first[mixed]"
        )

    args = [
        "-i", video_path,
        "-i", voice_path,
        "-i", music_path,
        "-filter_complex", filter_complex,
        "-map", "0:v",
        "-map", "[mixed]",
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        output_path
    ]

    run_ffmpeg(args)
    return output_path


def add_subtitles(
    video_path: str,
    subtitle_path: str,
    output_path: str,
    font_size: int = 24,
    font_color: str = "white",
    outline_color: str = "black",
    outline_width: int = 2
) -> str:
    """
    Add subtitles to video.

    Args:
        video_path: Input video path
        subtitle_path: SRT subtitle file path
        output_path: Output video path
        font_size: Subtitle font size
        font_color: Subtitle font color
        outline_color: Subtitle outline color
        outline_width: Subtitle outline width

    Returns:
        Path to output video
    """
    # Check if subtitles filter is available (requires libass)
    import shutil
    has_subtitles_filter = False
    try:
        result = subprocess.run(
            ["ffmpeg", "-filters"],
            capture_output=True, text=True, timeout=5
        )
        has_subtitles_filter = "subtitles" in result.stdout
    except Exception:
        pass

    if not has_subtitles_filter:
        logger.warning("FFmpeg subtitles filter not available (requires libass). Skipping subtitle overlay.")
        # Just copy the video without subtitles
        import shutil as shutil_copy
        shutil_copy.copy(video_path, output_path)
        return output_path

    # Escape path for FFmpeg subtitle filter (escape special chars)
    escaped_subtitle_path = subtitle_path.replace('\\', '/').replace(':', '\\\\:').replace("'", "\\\\'")

    # Build force_style string
    force_style = (
        f"FontSize={font_size},"
        f"PrimaryColour=&H{color_to_hex(font_color)},"
        f"OutlineColour=&H{color_to_hex(outline_color)},"
        f"Outline={outline_width}"
    )

    subtitle_filter = f"subtitles='{escaped_subtitle_path}':force_style='{force_style}'"

    args = [
        "-i", video_path,
        "-vf", subtitle_filter,
        "-c:a", "copy",
        output_path
    ]

    run_ffmpeg(args)
    return output_path


def color_to_hex(color: str) -> str:
    """
    Convert color name to hex for FFmpeg.

    Args:
        color: Color name

    Returns:
        Hex color code
    """
    colors = {
        "white": "FFFFFF",
        "black": "000000",
        "red": "FF0000",
        "green": "00FF00",
        "blue": "0000FF",
        "yellow": "FFFF00"
    }

    return colors.get(color.lower(), "FFFFFF")


def create_video_from_images(
    image_paths: List[str],
    output_path: str,
    durations: List[int],
    width: int = 1920,
    height: int = 1080,
    fps: int = 30,
    ken_burns: bool = True
) -> str:
    """
    Create video from sequence of images.

    Args:
        image_paths: List of image file paths
        output_path: Output video path
        durations: Duration for each image in seconds
        width: Output width
        height: Output height
        fps: Frames per second
        ken_burns: Apply Ken Burns effect

    Returns:
        Path to output video
    """
    if len(image_paths) != len(durations):
        raise ValueError("Number of images must match number of durations")

    # Create temporary videos for each image
    temp_dir = Path(output_path).parent / "temp_videos"
    temp_dir.mkdir(exist_ok=True)

    temp_videos = []

    try:
        for idx, (image_path, duration) in enumerate(zip(image_paths, durations)):
            temp_video = str(temp_dir / f"scene_{idx}.mp4")

            if ken_burns:
                zoom_dir = "in" if idx % 2 == 0 else "out"
                create_ken_burns_video(
                    image_path=image_path,
                    output_path=temp_video,
                    duration=duration,
                    width=width,
                    height=height,
                    fps=fps,
                    zoom_direction=zoom_dir
                )
            else:
                # Simple static image to video
                args = [
                    "-loop", "1",
                    "-i", image_path,
                    "-t", str(duration),
                    "-vf", f"scale={width}:{height}",
                    "-pix_fmt", "yuv420p",
                    "-c:v", "libx264",
                    "-preset", settings.FFMPEG_PRESET,
                    temp_video
                ]
                run_ffmpeg(args)

            temp_videos.append(temp_video)

        # Concatenate all videos
        concatenate_videos(temp_videos, output_path)

    finally:
        # Clean up temporary videos
        import shutil
        if temp_dir.exists():
            shutil.rmtree(temp_dir)

    return output_path


def get_audio_duration(audio_path: str) -> float:
    """
    Get audio file duration.

    Args:
        audio_path: Path to audio file

    Returns:
        Duration in seconds
    """
    info = get_video_info(audio_path)
    duration = float(info.get("format", {}).get("duration", 0))
    return duration


def extract_audio(video_path: str, output_path: str) -> str:
    """
    Extract audio from video.

    Args:
        video_path: Input video path
        output_path: Output audio path

    Returns:
        Path to output audio
    """
    args = [
        "-i", video_path,
        "-vn",
        "-acodec", "copy",
        output_path
    ]

    run_ffmpeg(args)
    return output_path
