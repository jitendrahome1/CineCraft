"""
Storage API endpoints.
Handles file uploads, downloads, and media asset management.
"""
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import Optional
import io

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.media_asset import MediaType
from app.services.storage import StorageService
from app.providers.storage.factory import get_storage_provider_from_config
from app.schemas.storage import (
    UploadResponse,
    PresignedUrlRequest,
    PresignedUrlResponse,
    DeleteAssetResponse,
    StorageStatsResponse,
    MediaAssetListResponse,
    MediaAssetResponse,
    StorageProviderInfoResponse
)
from app.core.errors import ValidationError
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


def get_storage_service(db: Session = Depends(get_db)) -> StorageService:
    """
    Dependency to get storage service.

    Args:
        db: Database session

    Returns:
        Storage service instance
    """
    storage_provider = get_storage_provider_from_config()
    return StorageService(db=db, storage_provider=storage_provider)


@router.post("/upload", response_model=UploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    project_id: Optional[int] = Form(None),
    scene_id: Optional[int] = Form(None),
    media_type: Optional[str] = Form(None),
    expires_in_days: Optional[int] = Form(None),
    current_user: User = Depends(get_current_user),
    storage_service: StorageService = Depends(get_storage_service)
):
    """
    Upload a file.

    Args:
        file: File to upload
        project_id: Optional project ID
        scene_id: Optional scene ID
        media_type: Optional media type
        expires_in_days: Optional expiration in days
        current_user: Current user
        storage_service: Storage service

    Returns:
        Upload response with asset details

    Raises:
        HTTPException: If upload fails
    """
    try:
        # Read file contents
        file_data = await file.read()

        # Convert media_type string to enum if provided
        media_type_enum = None
        if media_type:
            try:
                media_type_enum = MediaType(media_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid media type: {media_type}"
                )

        # Upload file
        asset = await storage_service.upload_file(
            file_data=file_data,
            filename=file.filename,
            user_id=current_user.id,
            project_id=project_id,
            scene_id=scene_id,
            media_type=media_type_enum,
            expires_in_days=expires_in_days
        )

        return UploadResponse(
            asset=MediaAssetResponse.model_validate(asset),
            message="File uploaded successfully"
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("Upload failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.get("/assets", response_model=MediaAssetListResponse)
async def list_assets(
    project_id: Optional[int] = None,
    scene_id: Optional[int] = None,
    media_type: Optional[str] = None,
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(get_current_user),
    storage_service: StorageService = Depends(get_storage_service)
):
    """
    List user's media assets.

    Args:
        project_id: Optional project filter
        scene_id: Optional scene filter
        media_type: Optional media type filter
        skip: Pagination offset
        limit: Pagination limit
        current_user: Current user
        storage_service: Storage service

    Returns:
        List of media assets

    Raises:
        HTTPException: If listing fails
    """
    try:
        # Convert media_type string to enum if provided
        media_type_enum = None
        if media_type:
            try:
                media_type_enum = MediaType(media_type)
            except ValueError:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Invalid media type: {media_type}"
                )

        # Get assets based on filters
        if scene_id:
            assets = storage_service.repository.get_by_scene(
                scene_id=scene_id,
                skip=skip,
                limit=limit,
                media_type=media_type_enum
            )
        elif project_id:
            assets = storage_service.repository.get_by_project(
                project_id=project_id,
                skip=skip,
                limit=limit,
                media_type=media_type_enum
            )
        else:
            assets = storage_service.repository.get_by_user(
                user_id=current_user.id,
                skip=skip,
                limit=limit,
                media_type=media_type_enum
            )

        # Get total count
        filters = {"user_id": current_user.id}
        if project_id:
            filters["project_id"] = project_id
        if scene_id:
            filters["scene_id"] = scene_id
        if media_type_enum:
            filters["media_type"] = media_type_enum

        total = storage_service.repository.count(filters)

        return MediaAssetListResponse(
            assets=[MediaAssetResponse.model_validate(a) for a in assets],
            total=total,
            skip=skip,
            limit=limit
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to list assets")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list assets: {str(e)}"
        )


@router.get("/assets/{asset_id}", response_model=MediaAssetResponse)
async def get_asset(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    storage_service: StorageService = Depends(get_storage_service)
):
    """
    Get media asset details.

    Args:
        asset_id: Asset ID
        current_user: Current user
        storage_service: Storage service

    Returns:
        Media asset details

    Raises:
        HTTPException: If asset not found or unauthorized
    """
    asset = storage_service.repository.get(asset_id)

    if not asset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Asset {asset_id} not found"
        )

    if asset.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized access to asset"
        )

    return MediaAssetResponse.model_validate(asset)


