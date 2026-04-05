"""
Storage service for managing media file uploads and downloads.
Handles file operations and database records for media assets.
"""
from typing import Optional, List, Dict, Any, BinaryIO
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import uuid
import mimetypes

from app.providers.base.storage_provider import StorageProvider
from app.repositories.media_asset import MediaAssetRepository
from app.models.media_asset import MediaAsset, MediaType
from app.core.errors import ValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)


class StorageService:
    """
    Service for managing media file storage and database records.

    Coordinates between storage providers and the database.
    """

    def __init__(self, db: Session, storage_provider: StorageProvider = None):
        """
        Initialize storage service.

        Args:
            db: Database session
            storage_provider: Storage provider instance (auto-detected if not provided)
        """
        self.db = db
        if storage_provider is None:
            from app.providers.storage.factory import get_storage_provider_from_config
            storage_provider = get_storage_provider_from_config()
        self.storage_provider = storage_provider
        self.repository = MediaAssetRepository(db)

    async def upload_file(
        self,
        file_data: bytes,
        filename: str,
        user_id: int,
        project_id: Optional[int] = None,
        scene_id: Optional[int] = None,
        media_type: Optional[MediaType] = None,
        metadata: Optional[Dict[str, Any]] = None,
        expires_in_days: Optional[int] = None
    ) -> MediaAsset:
        """
        Upload a file and create database record.

        Args:
            file_data: File contents as bytes
            filename: Original filename
            user_id: User ID
            project_id: Optional project ID
            scene_id: Optional scene ID
            media_type: Optional media type (will be detected if not provided)
            metadata: Optional metadata dictionary
            expires_in_days: Optional expiration in days (for temporary files)

        Returns:
            Created MediaAsset instance

        Raises:
            ValidationError: If validation fails
        """
        try:
            # Detect media type if not provided
            if not media_type:
                media_type = self._detect_media_type(filename)

            # Generate unique filename to avoid collisions
            file_path = self._generate_file_path(
                user_id=user_id,
                project_id=project_id,
                filename=filename
            )

            # Detect MIME type
            mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

            # Save file to storage
            url = await self.storage_provider.save_file(
                file=file_data,
                path=file_path,
                content_type=mime_type
            )

            # Calculate file size
            file_size = len(file_data)

            # Calculate expiry date if specified
            expires_at = None
            if expires_in_days:
                expires_at = datetime.utcnow() + timedelta(days=expires_in_days)

            # Create database record
            asset_data = {
                "user_id": user_id,
                "project_id": project_id,
                "scene_id": scene_id,
                "filename": file_path.split('/')[-1],
                "original_filename": filename,
                "file_path": file_path,
                "file_size": file_size,
                "mime_type": mime_type,
                "media_type": media_type,
                "storage_provider": self._get_provider_name(),
                "url": url,
                "metadata": metadata or {},
                "is_generated": 0,
                "uploaded_at": datetime.utcnow(),
                "expires_at": expires_at
            }

            asset = self.repository.create(asset_data)
            logger.info(f"Uploaded file {filename} as asset {asset.id}")

            return asset

        except Exception as e:
            logger.error(f"Error uploading file {filename}: {e}")
            raise ValidationError(f"File upload failed: {str(e)}")

    async def save_generated_asset(
        self,
        file_data: bytes,
        filename: str,
        user_id: int,
        project_id: int,
        scene_id: Optional[int] = None,
        media_type: MediaType = MediaType.IMAGE,
        generation_provider: str = "unknown",
        generation_prompt: Optional[str] = None,
        generation_cost: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> MediaAsset:
        """
        Save an AI-generated media file.

        Args:
            file_data: File contents as bytes
            filename: Filename
            user_id: User ID
            project_id: Project ID
            scene_id: Optional scene ID
            media_type: Media type
            generation_provider: AI provider name
            generation_prompt: Generation prompt
            generation_cost: Generation cost in cents
            metadata: Optional metadata

        Returns:
            Created MediaAsset instance
        """
        # Generate file path
        file_path = self._generate_file_path(
            user_id=user_id,
            project_id=project_id,
            filename=filename,
            is_generated=True
        )

        # Detect MIME type
        mime_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"

        # Save file to storage
        url = await self.storage_provider.save_file(
            file=file_data,
            path=file_path,
            content_type=mime_type
        )

        # Create database record
        asset_data = {
            "user_id": user_id,
            "project_id": project_id,
            "scene_id": scene_id,
            "filename": file_path.split('/')[-1],
            "original_filename": filename,
            "file_path": file_path,
            "file_size": len(file_data),
            "mime_type": mime_type,
            "media_type": media_type,
            "storage_provider": self._get_provider_name(),
            "url": url,
            "metadata": metadata or {},
            "is_generated": 1,
            "generation_provider": generation_provider,
            "generation_prompt": generation_prompt,
            "generation_cost": generation_cost,
            "uploaded_at": datetime.utcnow()
        }

        asset = self.repository.create(asset_data)
        logger.info(f"Saved generated asset {asset.id} from {generation_provider}")

        return asset

    async def get_file(self, asset_id: int, user_id: int) -> bytes:
        """
        Get file contents.

        Args:
            asset_id: Asset ID
            user_id: User ID (for authorization)

        Returns:
            File contents as bytes

        Raises:
            ValidationError: If asset not found or unauthorized
        """
        asset = self.repository.get(asset_id)

        if not asset:
            raise ValidationError(f"Asset {asset_id} not found")

        if asset.user_id != user_id:
            raise ValidationError("Unauthorized access to asset")

        if asset.is_expired:
            raise ValidationError("Asset has expired")

        return await self.storage_provider.get_file(asset.file_path)

    async def get_presigned_url(
        self,
        asset_id: int,
        user_id: int,
        expiry: int = 3600
    ) -> str:
        """
        Get presigned URL for asset.

        Args:
            asset_id: Asset ID
            user_id: User ID (for authorization)
            expiry: URL expiry in seconds

        Returns:
            Presigned URL

        Raises:
            ValidationError: If asset not found or unauthorized
        """
        asset = self.repository.get(asset_id)

        if not asset:
            raise ValidationError(f"Asset {asset_id} not found")

        if asset.user_id != user_id:
            raise ValidationError("Unauthorized access to asset")

        if asset.is_expired:
            raise ValidationError("Asset has expired")

        return await self.storage_provider.get_presigned_url(
            asset.file_path,
            expiry=expiry
        )

    async def delete_asset(self, asset_id: int, user_id: int) -> bool:
        """
        Delete asset and file.

        Args:
            asset_id: Asset ID
            user_id: User ID (for authorization)

        Returns:
            True if deleted successfully

        Raises:
            ValidationError: If asset not found or unauthorized
        """
        asset = self.repository.get(asset_id)

        if not asset:
            raise ValidationError(f"Asset {asset_id} not found")

        if asset.user_id != user_id:
            raise ValidationError("Unauthorized access to asset")

        # Delete from storage
        try:
            await self.storage_provider.delete_file(asset.file_path)
        except Exception as e:
            logger.warning(f"Error deleting file {asset.file_path}: {e}")

        # Delete from database
        self.repository.delete(asset_id)
        logger.info(f"Deleted asset {asset_id}")

        return True

    async def delete_expired_assets(self) -> int:
        """
        Delete all expired assets.

        Returns:
            Number of assets deleted
        """
        expired = self.repository.get_expired_assets()
        count = 0

        for asset in expired:
            try:
                await self.storage_provider.delete_file(asset.file_path)
                count += 1
            except Exception as e:
                logger.warning(f"Error deleting expired file {asset.file_path}: {e}")

        # Delete from database
        deleted_count = self.repository.delete_expired()
        logger.info(f"Deleted {deleted_count} expired assets")

        return deleted_count

    def get_user_storage_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get storage statistics for a user.

        Args:
            user_id: User ID

        Returns:
            Storage statistics
        """
        return self.repository.get_storage_stats(user_id)

    def get_project_storage_stats(self, project_id: int) -> Dict[str, Any]:
        """
        Get storage statistics for a project.

        Args:
            project_id: Project ID

        Returns:
            Storage statistics
        """
        return self.repository.get_project_storage_stats(project_id)

    def _detect_media_type(self, filename: str) -> MediaType:
        """
        Detect media type from filename.

        Args:
            filename: Filename

        Returns:
            MediaType
        """
        mime_type, _ = mimetypes.guess_type(filename)

        if mime_type:
            if mime_type.startswith("image/"):
                return MediaType.IMAGE
            elif mime_type.startswith("audio/"):
                return MediaType.AUDIO
            elif mime_type.startswith("video/"):
                return MediaType.VIDEO
            elif mime_type in ["application/x-subrip", "text/vtt"]:
                return MediaType.SUBTITLE

        # Check extension
        ext = filename.lower().split('.')[-1]
        if ext in ["jpg", "jpeg", "png", "gif", "webp", "bmp"]:
            return MediaType.IMAGE
        elif ext in ["mp3", "wav", "ogg", "flac", "m4a"]:
            return MediaType.AUDIO
        elif ext in ["mp4", "webm", "mov", "avi", "mkv"]:
            return MediaType.VIDEO
        elif ext in ["srt", "vtt", "ass"]:
            return MediaType.SUBTITLE
        elif ext in ["mid", "midi"]:
            return MediaType.MUSIC

        return MediaType.OTHER

    def _generate_file_path(
        self,
        user_id: int,
        project_id: Optional[int],
        filename: str,
        is_generated: bool = False
    ) -> str:
        """
        Generate unique file path.

        Args:
            user_id: User ID
            project_id: Optional project ID
            filename: Original filename
            is_generated: Whether file is AI-generated

        Returns:
            File path
        """
        # Generate UUID for uniqueness
        file_uuid = uuid.uuid4().hex

        # Get file extension
        ext = filename.split('.')[-1] if '.' in filename else ''

        # Build path: users/{user_id}/projects/{project_id}/{type}/{uuid}.{ext}
        path_parts = ["users", str(user_id)]

        if project_id:
            path_parts.extend(["projects", str(project_id)])

        if is_generated:
            path_parts.append("generated")
        else:
            path_parts.append("uploads")

        # Final filename
        final_filename = f"{file_uuid}.{ext}" if ext else file_uuid
        path_parts.append(final_filename)

        return "/".join(path_parts)

    def _get_provider_name(self) -> str:
        """
        Get storage provider name.

        Returns:
            Provider name ('local', 's3', etc.)
        """
        provider_class = self.storage_provider.__class__.__name__
        if "Local" in provider_class:
            return "local"
        elif "S3" in provider_class:
            return "s3"
        return "unknown"
