"""
Pydantic schemas for video rendering operations.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime


class RenderVideoRequest(BaseModel):
    """Schema for video render request."""
    project_id: int = Field(..., description="Project ID to render")
    width: int = Field(default=1920, ge=640, le=3840, description="Video width in pixels")
    height: int = Field(default=1080, ge=480, le=2160, description="Video height in pixels")
    fps: int = Field(default=30, ge=24, le=60, description="Frames per second")
    enable_ken_burns: bool = Field(default=True, description="Apply Ken Burns effect to images")
    music_volume: float = Field(default=0.3, ge=0.0, le=1.0, description="Background music volume (0.0-1.0)")
    enable_ducking: bool = Field(default=True, description="Enable audio ducking (lower music when voice plays)")
    enable_subtitles: bool = Field(default=True, description="Add subtitles to video")


class RenderVideoResponse(BaseModel):
    """Schema for video render response."""
    job_id: int
    status: str
    message: str = "Video rendering started successfully"


class RenderStatusResponse(BaseModel):
    """Schema for render status response."""
    job_id: int
    status: str
    progress: float = Field(..., ge=0.0, le=100.0, description="Progress percentage")
    current_stage: Optional[str] = None
    stages_completed: list[str] = []
    output_url: Optional[str] = None
    error_message: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None


class RenderResultResponse(BaseModel):
    """Schema for completed render result."""
    video_asset_id: int
    output_url: str
    duration_seconds: float
    file_size: int
    scene_count: int
    resolution: str
    metadata: Dict[str, Any] = {}


class CancelRenderResponse(BaseModel):
    """Schema for cancel render response."""
    job_id: int
    status: str
    message: str = "Render job cancelled successfully"


class RenderPresetsResponse(BaseModel):
    """Schema for render presets."""
    presets: Dict[str, Dict[str, Any]]


class RenderConfigResponse(BaseModel):
    """Schema for render configuration options."""
    resolutions: list[Dict[str, int]]
    fps_options: list[int]
    quality_presets: Dict[str, Dict[str, Any]]
    features: Dict[str, bool]
