"""
File utility functions for CineCraft.
Provides helper functions for file operations, validation, and processing.
"""
import os
import hashlib
import magic
import mimetypes
from typing import Optional, Tuple
from pathlib import Path

from app.core.logging import get_logger

logger = get_logger(__name__)


def get_file_hash(file_data: bytes, algorithm: str = "sha256") -> str:
    """
    Calculate hash of file contents.

    Args:
        file_data: File contents as bytes
        algorithm: Hash algorithm ('md5', 'sha1', 'sha256', 'sha512')

    Returns:
        Hexadecimal hash string

    Raises:
        ValueError: If algorithm is not supported
    """
    hash_functions = {
        "md5": hashlib.md5,
        "sha1": hashlib.sha1,
        "sha256": hashlib.sha256,
        "sha512": hashlib.sha512
    }

    if algorithm not in hash_functions:
        raise ValueError(f"Unsupported hash algorithm: {algorithm}")

    hasher = hash_functions[algorithm]()
    hasher.update(file_data)
    return hasher.hexdigest()


def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename.

    Args:
        filename: Filename

    Returns:
        File extension (lowercase, without dot) or empty string
    """
    if '.' not in filename:
        return ''

    return filename.rsplit('.', 1)[-1].lower()


def validate_file_size(
    file_size: int,
    max_size_mb: int = 100
) -> Tuple[bool, Optional[str]]:
    """
    Validate file size.

    Args:
        file_size: File size in bytes
        max_size_mb: Maximum allowed size in MB

    Returns:
        Tuple of (is_valid, error_message)
    """
    max_size_bytes = max_size_mb * 1024 * 1024

    if file_size > max_size_bytes:
        return False, f"File size exceeds maximum allowed size of {max_size_mb}MB"

    if file_size == 0:
        return False, "File is empty"

    return True, None


def validate_file_type(
    filename: str,
    allowed_extensions: list[str]
) -> Tuple[bool, Optional[str]]:
    """
    Validate file type by extension.

    Args:
        filename: Filename
        allowed_extensions: List of allowed extensions (without dots, e.g., ['jpg', 'png'])

    Returns:
        Tuple of (is_valid, error_message)
    """
    extension = get_file_extension(filename)

    if not extension:
        return False, "File has no extension"

    if extension not in [ext.lower() for ext in allowed_extensions]:
        return False, f"File type '{extension}' not allowed. Allowed types: {', '.join(allowed_extensions)}"

    return True, None


def validate_image_file(
    file_data: bytes,
    max_size_mb: int = 10,
    allowed_formats: Optional[list[str]] = None
) -> Tuple[bool, Optional[str]]:
    """
    Validate image file.

    Args:
        file_data: File contents
        max_size_mb: Maximum size in MB
        allowed_formats: Allowed image formats (e.g., ['jpeg', 'png'])

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check size
    is_valid, error = validate_file_size(len(file_data), max_size_mb)
    if not is_valid:
        return False, error

    # Check MIME type
    try:
        mime = magic.from_buffer(file_data, mime=True)
        if not mime.startswith('image/'):
            return False, f"File is not an image (detected: {mime})"

        # Check specific format if specified
        if allowed_formats:
            image_format = mime.split('/')[-1]
            if image_format not in allowed_formats:
                return False, f"Image format '{image_format}' not allowed"

    except Exception as e:
        logger.warning(f"Could not detect MIME type: {e}")
        # Fall back to extension check
        pass

    return True, None


