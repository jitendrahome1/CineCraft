"""
Repository for MediaAsset model.
Handles data access operations for media files.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import and_, desc, func
from datetime import datetime

from app.repositories.base import BaseRepository
from app.models.media_asset import MediaAsset, MediaType
from app.core.logging import get_logger

logger = get_logger(__name__)


class MediaAssetRepository(BaseRepository[MediaAsset]):
    """Repository for MediaAsset CRUD operations."""

    def __init__(self, db: Session):
        super().__init__(MediaAsset, db)

    def get_by_user(
        self,
        user_id: int,
        skip: int = 0,
        limit: int = 100,
        media_type: Optional[MediaType] = None
    ) -> List[MediaAsset]:
        """
        Get all media assets for a user.

        Args:
            user_id: User ID
            skip: Number of records to skip
            limit: Maximum number of records
            media_type: Optional media type filter

        Returns:
            List of media assets
        """
        query = self.db.query(MediaAsset).filter(MediaAsset.user_id == user_id)

        if media_type:
            query = query.filter(MediaAsset.media_type == media_type)

        return query.order_by(desc(MediaAsset.uploaded_at)).offset(skip).limit(limit).all()

    def get_by_project(
        self,
        project_id: int,
        skip: int = 0,
        limit: int = 100,
        media_type: Optional[MediaType] = None
    ) -> List[MediaAsset]:
        """
        Get all media assets for a project.

        Args:
            project_id: Project ID
            skip: Number of records to skip
            limit: Maximum number of records
            media_type: Optional media type filter

        Returns:
            List of media assets
        """
        query = self.db.query(MediaAsset).filter(MediaAsset.project_id == project_id)

        if media_type:
            query = query.filter(MediaAsset.media_type == media_type)

        return query.order_by(desc(MediaAsset.uploaded_at)).offset(skip).limit(limit).all()

    def get_by_scene(
        self,
        scene_id: int,
        skip: int = 0,
        limit: int = 100,
        media_type: Optional[MediaType] = None
    ) -> List[MediaAsset]:
        """
        Get all media assets for a scene.

        Args:
            scene_id: Scene ID
            skip: Number of records to skip
            limit: Maximum number of records
            media_type: Optional media type filter

        Returns:
            List of media assets
        """
        query = self.db.query(MediaAsset).filter(MediaAsset.scene_id == scene_id)

        if media_type:
            query = query.filter(MediaAsset.media_type == media_type)

        return query.order_by(desc(MediaAsset.uploaded_at)).offset(skip).limit(limit).all()

    def get_by_type(
        self,
        media_type: MediaType,
        user_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[MediaAsset]:
        """
        Get media assets by type.

        Args:
            media_type: Media type filter
            user_id: Optional user ID filter
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of media assets
        """
        query = self.db.query(MediaAsset).filter(MediaAsset.media_type == media_type)

        if user_id:
            query = query.filter(MediaAsset.user_id == user_id)

        return query.order_by(desc(MediaAsset.uploaded_at)).offset(skip).limit(limit).all()

    def get_generated_assets(
        self,
        user_id: Optional[int] = None,
        provider: Optional[str] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[MediaAsset]:
        """
        Get AI-generated assets.

        Args:
            user_id: Optional user ID filter
            provider: Optional generation provider filter
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of AI-generated assets
        """
        query = self.db.query(MediaAsset).filter(MediaAsset.is_generated == 1)

        if user_id:
            query = query.filter(MediaAsset.user_id == user_id)

        if provider:
            query = query.filter(MediaAsset.generation_provider == provider)

        return query.order_by(desc(MediaAsset.uploaded_at)).offset(skip).limit(limit).all()

    def get_expired_assets(self) -> List[MediaAsset]:
        """
        Get all expired assets that can be deleted.

        Returns:
            List of expired assets
        """
        return (
            self.db.query(MediaAsset)
            .filter(
                and_(
                    MediaAsset.expires_at.isnot(None),
                    MediaAsset.expires_at < datetime.utcnow()
                )
            )
            .all()
        )

    def delete_expired(self) -> int:
        """
        Delete all expired assets.

        Returns:
            Number of assets deleted
        """
        expired = self.get_expired_assets()
        count = len(expired)

        for asset in expired:
            self.db.delete(asset)

        self.db.commit()
        logger.info(f"Deleted {count} expired media assets")
        return count

    def get_storage_stats(self, user_id: int) -> Dict[str, Any]:
        """
        Get storage statistics for a user.

        Args:
            user_id: User ID

        Returns:
            Dictionary with storage statistics
        """
        stats = {
            "total_files": 0,
            "total_size_bytes": 0,
            "total_size_mb": 0.0,
            "by_type": {}
        }

        # Total count and size
        result = (
            self.db.query(
                func.count(MediaAsset.id).label("count"),
                func.sum(MediaAsset.file_size).label("total_size")
            )
            .filter(MediaAsset.user_id == user_id)
            .first()
        )

        if result:
            stats["total_files"] = result.count or 0
            stats["total_size_bytes"] = result.total_size or 0
            stats["total_size_mb"] = round((result.total_size or 0) / (1024 * 1024), 2)

        # By type
        by_type = (
            self.db.query(
                MediaAsset.media_type,
                func.count(MediaAsset.id).label("count"),
                func.sum(MediaAsset.file_size).label("total_size")
            )
            .filter(MediaAsset.user_id == user_id)
            .group_by(MediaAsset.media_type)
            .all()
        )

        for media_type, count, total_size in by_type:
            stats["by_type"][media_type.value] = {
                "count": count,
                "size_bytes": total_size or 0,
                "size_mb": round((total_size or 0) / (1024 * 1024), 2)
            }

        return stats

    def get_project_storage_stats(self, project_id: int) -> Dict[str, Any]:
        """
        Get storage statistics for a project.

        Args:
            project_id: Project ID

        Returns:
            Dictionary with storage statistics
        """
        stats = {
            "total_files": 0,
            "total_size_bytes": 0,
            "total_size_mb": 0.0,
            "by_type": {}
        }

        # Total count and size
        result = (
            self.db.query(
                func.count(MediaAsset.id).label("count"),
                func.sum(MediaAsset.file_size).label("total_size")
            )
            .filter(MediaAsset.project_id == project_id)
            .first()
        )

        if result:
            stats["total_files"] = result.count or 0
            stats["total_size_bytes"] = result.total_size or 0
            stats["total_size_mb"] = round((result.total_size or 0) / (1024 * 1024), 2)

        # By type
        by_type = (
            self.db.query(
                MediaAsset.media_type,
                func.count(MediaAsset.id).label("count"),
                func.sum(MediaAsset.file_size).label("total_size")
            )
            .filter(MediaAsset.project_id == project_id)
            .group_by(MediaAsset.media_type)
            .all()
        )

        for media_type, count, total_size in by_type:
            stats["by_type"][media_type.value] = {
                "count": count,
                "size_bytes": total_size or 0,
                "size_mb": round((total_size or 0) / (1024 * 1024), 2)
            }

        return stats

    def get_generation_cost_total(self, user_id: int) -> int:
        """
        Get total generation cost for a user.

        Args:
            user_id: User ID

        Returns:
            Total cost in cents
        """
        result = (
            self.db.query(func.sum(MediaAsset.generation_cost))
            .filter(
                and_(
                    MediaAsset.user_id == user_id,
                    MediaAsset.is_generated == 1,
                    MediaAsset.generation_cost.isnot(None)
                )
            )
            .scalar()
        )

        return result or 0

    def get_by_filename(self, filename: str, user_id: Optional[int] = None) -> Optional[MediaAsset]:
        """
        Get asset by filename.

        Args:
            filename: Filename to search for
            user_id: Optional user ID filter

        Returns:
            MediaAsset or None
        """
        query = self.db.query(MediaAsset).filter(MediaAsset.filename == filename)

        if user_id:
            query = query.filter(MediaAsset.user_id == user_id)

        return query.first()

    def bulk_delete_by_scene(self, scene_id: int) -> int:
        """
        Delete all assets for a scene.

        Args:
            scene_id: Scene ID

        Returns:
            Number of assets deleted
        """
        assets = self.get_by_scene(scene_id, limit=10000)
        count = len(assets)

        for asset in assets:
            self.db.delete(asset)

        self.db.commit()
        logger.info(f"Deleted {count} assets for scene {scene_id}")
        return count

    def bulk_delete_by_project(self, project_id: int) -> int:
        """
        Delete all assets for a project.

        Args:
            project_id: Project ID

        Returns:
            Number of assets deleted
        """
        assets = self.get_by_project(project_id, limit=10000)
        count = len(assets)

        for asset in assets:
            self.db.delete(asset)

        self.db.commit()
        logger.info(f"Deleted {count} assets for project {project_id}")
        return count

    def get_with_relations(self, asset_id: int) -> Optional[MediaAsset]:
        """
        Get asset with all relationships loaded.

        Args:
            asset_id: Asset ID

        Returns:
            MediaAsset with relationships or None
        """
        return (
            self.db.query(MediaAsset)
            .options(
                joinedload(MediaAsset.user),
                joinedload(MediaAsset.project),
                joinedload(MediaAsset.scene)
            )
            .filter(MediaAsset.id == asset_id)
            .first()
        )