@router.get("/assets/{asset_id}/download")
async def download_asset(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    storage_service: StorageService = Depends(get_storage_service)
):
    """
    Download media asset file.

    Args:
        asset_id: Asset ID
        current_user: Current user
        storage_service: Storage service

    Returns:
        File stream

    Raises:
        HTTPException: If asset not found or download fails
    """
    try:
        file_data = await storage_service.get_file(
            asset_id=asset_id,
            user_id=current_user.id
        )

        asset = storage_service.repository.get(asset_id)

        return StreamingResponse(
            io.BytesIO(file_data),
            media_type=asset.mime_type,
            headers={
                "Content-Disposition": f'attachment; filename="{asset.original_filename or asset.filename}"'
            }
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("Download failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Download failed: {str(e)}"
        )


@router.post("/assets/{asset_id}/presigned-url", response_model=PresignedUrlResponse)
async def get_presigned_url(
    asset_id: int,
    expiry: int = 3600,
    current_user: User = Depends(get_current_user),
    storage_service: StorageService = Depends(get_storage_service)
):
    """
    Get presigned URL for asset.

    Args:
        asset_id: Asset ID
        expiry: URL expiry in seconds (default: 3600)
        current_user: Current user
        storage_service: Storage service

    Returns:
        Presigned URL response

    Raises:
        HTTPException: If asset not found or generation fails
    """
    try:
        url = await storage_service.get_presigned_url(
            asset_id=asset_id,
            user_id=current_user.id,
            expiry=expiry
        )

        return PresignedUrlResponse(
            asset_id=asset_id,
            url=url,
            expires_in=expiry
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("Presigned URL generation failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate presigned URL: {str(e)}"
        )


@router.delete("/assets/{asset_id}", response_model=DeleteAssetResponse)
async def delete_asset(
    asset_id: int,
    current_user: User = Depends(get_current_user),
    storage_service: StorageService = Depends(get_storage_service)
):
    """
    Delete media asset.

    Args:
        asset_id: Asset ID
        current_user: Current user
        storage_service: Storage service

    Returns:
        Deletion response

    Raises:
        HTTPException: If asset not found or deletion fails
    """
    try:
        deleted = await storage_service.delete_asset(
            asset_id=asset_id,
            user_id=current_user.id
        )

        return DeleteAssetResponse(
            asset_id=asset_id,
            deleted=deleted,
            message="Asset deleted successfully" if deleted else "Failed to delete asset"
        )

    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.exception("Deletion failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Deletion failed: {str(e)}"
        )


@router.get("/stats", response_model=StorageStatsResponse)
async def get_storage_stats(
    project_id: Optional[int] = None,
    current_user: User = Depends(get_current_user),
    storage_service: StorageService = Depends(get_storage_service)
):
    """
    Get storage statistics.

    Args:
        project_id: Optional project ID filter
        current_user: Current user
        storage_service: Storage service

    Returns:
        Storage statistics

    Raises:
        HTTPException: If retrieval fails
    """
    try:
        if project_id:
            stats = storage_service.get_project_storage_stats(project_id)
        else:
            stats = storage_service.get_user_storage_stats(current_user.id)

        return StorageStatsResponse(**stats)

    except Exception as e:
        logger.exception("Failed to get storage stats")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get storage stats: {str(e)}"
        )


@router.get("/provider/info", response_model=StorageProviderInfoResponse)
async def get_provider_info(
    storage_service: StorageService = Depends(get_storage_service)
):
    """
    Get storage provider information.

    Args:
        storage_service: Storage service

    Returns:
        Storage provider information
    """
    try:
        info = storage_service.storage_provider.get_storage_info()
        return StorageProviderInfoResponse(**info)

    except Exception as e:
        logger.exception("Failed to get provider info")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get provider info: {str(e)}"
        )
