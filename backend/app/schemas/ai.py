"""
Pydantic schemas for AI generation operations.
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class GenerateStoryRequest(BaseModel):
    """Schema for story generation request."""
    project_id: int
    regenerate_scenes: bool = True
    regenerate_characters: bool = True


class GenerateStoryResponse(BaseModel):
    """Schema for story generation response."""
    project_id: int
    story: str
    story_length: int
    scenes: List[Dict[str, Any]]
    characters: List[Dict[str, Any]]
    status: str


class StoryOnlyRequest(BaseModel):
    """Schema for story-only generation request."""
    project_id: int


class StoryOnlyResponse(BaseModel):
    """Schema for story-only response."""
    project_id: int
    story: str
    story_length: int


class RegenerateScenesRequest(BaseModel):
    """Schema for scene regeneration request."""
    project_id: int


class RegenerateScenesResponse(BaseModel):
    """Schema for scene regeneration response."""
    project_id: int
    scenes: List[Dict[str, Any]]
    total: int


class RegenerateCharactersRequest(BaseModel):
    """Schema for character regeneration request."""
    project_id: int


class RegenerateCharactersResponse(BaseModel):
    """Schema for character regeneration response."""
    project_id: int
    characters: List[Dict[str, Any]]
    total: int


class GenerateProjectContentRequest(BaseModel):
    """Schema for full project content generation."""
    project_id: int
    include_story: bool = True
    include_scenes: bool = True
    include_characters: bool = True
    include_images: bool = False
    include_audio: bool = False
    include_music: bool = False


class GenerateProjectContentResponse(BaseModel):
    """Schema for project content generation response."""
    project_id: int
    generated: Dict[str, Any]


class ProviderTestResponse(BaseModel):
    """Schema for provider connection test response."""
    ai: bool
    image: bool
    voice: bool
    music: bool


class ProviderInfoResponse(BaseModel):
    """Schema for provider information response."""
    ai: Dict[str, Any]
    image: Dict[str, Any]
    voice: Dict[str, Any]
    music: Dict[str, Any]
