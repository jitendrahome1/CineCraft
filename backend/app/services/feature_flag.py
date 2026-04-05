"""
Feature flag service for CineCraft.
Business logic for feature flag evaluation and management.
"""
from typing import Optional, Any, Dict, List
from sqlalchemy.orm import Session

from app.repositories.feature_flag import FeatureFlagRepository
from app.repositories.user import UserRepository
from app.repositories.subscription import SubscriptionRepository
from app.models.feature_flag import FeatureFlag, FeatureFlagScope
from app.core.logging import get_logger

logger = get_logger(__name__)


class FeatureFlagService:
    """Service for feature flag operations."""

    def __init__(self, db: Session):
        self.db = db
        self.flag_repo = FeatureFlagRepository(db)
        self.user_repo = UserRepository(db)
        self.subscription_repo = SubscriptionRepository(db)

    def is_enabled(
        self,
        key: str,
        user_id: Optional[int] = None,
        default: bool = False
    ) -> bool:
        """
        Check if feature flag is enabled.

        Args:
            key: Feature flag key
            user_id: Optional user ID for user-specific checks
            default: Default value if flag not found

        Returns:
            True if enabled, False otherwise
        """
        flag = self.flag_repo.get_by_key(key)

        if not flag:
            logger.debug(f"Feature flag '{key}' not found, using default: {default}")
            return default

        # Check if flag is globally enabled
        if not flag.enabled:
            return False

        # Global scope - enabled for everyone
        if flag.scope == FeatureFlagScope.GLOBAL:
            if user_id:
                return flag.is_in_rollout(user_id)
            return True

        # User-specific checks
        if user_id:
            # Check rollout percentage
            if not flag.is_in_rollout(user_id):
                return False

            # User scope
            if flag.scope == FeatureFlagScope.USER:
                return flag.is_enabled_for_user(user_id)

            # Plan scope
            if flag.scope == FeatureFlagScope.PLAN:
                subscription = self.subscription_repo.get_active_by_user(user_id)
                if subscription and flag.target_plan_ids:
                    return subscription.plan_id in flag.target_plan_ids
                return False

            # Role scope
            if flag.scope == FeatureFlagScope.ROLE:
                user = self.user_repo.get(user_id)
                if user and flag.target_roles:
                    return user.role.value in flag.target_roles
                return False

        return False

    def get_value(
        self,
        key: str,
        user_id: Optional[int] = None,
        default: Any = None
    ) -> Any:
        """
        Get feature flag value.

        Args:
            key: Feature flag key
            user_id: Optional user ID for user-specific checks
            default: Default value if flag not found or disabled

        Returns:
            Flag value or default
        """
        if not self.is_enabled(key, user_id, default=False):
            return default

        flag = self.flag_repo.get_by_key(key)
        if flag:
            return flag.get_value()

        return default

    def get_all_for_user(self, user_id: int) -> Dict[str, Any]:
        """
        Get all enabled feature flags for a user.

        Args:
            user_id: User ID

        Returns:
            Dictionary of {key: value} for all enabled flags
        """
        flags = {}

        # Get user info
        user = self.user_repo.get(user_id)
        if not user:
            return flags

        subscription = self.subscription_repo.get_active_by_user(user_id)

        # Get all enabled flags
        all_flags = self.flag_repo.get_enabled_flags(limit=1000)

        for flag in all_flags:
            # Check if flag applies to user
            enabled = False

            if flag.scope == FeatureFlagScope.GLOBAL:
                enabled = flag.is_in_rollout(user_id)

            elif flag.scope == FeatureFlagScope.USER:
                enabled = flag.is_enabled_for_user(user_id) and flag.is_in_rollout(user_id)

            elif flag.scope == FeatureFlagScope.PLAN and subscription:
                if flag.target_plan_ids and subscription.plan_id in flag.target_plan_ids:
                    enabled = flag.is_in_rollout(user_id)

            elif flag.scope == FeatureFlagScope.ROLE:
                if flag.target_roles and user.role.value in flag.target_roles:
                    enabled = flag.is_in_rollout(user_id)

            if enabled:
                flags[flag.key] = flag.get_value()

        return flags

    def create_flag(
        self,
        key: str,
        name: str,
        description: Optional[str] = None,
        enabled: bool = False,
        created_by: Optional[int] = None,
        **kwargs
    ) -> FeatureFlag:
        """
        Create a new feature flag.

        Args:
            key: Unique flag key
            name: Flag name
            description: Flag description
            enabled: Initial enabled state
            created_by: User ID who created the flag
            **kwargs: Additional flag attributes

        Returns:
            Created feature flag
        """
        data = {
            "key": key,
            "name": name,
            "description": description,
            "enabled": enabled,
            "created_by": created_by,
            **kwargs
        }

        return self.flag_repo.create(data)

    def update_flag(
        self,
        flag_id: int,
        updated_by: Optional[int] = None,
        **kwargs
    ) -> FeatureFlag:
        """
        Update feature flag.

        Args:
            flag_id: Flag ID
            updated_by: User ID who updated the flag
            **kwargs: Fields to update

        Returns:
            Updated feature flag
        """
        if updated_by:
            kwargs['updated_by'] = updated_by

        flag = self.flag_repo.get(flag_id)
        return self.flag_repo.update(flag, kwargs)

    def toggle_flag(self, flag_id: int, updated_by: Optional[int] = None) -> FeatureFlag:
        """
        Toggle feature flag enabled state.

        Args:
            flag_id: Flag ID
            updated_by: User ID who toggled the flag

        Returns:
            Updated feature flag
        """
        flag = self.flag_repo.toggle(flag_id)

        if flag and updated_by:
            flag.updated_by = updated_by
            self.db.commit()
            self.db.refresh(flag)

        logger.info(f"Feature flag {flag.key} toggled to {flag.enabled} by user {updated_by}")

        return flag

    def set_rollout(
        self,
        flag_id: int,
        percentage: int,
        updated_by: Optional[int] = None
    ) -> FeatureFlag:
        """
        Set rollout percentage.

        Args:
            flag_id: Flag ID
            percentage: Rollout percentage (0-100)
            updated_by: User ID who updated the rollout

        Returns:
            Updated feature flag
        """
        flag = self.flag_repo.set_rollout_percentage(flag_id, percentage)

        if flag and updated_by:
            flag.updated_by = updated_by
            self.db.commit()
            self.db.refresh(flag)

        logger.info(f"Feature flag {flag.key} rollout set to {percentage}% by user {updated_by}")

        return flag

    def delete_flag(self, flag_id: int) -> bool:
        """
        Delete feature flag.

        Args:
            flag_id: Flag ID

        Returns:
            True if deleted
        """
        logger.warning(f"Deleting feature flag {flag_id}")
        return self.flag_repo.delete(flag_id)

    def get_stats(self) -> Dict[str, Any]:
        """
        Get feature flag statistics.

        Returns:
            Statistics dictionary
        """
        return self.flag_repo.get_stats()

    def get_all_flags(
        self,
        category: Optional[str] = None,
        enabled_only: bool = False,
        skip: int = 0,
        limit: int = 100
    ) -> List[FeatureFlag]:
        """
        Get all feature flags with optional filtering.

        Args:
            category: Filter by category
            enabled_only: Only return enabled flags
            skip: Number to skip
            limit: Maximum number to return

        Returns:
            List of feature flags
        """
        if category:
            return self.flag_repo.get_by_category(category, skip, limit)
        elif enabled_only:
            return self.flag_repo.get_enabled_flags(skip, limit)
        else:
            return self.flag_repo.get_all(skip, limit)
