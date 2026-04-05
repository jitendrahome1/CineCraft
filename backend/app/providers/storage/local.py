"""
Local filesystem storage provider implementation.
Implements the StorageProvider interface for local file storage.
"""
import os
import aiofiles
from pathlib import Path
from typing import Optional
from urllib.parse import quote

from app.providers.base.storage_provider import StorageProvider
from app.core.logging import get_logger

logger = get_logger(__name__)


class LocalStorageProvider(StorageProvider):
    """
    Local filesystem storage provider.

    Stores files in a local directory structure.
    Suitable for development and small-scale deployments.
    """

    def __init__(self, base_path: str, base_url: Optional[str] = None):
        """
        Initialize local storage provider.

        Args:
            base_path: Base directory path for file storage
            base_url: Base URL for accessing files (e.g., 'http://localhost:8000/storage')
        """
        self.base_path = Path(base_path)
        self.base_url = base_url or f"file://{base_path}"

        # Create base directory if it doesn't exist
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Local storage initialized at {self.base_path}")

    def _get_full_path(self, path: str) -> Path:
        """
        Get full filesystem path.

        Args:
            path: Relative path

        Returns:
            Full filesystem path
        """
        # Remove leading slash if present
        path = path.lstrip('/')
        full_path = self.base_path / path

        # Ensure the file is within the base path (security check)
        try:
            full_path.resolve().relative_to(self.base_path.resolve())
        except ValueError:
            raise ValueError(f"Invalid path: {path} is outside base directory")

        return full_path

    def _get_url(self, path: str) -> str:
        """
        Get URL for a file.

        Args:
            path: File path

        Returns:
            File URL
        """
        path = path.lstrip('/')
        # URL-encode the path
        encoded_path = quote(path)
        return f"{self.base_url}/{encoded_path}"

    async def save_file(
        self,
        file: bytes,
        path: str,
        content_type: Optional[str] = None
    ) -> str:
        """
        Save file to local storage.

        Args:
            file: File data as bytes
            path: Destination path
            content_type: MIME type (not used for local storage)

        Returns:
            URL to the saved file
        """
        full_path = self._get_full_path(path)

        # Create parent directories if they don't exist
        full_path.parent.mkdir(parents=True, exist_ok=True)

        # Write file asynchronously
        async with aiofiles.open(full_path, 'wb') as f:
            await f.write(file)

        logger.info(f"Saved file to {full_path}")
        return self._get_url(path)

    async def get_file(self, path: str) -> bytes:
        """
        Retrieve file from local storage.

        Args:
            path: File path

        Returns:
            File data as bytes

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        full_path = self._get_full_path(path)

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        async with aiofiles.open(full_path, 'rb') as f:
            data = await f.read()

        return data

    async def delete_file(self, path: str) -> bool:
        """
        Delete file from local storage.

        Args:
            path: File path

        Returns:
            True if deleted successfully
        """
        try:
            full_path = self._get_full_path(path)

            if full_path.exists():
                full_path.unlink()
                logger.info(f"Deleted file: {full_path}")

                # Clean up empty parent directories
                try:
                    parent = full_path.parent
                    while parent != self.base_path and not any(parent.iterdir()):
                        parent.rmdir()
                        parent = parent.parent
                except Exception as e:
                    logger.warning(f"Could not clean up empty directories: {e}")

                return True

            logger.warning(f"File not found for deletion: {path}")
            return False

        except Exception as e:
            logger.error(f"Error deleting file {path}: {e}")
            return False

    async def file_exists(self, path: str) -> bool:
        """
        Check if file exists in local storage.

        Args:
            path: File path

        Returns:
            True if file exists
        """
        try:
            full_path = self._get_full_path(path)
            return full_path.exists() and full_path.is_file()
        except Exception:
            return False

    async def get_presigned_url(
        self,
        path: str,
        expiry: int = 3600
    ) -> str:
        """
        Get URL for file (no expiry for local storage).

        Args:
            path: File path
            expiry: Not used for local storage

        Returns:
            File URL
        """
        # Local storage URLs don't expire
        if not await self.file_exists(path):
            raise FileNotFoundError(f"File not found: {path}")

        return self._get_url(path)

    async def list_files(self, prefix: str = "") -> list[str]:
        """
        List files in local storage with optional prefix.

        Args:
            prefix: Path prefix to filter files

        Returns:
            List of relative file paths
        """
        try:
            prefix_path = self._get_full_path(prefix) if prefix else self.base_path

            if not prefix_path.exists():
                return []

            files = []

            if prefix_path.is_file():
                # If prefix is a file, return it
                relative_path = prefix_path.relative_to(self.base_path)
                return [str(relative_path)]

            # Walk the directory tree
            for item in prefix_path.rglob('*'):
                if item.is_file():
                    relative_path = item.relative_to(self.base_path)
                    files.append(str(relative_path))

            return sorted(files)

        except Exception as e:
            logger.error(f"Error listing files with prefix '{prefix}': {e}")
            return []

    async def get_file_size(self, path: str) -> int:
        """
        Get file size in bytes.

        Args:
            path: File path

        Returns:
            File size in bytes

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        full_path = self._get_full_path(path)

        if not full_path.exists():
            raise FileNotFoundError(f"File not found: {path}")

        return full_path.stat().st_size

    async def copy_file(self, source: str, destination: str) -> str:
        """
        Copy file within local storage.

        Args:
            source: Source file path
            destination: Destination file path

        Returns:
            URL to the copied file

        Raises:
            FileNotFoundError: If source file doesn't exist
        """
        source_path = self._get_full_path(source)
        dest_path = self._get_full_path(destination)

        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        # Create parent directories for destination
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Read source and write to destination
        async with aiofiles.open(source_path, 'rb') as src:
            data = await src.read()

        async with aiofiles.open(dest_path, 'wb') as dst:
            await dst.write(data)

        logger.info(f"Copied file from {source} to {destination}")
        return self._get_url(destination)

    async def move_file(self, source: str, destination: str) -> str:
        """
        Move file within local storage.

        Args:
            source: Source file path
            destination: Destination file path

        Returns:
            URL to the moved file

        Raises:
            FileNotFoundError: If source file doesn't exist
        """
        source_path = self._get_full_path(source)
        dest_path = self._get_full_path(destination)

        if not source_path.exists():
            raise FileNotFoundError(f"Source file not found: {source}")

        # Create parent directories for destination
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Move file
        source_path.rename(dest_path)

        logger.info(f"Moved file from {source} to {destination}")
        return self._get_url(destination)

    def get_storage_info(self) -> dict:
        """
        Get storage provider information.

        Returns:
            Dictionary with storage info
        """
        total_files = 0
        total_size = 0

        for item in self.base_path.rglob('*'):
            if item.is_file():
                total_files += 1
                total_size += item.stat().st_size

        return {
            "provider": "local",
            "base_path": str(self.base_path),
            "base_url": self.base_url,
            "total_files": total_files,
            "total_size_bytes": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2)
        }
