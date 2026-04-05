"""
Character model for CineCraft.
Represents a character extracted from a story.
"""
from sqlalchemy import Column, Integer, String, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Character(BaseModel):
    """
    Character model.

    Represents a character identified in a story.
    Used for consistency in image generation and scene descriptions.
    """
    __tablename__ = "characters"

    # Basic information
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    role = Column(String(100), nullable=True)  # e.g., "protagonist", "antagonist", "mentor"

    # Character details (for image generation consistency)
    description = Column(Text, nullable=True)
    # Example: "A young woman in her 20s with long dark hair, wearing a traveler's cloak"

    appearance = Column(Text, nullable=True)
    # Detailed appearance for visual consistency across scenes

    personality = Column(Text, nullable=True)
    # Character traits for story consistency

    # Character metadata
    character_metadata = Column(JSON, nullable=False, default=dict)
    # Example character_metadata:
    # {
    #   "age": "mid-20s",
    #   "gender": "female",
    #   "species": "human",
    #   "occupation": "adventurer",
    #   "traits": ["brave", "curious", "determined"],
    #   "relationships": {"guide": "mentor"}
    # }

    # Visual reference (for image generation)
    reference_image_url = Column(String(500), nullable=True)
    # Reference image for maintaining visual consistency

    visual_prompt = Column(Text, nullable=True)
    # Standardized prompt for generating this character in scenes

    # Relationships
    project = relationship("Project", back_populates="characters")

    def __repr__(self):
        return f"<Character(id={self.id}, name='{self.name}', role='{self.role}')>"

    @property
    def has_visual_reference(self) -> bool:
        """Check if character has visual reference."""
        return self.reference_image_url is not None or self.visual_prompt is not None

    def get_full_description(self) -> str:
        """
        Get complete character description for prompts.

        Returns:
            Combined description including name, role, appearance, and traits
        """
        parts = [f"{self.name}"]

        if self.role:
            parts.append(f"({self.role})")

        if self.appearance:
            parts.append(f": {self.appearance}")
        elif self.description:
            parts.append(f": {self.description}")

        if self.personality:
            parts.append(f"Personality: {self.personality}")

        return " ".join(parts)