def validate_audio_file(
    file_data: bytes,
    max_size_mb: int = 50,
    allowed_formats: Optional[list[str]] = None
) -> Tuple[bool, Optional[str]]:
    """
    Validate audio file.

    Args:
        file_data: File contents
        max_size_mb: Maximum size in MB
        allowed_formats: Allowed audio formats (e.g., ['mp3', 'wav'])

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check size
    is_valid, error = validate_file_size(len(file_data), max_size_mb)
    if not is_valid:
        return False, error

    # Check MIME type
    try:
        mime = magic.from_buffer(file_data, mime=True)
        if not (mime.startswith('audio/') or mime == 'application/ogg'):
            return False, f"File is not audio (detected: {mime})"

        # Check specific format if specified
        if allowed_formats:
            audio_format = mime.split('/')[-1]
            if audio_format not in allowed_formats:
                return False, f"Audio format '{audio_format}' not allowed"

    except Exception as e:
        logger.warning(f"Could not detect MIME type: {e}")
        pass

    return True, None


def validate_video_file(
    file_data: bytes,
    max_size_mb: int = 500,
    allowed_formats: Optional[list[str]] = None
) -> Tuple[bool, Optional[str]]:
    """
    Validate video file.

    Args:
        file_data: File contents
        max_size_mb: Maximum size in MB
        allowed_formats: Allowed video formats (e.g., ['mp4', 'webm'])

    Returns:
        Tuple of (is_valid, error_message)
    """
    # Check size
    is_valid, error = validate_file_size(len(file_data), max_size_mb)
    if not is_valid:
        return False, error

    # Check MIME type
    try:
        mime = magic.from_buffer(file_data, mime=True)
        if not mime.startswith('video/'):
            return False, f"File is not a video (detected: {mime})"

        # Check specific format if specified
        if allowed_formats:
            video_format = mime.split('/')[-1]
            if video_format not in allowed_formats:
                return False, f"Video format '{video_format}' not allowed"

    except Exception as e:
        logger.warning(f"Could not detect MIME type: {e}")
        pass

    return True, None


def get_safe_filename(filename: str) -> str:
    """
    Generate safe filename by removing dangerous characters.

    Args:
        filename: Original filename

    Returns:
        Safe filename
    """
    # Get name and extension
    name, ext = os.path.splitext(filename)

    # Remove or replace dangerous characters
    safe_chars = []
    for char in name:
        if char.isalnum() or char in ['-', '_', '.', ' ']:
            safe_chars.append(char)
        else:
            safe_chars.append('_')

    safe_name = ''.join(safe_chars).strip()

    # Limit length
    if len(safe_name) > 200:
        safe_name = safe_name[:200]

    # Ensure not empty
    if not safe_name:
        safe_name = "file"

    return f"{safe_name}{ext}"


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format.

    Args:
        size_bytes: Size in bytes

    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    units = ['B', 'KB', 'MB', 'GB', 'TB']
    size = float(size_bytes)
    unit_index = 0

    while size >= 1024 and unit_index < len(units) - 1:
        size /= 1024
        unit_index += 1

    if unit_index == 0:
        return f"{int(size)} {units[unit_index]}"
    else:
        return f"{size:.2f} {units[unit_index]}"


def get_mime_type(filename: str) -> str:
    """
    Get MIME type from filename.

    Args:
        filename: Filename

    Returns:
        MIME type string
    """
    mime_type, _ = mimetypes.guess_type(filename)
    return mime_type or "application/octet-stream"


def is_image_file(filename: str) -> bool:
    """
    Check if filename appears to be an image.

    Args:
        filename: Filename

    Returns:
        True if likely an image
    """
    mime_type = get_mime_type(filename)
    return mime_type.startswith('image/')


def is_audio_file(filename: str) -> bool:
    """
    Check if filename appears to be audio.

    Args:
        filename: Filename

    Returns:
        True if likely audio
    """
    mime_type = get_mime_type(filename)
    return mime_type.startswith('audio/')


def is_video_file(filename: str) -> bool:
    """
    Check if filename appears to be video.

    Args:
        filename: Filename

    Returns:
        True if likely video
    """
    mime_type = get_mime_type(filename)
    return mime_type.startswith('video/')


def ensure_directory_exists(directory: str):
    """
    Ensure directory exists, create if it doesn't.

    Args:
        directory: Directory path
    """
    Path(directory).mkdir(parents=True, exist_ok=True)


def get_file_info(file_path: str) -> dict:
    """
    Get comprehensive file information.

    Args:
        file_path: Path to file

    Returns:
        Dictionary with file information
    """
    path = Path(file_path)

    if not path.exists():
        return {"exists": False}

    stat = path.stat()

    return {
        "exists": True,
        "name": path.name,
        "extension": get_file_extension(path.name),
        "size_bytes": stat.st_size,
        "size_formatted": format_file_size(stat.st_size),
        "mime_type": get_mime_type(path.name),
        "is_file": path.is_file(),
        "is_dir": path.is_dir(),
        "created": stat.st_ctime,
        "modified": stat.st_mtime,
        "absolute_path": str(path.absolute())
    }
