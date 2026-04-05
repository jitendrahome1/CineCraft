"""
Authentication service for user login, registration, and token management.
"""
from typing import Optional
from datetime import timedelta
from sqlalchemy.orm import Session

from app.repositories.user import UserRepository
from app.models.user import User, UserRole
from app.core.security import (
    verify_password,
    get_password_hash,
    create_access_token,
    create_refresh_token
)
from app.core.errors import (
    AuthenticationError,
    UserAlreadyExistsError,
    UserNotFoundError,
    UserInactiveError
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class AuthService:
    """Service for authentication operations."""

    def __init__(self, db: Session):
        """
        Initialize auth service.

        Args:
            db: Database session
        """
        self.db = db
        self.user_repo = UserRepository(db)

    def register_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None
    ) -> User:
        """
        Register a new user.

        Args:
            email: User's email address
            password: Plain text password
            full_name: User's full name

        Returns:
            Created user instance

        Raises:
            UserAlreadyExistsError: If email already exists
        """
        # Check if user already exists
        if self.user_repo.email_exists(email):
            logger.warning(f"Registration attempt with existing email: {email}")
            raise UserAlreadyExistsError(
                f"User with email {email} already exists"
            )

        # Hash password
        hashed_password = get_password_hash(password)

        # Create user
        user = self.user_repo.create_user(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=UserRole.USER
        )

        logger.info(f"User registered successfully: {email}")
        return user

    def authenticate_user(
        self,
        email: str,
        password: str
    ) -> tuple[User, str, str]:
        """
        Authenticate user with email and password.

        Args:
            email: User's email address
            password: Plain text password

        Returns:
            Tuple of (user, access_token, refresh_token)

        Raises:
            AuthenticationError: If credentials are invalid
            UserInactiveError: If user account is inactive
        """
        # Get user by email
        user = self.user_repo.get_by_email(email)

        if not user:
            logger.warning(f"Login attempt with non-existent email: {email}")
            raise AuthenticationError("Invalid email or password")

        # Check if user is active
        if not user.is_active:
            logger.warning(f"Login attempt for inactive user: {email}")
            raise UserInactiveError("User account is inactive")

        # Verify password
        if not verify_password(password, user.hashed_password):
            logger.warning(f"Login attempt with incorrect password: {email}")
            raise AuthenticationError("Invalid email or password")

        # Update last login
        self.user_repo.update_last_login(user.id)

        # Create tokens
        access_token = create_access_token(data={"sub": str(user.id)})
        refresh_token = create_refresh_token(data={"sub": str(user.id)})

        logger.info(f"User authenticated successfully: {email}")
        return user, access_token, refresh_token

    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User instance or None

        Raises:
            UserNotFoundError: If user not found
        """
        user = self.user_repo.get(user_id)
        if not user:
            raise UserNotFoundError(f"User with ID {user_id} not found")
        return user

    def change_password(
        self,
        user_id: int,
        current_password: str,
        new_password: str
    ) -> User:
        """
        Change user's password.

        Args:
            user_id: User ID
            current_password: Current password
            new_password: New password

        Returns:
            Updated user instance

        Raises:
            UserNotFoundError: If user not found
            AuthenticationError: If current password is incorrect
        """
        user = self.get_user_by_id(user_id)

        # Verify current password
        if not verify_password(current_password, user.hashed_password):
            logger.warning(f"Password change attempt with incorrect current password: {user.email}")
            raise AuthenticationError("Current password is incorrect")

        # Hash new password
        hashed_password = get_password_hash(new_password)

        # Update password
        updated_user = self.user_repo.update_password(user_id, hashed_password)
        logger.info(f"Password changed successfully for user: {user.email}")

        return updated_user

    def refresh_access_token(self, refresh_token: str) -> str:
        """
        Generate new access token from refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New access token

        Raises:
            AuthenticationError: If refresh token is invalid
        """
        from app.core.security import decode_access_token

        # Decode refresh token
        payload = decode_access_token(refresh_token)

        if not payload or payload.get("type") != "refresh":
            raise AuthenticationError("Invalid refresh token")

        user_id = payload.get("sub")
        if not user_id:
            raise AuthenticationError("Invalid refresh token payload")

        # Verify user exists and is active
        user = self.get_user_by_id(int(user_id))
        if not user.is_active:
            raise UserInactiveError("User account is inactive")

        # Create new access token
        access_token = create_access_token(data={"sub": user_id})

        return access_token

    def create_admin_user(
        self,
        email: str,
        password: str,
        full_name: Optional[str] = None
    ) -> User:
        """
        Create an admin user (internal use only).

        Args:
            email: Admin email address
            password: Plain text password
            full_name: Admin full name

        Returns:
            Created admin user

        Raises:
            UserAlreadyExistsError: If email already exists
        """
        # Check if user already exists
        if self.user_repo.email_exists(email):
            raise UserAlreadyExistsError(
                f"User with email {email} already exists"
            )

        # Hash password
        hashed_password = get_password_hash(password)

        # Create admin user
        user = self.user_repo.create_user(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            role=UserRole.ADMIN
        )

        # Auto-verify admin
        self.user_repo.verify_email(user.id)

        logger.info(f"Admin user created: {email}")
        return user
