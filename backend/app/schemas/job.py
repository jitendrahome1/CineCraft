"""
Pydantic schemas for render job operations.
"""
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.models.render_job import JobStatus, JobType


class JobCreate(BaseModel):
    """Schema for creating a render job."""
    project_id: int
    job_type: JobType
    config: Optional[Dict[str, Any]] = {}
    priority: int = Field(default=5, ge=0, le=9)


class JobResponse(BaseModel):
    """Schema for render job response."""
    id: int
    user_id: int
    project_id: int
    job_type: JobType
    status: JobStatus
    task_id: Optional[str]
    progress: float
    current_stage: Optional[str]
    stages_completed: List[str]
    result_data: Optional[Dict[str, Any]]
    output_path: Optional[str]
    output_url: Optional[str]
    error_message: Optional[str]
    retry_count: int
    config: Dict[str, Any]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_seconds: Optional[float]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class JobListResponse(BaseModel):
    """Schema for paginated job list."""
    jobs: List[JobResponse]
    total: int
    skip: int
    limit: int


class JobStatsResponse(BaseModel):
    """Schema for job statistics."""
    total: int
    pending: int
    queued: int
    processing: int
    completed: int
    failed: int
    cancelled: int
    avg_duration_seconds: float
    by_type: Dict[str, int]


class StartJobRequest(BaseModel):
    """Schema for starting a job."""
    job_type: JobType
    project_id: int
    config: Optional[Dict[str, Any]] = {}


class StartJobResponse(BaseModel):
    """Schema for start job response."""
    job: JobResponse
    message: str = "Job started successfully"
