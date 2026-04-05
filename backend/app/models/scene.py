"""
Scene model for CineCraft.
Represents an individual scene within a project.
"""
from sqlalchemy import Column, Integer, String, Text, Float, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import BaseModel


class Scene(BaseModel):
    """
    Scene model.

    Represents a single scene within a video project.
    Contains scene description, narration, and links to generated media assets.
    """
    __tablename__ = "scenes"

    # Basic information
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    sequence_number = Column(Integer, nullable=False)  # Order of scene in project (1, 2, 3...)
    title = Column(String(255), nullable=True)

    # Scene content
    description = Column(Text, nullable=False)
    narration = Column(Text, nullable=True)  # Voice narration text

    # Visual details (for image generation)
    visual_description = Column(Text, nullable=True)
    video_prompt = Column(Text, nullable=True)
    emotion = Column(String(100), nullable=True)
    # Example: "A serene forest clearing at dawn with mist rising from the ground"

    # Scene metadata
    scene_metadata = Column(JSON, nullable=False, default=dict)
    # Example scene_metadata:
    # {
    #   "mood": "peaceful",
    #   "camera_angle": "wide shot",
    #   "lighting": "soft morning light",
    #   "setting": "forest",
    #   "characters_present": ["hero", "guide"]
    # }

    # Timing
    duration = Column(Float, nullable=True)  # Duration in seconds
    start_time = Column(Float, nullable=True)  # Start time in final video
    end_time = Column(Float, nullable=True)  # End time in final video

    # Generated media assets
    image_url = Column(String(500), nullable=True)  # Generated scene image
    image_prompt = Column(Text, nullable=True)  # Prompt used for image generation

    audio_url = Column(String(500), nullable=True)  # Voice narration audio
    audio_duration = Column(Float, nullable=True)  # Audio duration in seconds

    # Subtitle/Caption
    subtitle_text = Column(Text, nullable=True)
    subtitle_start_time = Column(Float, nullable=True)
    subtitle_end_time = Column(Float, nullable=True)

    # Generation timestamps
    image_generated_at = Column(DateTime, nullable=True)
    audio_generated_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project", back_populates="scenes")

    def __repr__(self):
        return f"<Scene(id={self.id}, project_id={self.project_id}, seq={self.sequence_number})>"

    @property
    def is_complete(self) -> bool:
        """Check if scene has all required media generated."""
        return (
            self.image_url is not None and
            self.audio_url is not None
        )

    @property
    def has_image(self) -> bool:
        """Check if scene has generated image."""
        return self.image_url is not None and self.image_generated_at is not None

    @property
    def has_audio(self) -> bool:
        """Check if scene has generated audio."""
        return self.audio_url is not None and self.audio_generated_at is not None

    def set_timing(self, start_time: float, duration: float):
        """
        Set scene timing in the final video.

        Args:
            start_time: Start time in seconds
            duration: Duration in seconds
        """
        self.start_time = start_time
        self.duration = duration
        self.end_time = start_time + duration
        self.updated_at = datetime.utcnow()

    def mark_image_generated(self, image_url: str, prompt: str = None):
        """
        Mark scene image as generated.

        Args:
            image_url: URL of generated image
            prompt: Prompt used for generation
        """
        self.image_url = image_url
        self.image_prompt = prompt
        self.image_generated_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()

    def mark_audio_generated(self, audio_url: str, duration: float = None):
        """
        Mark scene audio as generated.

        Args:
            audio_url: URL of generated audio
            duration: Audio duration in seconds
        """
        self.audio_url = audio_url
        self.audio_duration = duration
        self.audio_generated_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
