"""
Pydantic schemas for Scene model.
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class SceneCreateRequest(BaseModel):
    """Schema for creating a new scene."""
    description: str = Field(..., min_length=1)
    narration: Optional[str] = None
    visual_description: Optional[str] = None
    video_prompt: Optional[str] = None
    emotion: Optional[str] = None
    title: Optional[str] = Field(None, max_length=255)
    metadata: Optional[Dict[str, Any]] = None


class SceneUpdateRequest(BaseModel):
    """Schema for updating a scene."""
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = Field(None, min_length=1)
    narration: Optional[str] = None
    visual_description: Optional[str] = None
    video_prompt: Optional[str] = None
    emotion: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    duration: Optional[float] = None
    subtitle_text: Optional[str] = None


class SceneResponse(BaseModel):
    """Schema for scene response."""
    id: int
    project_id: int
    sequence_number: int
    title: Optional[str] = None
    description: str
    narration: Optional[str] = None
    visual_description: Optional[str] = None
    video_prompt: Optional[str] = None
    emotion: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    duration: Optional[float] = None
    start_time: Optional[float] = None
    end_time: Optional[float] = None
    image_url: Optional[str] = None
    image_prompt: Optional[str] = None
    audio_url: Optional[str] = None
    audio_duration: Optional[float] = None
    subtitle_text: Optional[str] = None
    subtitle_start_time: Optional[float] = None
    subtitle_end_time: Optional[float] = None
    image_generated_at: Optional[datetime] = None
    audio_generated_at: Optional[datetime] = None
    is_complete: bool
    has_image: bool
    has_audio: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class SceneBulkCreateRequest(BaseModel):
    """Schema for bulk creating scenes."""
    scenes: List[SceneCreateRequest]


class SceneReorderRequest(BaseModel):
    """Schema for reordering scenes."""
    scene_order: List[int] = Field(..., min_length=1)


class SceneTimingRequest(BaseModel):
    """Schema for setting scene timing."""
    start_time: float = Field(..., ge=0)
    duration: float = Field(..., gt=0)


class SceneMediaGeneratedRequest(BaseModel):
    """Schema for marking scene media as generated."""
    image_url: Optional[str] = None
    audio_url: Optional[str] = None
    image_prompt: Optional[str] = None
    audio_duration: Optional[float] = None


class SceneListResponse(BaseModel):
    """Schema for scene list response."""
    scenes: List[SceneResponse]
    total: int
