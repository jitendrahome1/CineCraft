"""
Feature flag repository for CineCraft.
Data access layer for feature flags.
"""
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session

from app.repositories.base import BaseRepository
from app.models.feature_flag import FeatureFlag, FeatureFlagType, FeatureFlagScope


class FeatureFlagRepository(BaseRepository[FeatureFlag]):
    """Repository for feature flag operations."""

    def __init__(self, db: Session):
        super().__init__(FeatureFlag, db)

    def get_by_key(self, key: str) -> Optional[FeatureFlag]:
        """
        Get feature flag by key.

        Args:
            key: Feature flag key

        Returns:
            FeatureFlag or None
        """
        return self.db.query(FeatureFlag).filter(
            FeatureFlag.key == key
        ).first()

    def get_by_category(
        self,
        category: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[FeatureFlag]:
        """
        Get feature flags by category.

        Args:
            category: Category name
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of feature flags
        """
        return self.db.query(FeatureFlag).filter(
            FeatureFlag.category == category
        ).offset(skip).limit(limit).all()

    def get_enabled_flags(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[FeatureFlag]:
        """
        Get all enabled feature flags.

        Args:
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of enabled feature flags
        """
        return self.db.query(FeatureFlag).filter(
            FeatureFlag.enabled == True
        ).offset(skip).limit(limit).all()

    def get_by_scope(
        self,
        scope: FeatureFlagScope,
        skip: int = 0,
        limit: int = 100
    ) -> List[FeatureFlag]:
        """
        Get feature flags by scope.

        Args:
            scope: Feature flag scope
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            List of feature flags
        """
        return self.db.query(FeatureFlag).filter(
            FeatureFlag.scope == scope.value
        ).offset(skip).limit(limit).all()

    def get_flags_for_user(self, user_id: int) -> List[FeatureFlag]:
        """
        Get all flags that apply to a specific user.

        Args:
            user_id: User ID

        Returns:
            List of applicable feature flags
        """
        # Get global flags
        global_flags = self.db.query(FeatureFlag).filter(
            FeatureFlag.scope == FeatureFlagScope.GLOBAL.value,
            FeatureFlag.enabled == True
        ).all()

        # Get user-specific flags
        user_flags = self.db.query(FeatureFlag).filter(
            FeatureFlag.scope == FeatureFlagScope.USER.value,
            FeatureFlag.enabled == True,
            FeatureFlag.target_user_ids.contains([user_id])
        ).all()

        return global_flags + user_flags

    def get_flags_for_plan(self, plan_id: int) -> List[FeatureFlag]:
        """
        Get all flags that apply to a specific plan.

        Args:
            plan_id: Plan ID

        Returns:
            List of applicable feature flags
        """
        return self.db.query(FeatureFlag).filter(
            FeatureFlag.scope == FeatureFlagScope.PLAN.value,
            FeatureFlag.enabled == True,
            FeatureFlag.target_plan_ids.contains([plan_id])
        ).all()

    def get_flags_for_role(self, role: str) -> List[FeatureFlag]:
        """
        Get all flags that apply to a specific role.

        Args:
            role: Role name

        Returns:
            List of applicable feature flags
        """
        return self.db.query(FeatureFlag).filter(
            FeatureFlag.scope == FeatureFlagScope.ROLE.value,
            FeatureFlag.enabled == True,
            FeatureFlag.target_roles.contains([role])
        ).all()

    def create_or_update(self, key: str, data: Dict[str, Any]) -> FeatureFlag:
        """
        Create or update feature flag.

        Args:
            key: Feature flag key
            data: Flag data

        Returns:
            Created or updated feature flag
        """
        flag = self.get_by_key(key)

        if flag:
            # Update existing
            for field, value in data.items():
                if hasattr(flag, field):
                    setattr(flag, field, value)
            self.db.commit()
            self.db.refresh(flag)
        else:
            # Create new
            data['key'] = key
            flag = self.create(data)

        return flag

    def toggle(self, flag_id: int) -> FeatureFlag:
        """
        Toggle feature flag enabled state.

        Args:
            flag_id: Feature flag ID

        Returns:
            Updated feature flag
        """
        flag = self.get(flag_id)
        if flag:
            flag.enabled = not flag.enabled
            self.db.commit()
            self.db.refresh(flag)
        return flag

    def set_rollout_percentage(
        self,
        flag_id: int,
        percentage: int
    ) -> FeatureFlag:
        """
        Set rollout percentage for flag.

        Args:
            flag_id: Feature flag ID
            percentage: Rollout percentage (0-100)

        Returns:
            Updated feature flag
        """
        flag = self.get(flag_id)
        if flag:
            flag.rollout_percentage = max(0, min(100, percentage))
            self.db.commit()
            self.db.refresh(flag)
        return flag

    def get_by_tags(self, tags: List[str]) -> List[FeatureFlag]:
        """
        Get feature flags by tags.

        Args:
            tags: List of tags to search

        Returns:
            List of feature flags with any of the tags
        """
        flags = []
        for tag in tags:
            tag_flags = self.db.query(FeatureFlag).filter(
                FeatureFlag.tags.contains([tag])
            ).all()
            flags.extend(tag_flags)

        # Remove duplicates
        return list(set(flags))

    def get_stats(self) -> Dict[str, Any]:
        """
        Get feature flag statistics.

        Returns:
            Dictionary with statistics
        """
        total = self.db.query(FeatureFlag).count()
        enabled = self.db.query(FeatureFlag).filter(
            FeatureFlag.enabled == True
        ).count()

        by_scope = {}
        for scope in FeatureFlagScope:
            count = self.db.query(FeatureFlag).filter(
                FeatureFlag.scope == scope.value
            ).count()
            by_scope[scope.value] = count

        by_type = {}
        for flag_type in FeatureFlagType:
            count = self.db.query(FeatureFlag).filter(
                FeatureFlag.flag_type == flag_type.value
            ).count()
            by_type[flag_type.value] = count

        return {
            "total": total,
            "enabled": enabled,
            "disabled": total - enabled,
            "by_scope": by_scope,
            "by_type": by_type
        }
