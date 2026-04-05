"""
User repository for database operations related to users.
"""
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime

from app.repositories.base import BaseRepository
from app.models.user import User, UserRole
from app.core.logging import get_logger

logger = get_logger(__name__)


class UserRepository(BaseRepository[User]):
    """Repository for User model operations."""

    def __init__(self, db: Session):
        """
        Initialize user repository.

        Args:
            db: Database session
        """
        super().__init__(User, db)

    def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            email: User's email address

        Returns:
            User instance or None
        """
        return self.db.query(User).filter(
            func.lower(User.email) == func.lower(email)
        ).first()

    def get_by_email_active(self, email: str) -> Optional[User]:
        """
        Get active user by email address.

        Args:
            email: User's email address

        Returns:
            User instance or None if not found or inactive
        """
        return self.db.query(User).filter(
            func.lower(User.email) == func.lower(email),
            User.is_active == True
        ).first()

    def create_user(
        self,
        email: str,
        hashed_password: str,
        full_name: Optional[str] = None,
        role: UserRole = UserRole.USER
    ) -> User:
        """
        Create a new user.

        Args:
            email: User's email address
            hashed_password: Hashed password
            full_name: User's full name
            role: User role (default: USER)

        Returns:
            Created user instance
        """
        user = User(
            email=email.lower(),
            hashed_password=hashed_password,
            full_name=full_name,
            role=role,
            is_active=True,
            is_verified=False
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)

        logger.info(f"Created new user: {user.email} (ID: {user.id})")
        return user

    def update_last_login(self, user_id: int) -> None:
        """
        Update user's last login timestamp.

        Args:
            user_id: User ID
        """
        user = self.get(user_id)
        if user:
            user.last_login = datetime.utcnow()
            self.db.commit()

    def update_password(self, user_id: int, hashed_password: str) -> Optional[User]:
        """
        Update user's password.

        Args:
            user_id: User ID
            hashed_password: New hashed password

        Returns:
            Updated user instance or None
        """
        user = self.get(user_id)
        if user:
            user.hashed_password = hashed_password
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"Updated password for user: {user.email}")
            return user
        return None

    def deactivate_user(self, user_id: int) -> Optional[User]:
        """
        Deactivate a user account.

        Args:
            user_id: User ID

        Returns:
            Updated user instance or None
        """
        user = self.get(user_id)
        if user:
            user.is_active = False
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"Deactivated user: {user.email}")
            return user
        return None

    def activate_user(self, user_id: int) -> Optional[User]:
        """
        Activate a user account.

        Args:
            user_id: User ID

        Returns:
            Updated user instance or None
        """
        user = self.get(user_id)
        if user:
            user.is_active = True
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"Activated user: {user.email}")
            return user
        return None

    def verify_email(self, user_id: int) -> Optional[User]:
        """
        Mark user's email as verified.

        Args:
            user_id: User ID

        Returns:
            Updated user instance or None
        """
        user = self.get(user_id)
        if user:
            user.is_verified = True
            self.db.commit()
            self.db.refresh(user)
            logger.info(f"Verified email for user: {user.email}")
            return user
        return None

    def get_admin_users(self) -> list[User]:
        """
        Get all admin users.

        Returns:
            List of admin users
        """
        return self.db.query(User).filter(
            User.role == UserRole.ADMIN,
            User.is_active == True
        ).all()

    def email_exists(self, email: str) -> bool:
        """
        Check if email already exists.

        Args:
            email: Email address to check

        Returns:
            True if exists, False otherwise
        """
        return self.db.query(User).filter(
            func.lower(User.email) == func.lower(email)
        ).first() is not None
