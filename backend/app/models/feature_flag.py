"""
Feature flag model for CineCraft.
Allows runtime feature toggling and A/B testing.
"""
from sqlalchemy import Column, Integer, String, Boolean, Text, JSON
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class FeatureFlagType(str, enum.Enum):
    """Feature flag types."""
    BOOLEAN = "boolean"
    STRING = "string"
    NUMBER = "number"
    JSON = "json"


class FeatureFlagScope(str, enum.Enum):
    """Feature flag scopes."""
    GLOBAL = "global"  # Applies to all users
    USER = "user"  # Per-user override
    PLAN = "plan"  # Per-subscription plan
    ROLE = "role"  # Per-user role


class FeatureFlag(BaseModel):
    """
    Feature flag model for runtime configuration.

    Features can be toggled globally or per user/plan/role.
    """
    __tablename__ = "feature_flags"

    # Basic info
    key = Column(String(100), nullable=False, unique=True, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Flag configuration
    flag_type = Column(String(20), nullable=False, default=FeatureFlagType.BOOLEAN.value)
    scope = Column(String(20), nullable=False, default=FeatureFlagScope.GLOBAL.value)

    # Values for different types
    enabled = Column(Boolean, nullable=False, default=False)  # For BOOLEAN type
    value_string = Column(String(500), nullable=True)  # For STRING type
    value_number = Column(Integer, nullable=True)  # For NUMBER type
    value_json = Column(JSON, nullable=True)  # For JSON type

    # Scope filters
    target_user_ids = Column(JSON, nullable=True)  # List of user IDs [1, 2, 3]
    target_plan_ids = Column(JSON, nullable=True)  # List of plan IDs [1, 2]
    target_roles = Column(JSON, nullable=True)  # List of roles ["admin", "pro_user"]

    # Metadata
    category = Column(String(100), nullable=True)  # e.g., "rendering", "ai", "storage"
    tags = Column(JSON, nullable=True)  # List of tags ["beta", "experimental"]

    # Rollout percentage (0-100)
    rollout_percentage = Column(Integer, nullable=False, default=100)

    # Admin info
    created_by = Column(Integer, nullable=True)
    updated_by = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<FeatureFlag {self.key}={self.get_value()}>"

    def get_value(self):
        """
        Get the flag value based on its type.

        Returns:
            Flag value (bool, str, int, or dict)
        """
        if self.flag_type == FeatureFlagType.BOOLEAN:
            return self.enabled
        elif self.flag_type == FeatureFlagType.STRING:
            return self.value_string
        elif self.flag_type == FeatureFlagType.NUMBER:
            return self.value_number
        elif self.flag_type == FeatureFlagType.JSON:
            return self.value_json
        return None

    def set_value(self, value):
        """
        Set the flag value based on its type.

        Args:
            value: Value to set
        """
        if self.flag_type == FeatureFlagType.BOOLEAN:
            self.enabled = bool(value)
        elif self.flag_type == FeatureFlagType.STRING:
            self.value_string = str(value)
        elif self.flag_type == FeatureFlagType.NUMBER:
            self.value_number = int(value)
        elif self.flag_type == FeatureFlagType.JSON:
            self.value_json = value

    def is_enabled_for_user(self, user_id: int) -> bool:
        """
        Check if flag is enabled for specific user.

        Args:
            user_id: User ID

        Returns:
            True if enabled for user
        """
        if not self.enabled:
            return False

        # Check scope
        if self.scope == FeatureFlagScope.GLOBAL:
            return True

        if self.scope == FeatureFlagScope.USER:
            if self.target_user_ids:
                return user_id in self.target_user_ids
            return False

        # For PLAN and ROLE scopes, additional checks needed in service layer
        return True

    def is_in_rollout(self, user_id: int) -> bool:
        """
        Check if user is in rollout percentage.

        Uses consistent hashing so same user always gets same result.

        Args:
            user_id: User ID

        Returns:
            True if user is in rollout
        """
        if self.rollout_percentage == 100:
            return True

        if self.rollout_percentage == 0:
            return False

        # Consistent hash: user_id % 100 < rollout_percentage
        hash_value = user_id % 100
        return hash_value < self.rollout_percentage
