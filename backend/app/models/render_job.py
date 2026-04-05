"""
RenderJob model for CineCraft.
Tracks video rendering jobs and their status.
"""
from sqlalchemy import Column, Integer, String, ForeignKey, Enum as SQLEnum, JSON, DateTime, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.models.base import BaseModel


class JobStatus(str, enum.Enum):
    """Job status enumeration."""
    PENDING = "pending"
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, enum.Enum):
    """Job type enumeration."""
    STORY_GENERATION = "story_generation"
    IMAGE_GENERATION = "image_generation"
    VOICE_GENERATION = "voice_generation"
    MUSIC_GENERATION = "music_generation"
    VIDEO_RENDERING = "video_rendering"
    FULL_GENERATION = "full_generation"


class RenderJob(BaseModel):
    """
    RenderJob model.

    Represents an asynchronous job for generating media or rendering videos.
    """
    __tablename__ = "render_jobs"

    # Ownership
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)

    # Job information
    job_type = Column(SQLEnum(JobType), nullable=False, index=True)
    status = Column(SQLEnum(JobStatus), nullable=False, default=JobStatus.PENDING, index=True)

    # Celery task tracking
    task_id = Column(String(255), nullable=True, index=True, unique=True)  # Celery task ID
    task_name = Column(String(255), nullable=True)  # Task name for debugging

    # Progress tracking
    progress = Column(Float, nullable=False, default=0.0)  # 0.0 to 100.0
    current_stage = Column(String(100), nullable=True)  # Current processing stage
    stages_completed = Column(JSON, nullable=False, default=list)  # List of completed stages

    # Result information
    result_data = Column(JSON, nullable=True)  # Job result data
    output_path = Column(String(500), nullable=True)  # Path to output file
    output_url = Column(String(500), nullable=True)  # URL to output file

    # Error tracking
    error_message = Column(String(1000), nullable=True)
    error_details = Column(JSON, nullable=True)
    retry_count = Column(Integer, nullable=False, default=0)

    # Configuration
    config = Column(JSON, nullable=False, default=dict)  # Job configuration
    # Example config:
    # {
    #   "resolution": "1920x1080",
    #   "fps": 30,
    #   "format": "mp4",
    #   "quality": "high",
    #   "include_subtitles": true
    # }

    # Performance metrics
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    duration_seconds = Column(Float, nullable=True)  # Total processing time

    # Priority
    priority = Column(Integer, nullable=False, default=5)  # 0-9, higher = more important

    # Relationships
    user = relationship("User", back_populates="render_jobs")
    project = relationship("Project", back_populates="render_jobs")

    def __repr__(self):
        return f"<RenderJob(id={self.id}, type='{self.job_type}', status='{self.status}')>"

    def start(self):
        """Mark job as started."""
        self.status = JobStatus.PROCESSING
        self.started_at = datetime.utcnow()

    def complete(self, result_data: dict = None, output_path: str = None, output_url: str = None):
        """
        Mark job as completed.

        Args:
            result_data: Job result data
            output_path: Path to output file
            output_url: URL to output file
        """
        self.status = JobStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        self.progress = 100.0

        if result_data:
            self.result_data = result_data
        if output_path:
            self.output_path = output_path
        if output_url:
            self.output_url = output_url

        if self.started_at:
            duration = (self.completed_at - self.started_at).total_seconds()
            self.duration_seconds = duration

    def fail(self, error_message: str, error_details: dict = None):
        """
        Mark job as failed.

        Args:
            error_message: Error message
            error_details: Optional error details
        """
        self.status = JobStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.error_message = error_message

        if error_details:
            self.error_details = error_details

        if self.started_at:
            duration = (self.completed_at - self.started_at).total_seconds()
            self.duration_seconds = duration

    def cancel(self):
        """Mark job as cancelled."""
        self.status = JobStatus.CANCELLED
        self.completed_at = datetime.utcnow()

        if self.started_at:
            duration = (self.completed_at - self.started_at).total_seconds()
            self.duration_seconds = duration

    def update_progress(self, progress: float, stage: str = None):
        """
        Update job progress.

        Args:
            progress: Progress percentage (0-100)
            stage: Current processing stage
        """
        self.progress = min(100.0, max(0.0, progress))

        if stage:
            self.current_stage = stage
            if stage not in self.stages_completed:
                stages = self.stages_completed or []
                stages.append(stage)
                self.stages_completed = stages

    @property
    def is_running(self) -> bool:
        """Check if job is currently running."""
        return self.status in [JobStatus.QUEUED, JobStatus.PROCESSING]

    @property
    def is_finished(self) -> bool:
        """Check if job is finished (completed, failed, or cancelled)."""
        return self.status in [JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED]

    @property
    def is_successful(self) -> bool:
        """Check if job completed successfully."""
        return self.status == JobStatus.COMPLETED

    @property
    def duration_formatted(self) -> str:
        """Get formatted duration string."""
        if not self.duration_seconds:
            return "N/A"

        duration = int(self.duration_seconds)
        hours = duration // 3600
        minutes = (duration % 3600) // 60
        seconds = duration % 60

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"


# Add relationships to other models
from app.models.user import User
from app.models.project import Project

User.render_jobs = relationship(
    "RenderJob",
    back_populates="user",
    cascade="all, delete-orphan"
)

Project.render_jobs = relationship(
    "RenderJob",
    back_populates="project",
    cascade="all, delete-orphan"
)
