"""
User management API endpoints.
Admin operations for managing users.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from typing import List

from app.api.deps import get_current_admin_user, get_current_user, get_auth_service
from app.services.auth import AuthService
from app.models.user import User
from app.schemas.user import UserResponse, UserInDB
from app.repositories.user import UserRepository
from app.db.session import get_db
from sqlalchemy.orm import Session
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 100,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    List all users (admin only).

    Args:
        skip: Number of records to skip
        limit: Maximum number of records
        current_admin: Current admin user
        db: Database session

    Returns:
        List of users
    """
    user_repo = UserRepository(db)
    users = user_repo.get_all(skip=skip, limit=limit)
    return users


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.

    Args:
        current_user: Current authenticated user

    Returns:
        Current user information
    """
    return current_user


@router.get("/{user_id}", response_model=UserInDB)
async def get_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Get user by ID (admin only).

    Args:
        user_id: User ID
        current_admin: Current admin user
        auth_service: Auth service

    Returns:
        User information
    """
    user = auth_service.get_user_by_id(user_id)
    return user


@router.delete("/{user_id}")
async def deactivate_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Deactivate a user (admin only).

    Args:
        user_id: User ID
        current_admin: Current admin user
        db: Database session

    Returns:
        Success message
    """
    # Don't allow deactivating self
    if current_admin.id == user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )

    user_repo = UserRepository(db)
    user = user_repo.deactivate_user(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {"message": f"User {user.email} deactivated successfully"}


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int,
    current_admin: User = Depends(get_current_admin_user),
    db: Session = Depends(get_db)
):
    """
    Activate a user (admin only).

    Args:
        user_id: User ID
        current_admin: Current admin user
        db: Database session

    Returns:
        Success message
    """
    user_repo = UserRepository(db)
    user = user_repo.activate_user(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return {"message": f"User {user.email} activated successfully"}
