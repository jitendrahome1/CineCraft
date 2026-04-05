"""
Pydantic schemas for Project model.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from app.models.project import ProjectStatus


class CharacterResponse(BaseModel):
    """Schema for character in project response."""
    id: int
    name: str
    role: Optional[str] = None
    description: Optional[str] = None
    appearance: Optional[str] = None

    class Config:
        from_attributes = True


class SceneSummaryResponse(BaseModel):
    """Schema for scene summary in project response."""
    id: int
    sequence_number: int
    title: Optional[str] = None
    description: str
    has_image: bool
    has_audio: bool
    duration: Optional[float] = None
    video_prompt: Optional[str] = None
    emotion: Optional[str] = None

    class Config:
        from_attributes = True


class ProjectCreateRequest(BaseModel):
    """Schema for creating a new project."""
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    story_prompt: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    language: Optional[str] = "english"
    video_length: Optional[str] = "short"


class ProjectUpdateRequest(BaseModel):
    """Schema for updating a project."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    story_prompt: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    is_public: Optional[bool] = None


class ProjectResponse(BaseModel):
    """Schema for project response."""
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    status: ProjectStatus
    story: Optional[str] = None
    story_prompt: Optional[str] = None
    metadata: Dict[str, Any] = Field(alias='project_metadata')
    video_duration: Optional[int] = None
    language: Optional[str] = None
    video_length: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    views_count: int
    likes_count: int
    is_public: bool
    is_archived: bool
    scene_count: int
    created_at: datetime
    updated_at: datetime
    story_generated_at: Optional[datetime] = None
    scenes_generated_at: Optional[datetime] = None
    media_generated_at: Optional[datetime] = None
    rendered_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        populate_by_name = True


class ProjectDetailResponse(BaseModel):
    """Schema for detailed project response with scenes and characters."""
    id: int
    user_id: int
    title: str
    description: Optional[str] = None
    status: ProjectStatus
    story: Optional[str] = None
    story_prompt: Optional[str] = None
    metadata: Dict[str, Any] = Field(alias='project_metadata')
    video_duration: Optional[int] = None
    language: Optional[str] = None
    video_length: Optional[str] = None
    video_url: Optional[str] = None
    thumbnail_url: Optional[str] = None
    views_count: int
    likes_count: int
    is_public: bool
    is_archived: bool
    created_at: datetime
    updated_at: datetime
    story_generated_at: Optional[datetime] = None
    scenes_generated_at: Optional[datetime] = None
    media_generated_at: Optional[datetime] = None
    rendered_at: Optional[datetime] = None

    # Related data
    scenes: List[SceneSummaryResponse] = []
    characters: List[CharacterResponse] = []

    class Config:
        from_attributes = True
        populate_by_name = True


class ProjectStatsResponse(BaseModel):
    """Schema for project statistics."""
    project_id: int
    status: ProjectStatus
    scene_count: int
    complete_scenes: int
    character_count: int
    has_story: bool
    has_video: bool
    views_count: int
    is_public: bool


class ProjectVisibilityRequest(BaseModel):
    """Schema for updating project visibility."""
    is_public: bool


class ProjectListResponse(BaseModel):
    """Schema for project list with pagination."""
    projects: List[ProjectResponse]
    total: int
    skip: int
    limit: int
