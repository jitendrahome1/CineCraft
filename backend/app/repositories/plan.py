"""
Plan repository for database operations related to subscription plans.
"""
from typing import Optional, List
from sqlalchemy.orm import Session
from app.repositories.base import BaseRepository
from app.models.plan import Plan
from app.core.logging import get_logger

logger = get_logger(__name__)


class PlanRepository(BaseRepository[Plan]):
    """Repository for Plan model operations."""

    def __init__(self, db: Session):
        """
        Initialize plan repository.

        Args:
            db: Database session
        """
        super().__init__(Plan, db)

    def get_by_name(self, name: str) -> Optional[Plan]:
        """
        Get plan by name.

        Args:
            name: Plan name

        Returns:
            Plan instance or None
        """
        return self.db.query(Plan).filter(Plan.name == name).first()

    def get_active_plans(self) -> List[Plan]:
        """
        Get all active plans.

        Returns:
            List of active plans
        """
        return self.db.query(Plan).filter(Plan.is_active == True).all()

    def get_by_stripe_price_id(self, stripe_price_id: str) -> Optional[Plan]:
        """
        Get plan by Stripe price ID.

        Args:
            stripe_price_id: Stripe Price ID

        Returns:
            Plan instance or None
        """
        return self.db.query(Plan).filter(
            (Plan.stripe_price_id_monthly == stripe_price_id) |
            (Plan.stripe_price_id_yearly == stripe_price_id)
        ).first()
