"""
Pydantic schemas for storage and media asset operations.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime

from app.models.media_asset import MediaType


class MediaAssetBase(BaseModel):
    """Base schema for media assets."""
    filename: str
    original_filename: Optional[str] = None
    media_type: MediaType
    metadata: Optional[Dict[str, Any]] = {}


class MediaAssetCreate(MediaAssetBase):
    """Schema for creating a media asset."""
    user_id: int
    project_id: Optional[int] = None
    scene_id: Optional[int] = None
    file_path: str
    file_size: int
    mime_type: str
    storage_provider: str = "local"
    url: Optional[str] = None
    is_generated: bool = False
    generation_provider: Optional[str] = None
    generation_prompt: Optional[str] = None
    generation_cost: Optional[int] = None
    expires_at: Optional[datetime] = None


class MediaAssetResponse(BaseModel):
    """Schema for media asset response."""
    id: int
    user_id: int
    project_id: Optional[int]
    scene_id: Optional[int]
    filename: str
    original_filename: Optional[str]
    file_path: str
    file_size: int
    file_size_mb: float
    mime_type: str
    media_type: MediaType
    storage_provider: str
    url: Optional[str]
    cdn_url: Optional[str]
    width: Optional[int]
    height: Optional[int]
    duration: Optional[int]
    metadata: Dict[str, Any]
    is_generated: bool
    generation_provider: Optional[str]
    generation_prompt: Optional[str]
    generation_cost: Optional[int]
    uploaded_at: datetime
    expires_at: Optional[datetime]
    is_expired: bool

    class Config:
        from_attributes = True


class UploadRequest(BaseModel):
    """Schema for file upload request."""
    project_id: Optional[int] = None
    scene_id: Optional[int] = None
    media_type: Optional[MediaType] = None
    metadata: Optional[Dict[str, Any]] = {}
    expires_in_days: Optional[int] = None


class UploadResponse(BaseModel):
    """Schema for file upload response."""
    asset: MediaAssetResponse
    message: str = "File uploaded successfully"


class PresignedUrlRequest(BaseModel):
    """Schema for presigned URL request."""
    asset_id: int
    expiry: int = Field(default=3600, ge=60, le=86400)  # 1 minute to 24 hours


class PresignedUrlResponse(BaseModel):
    """Schema for presigned URL response."""
    asset_id: int
    url: str
    expires_in: int


class DeleteAssetResponse(BaseModel):
    """Schema for asset deletion response."""
    asset_id: int
    deleted: bool
    message: str


class StorageStatsResponse(BaseModel):
    """Schema for storage statistics response."""
    total_files: int
    total_size_bytes: int
    total_size_mb: float
    by_type: Dict[str, Dict[str, Any]]


class MediaAssetListResponse(BaseModel):
    """Schema for paginated media asset list."""
    assets: list[MediaAssetResponse]
    total: int
    skip: int
    limit: int


class GeneratedAssetRequest(BaseModel):
    """Schema for saving generated asset."""
    filename: str
    user_id: int
    project_id: int
    scene_id: Optional[int] = None
    media_type: MediaType
    generation_provider: str
    generation_prompt: Optional[str] = None
    generation_cost: Optional[int] = None
    metadata: Optional[Dict[str, Any]] = {}


class StorageProviderInfoResponse(BaseModel):
    """Schema for storage provider information."""
    provider: str
    base_path: Optional[str] = None
    base_url: Optional[str] = None
    bucket: Optional[str] = None
    region: Optional[str] = None
    total_files: Optional[int] = None
    total_size_bytes: Optional[int] = None
    total_size_mb: Optional[float] = None
    status: Optional[str] = None
    message: Optional[str] = None
