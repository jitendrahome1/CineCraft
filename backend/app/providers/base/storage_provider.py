"""
Base abstract class for storage providers.
Implements Strategy Pattern for swappable storage backends.
"""
from abc import ABC, abstractmethod
from typing import Optional


class StorageProvider(ABC):
    """
    Abstract base class for storage providers.
    All storage providers must implement these methods.
    """

    @abstractmethod
    async def save_file(
        self,
        file: bytes,
        path: str,
        content_type: Optional[str] = None
    ) -> str:
        """
        Save file to storage.

        Args:
            file: File data as bytes
            path: Destination path/key
            content_type: MIME type of the file

        Returns:
            URL or path to the saved file
        """
        pass

    @abstractmethod
    async def get_file(self, path: str) -> bytes:
        """
        Retrieve file from storage.

        Args:
            path: File path/key

        Returns:
            File data as bytes
        """
        pass

    @abstractmethod
    async def delete_file(self, path: str) -> bool:
        """
        Delete file from storage.

        Args:
            path: File path/key

        Returns:
            True if deleted successfully
        """
        pass

    @abstractmethod
    async def file_exists(self, path: str) -> bool:
        """
        Check if file exists in storage.

        Args:
            path: File path/key

        Returns:
            True if file exists
        """
        pass

    @abstractmethod
    async def get_presigned_url(
        self,
        path: str,
        expiry: int = 3600
    ) -> str:
        """
        Get temporary download URL for file.

        Args:
            path: File path/key
            expiry: URL expiry time in seconds

        Returns:
            Presigned URL
        """
        pass

    @abstractmethod
    async def list_files(self, prefix: str = "") -> list[str]:
        """
        List files in storage with optional prefix.

        Args:
            prefix: Path prefix to filter files

        Returns:
            List of file paths
        """
        pass
