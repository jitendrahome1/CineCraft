"""
Authentication API endpoints.
Handles user registration, login, token refresh, and password management.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_auth_service
from app.services.auth import AuthService
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    RegisterResponse,
    LoginRequest,
    LoginResponse,
    TokenRefreshRequest,
    TokenRefreshResponse
)
from app.schemas.user import UserResponse, UserChangePassword
from app.core.errors import (
    AuthenticationError,
    UserAlreadyExistsError,
    UserInactiveError
)
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter()


@router.post("/register", response_model=RegisterResponse, status_code=status.HTTP_201_CREATED)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Register a new user account.

    Args:
        request: Registration data (email, password, full_name)
        auth_service: Auth service instance

    Returns:
        Registered user information

    Raises:
        HTTPException: If email already exists
    """
    try:
        user = auth_service.register_user(
            email=request.email,
            password=request.password,
            full_name=request.full_name
        )

        return RegisterResponse(
            id=user.id,
            email=user.email,
            full_name=user.full_name
        )

    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Login with email and password.

    Args:
        request: Login credentials (email, password)
        auth_service: Auth service instance

    Returns:
        Access token and refresh token

    Raises:
        HTTPException: If credentials are invalid or account is inactive
    """
    try:
        user, access_token, refresh_token = auth_service.authenticate_user(
            email=request.email,
            password=request.password
        )

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token
        )

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )
    except UserInactiveError as e:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(e)
        )


@router.post("/refresh", response_model=TokenRefreshResponse)
async def refresh_token(
    request: TokenRefreshRequest,
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Refresh access token using refresh token.

    Args:
        request: Refresh token
        auth_service: Auth service instance

    Returns:
        New access token

    Raises:
        HTTPException: If refresh token is invalid
    """
    try:
        access_token = auth_service.refresh_access_token(request.refresh_token)

        return TokenRefreshResponse(access_token=access_token)

    except (AuthenticationError, UserInactiveError) as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e)
        )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current authenticated user information.

    Args:
        current_user: Current user from token

    Returns:
        User information
    """
    return UserResponse.from_user(current_user)


@router.post("/change-password")
async def change_password(
    request: UserChangePassword,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
):
    """
    Change user password.

    Args:
        request: Current and new password
        current_user: Current user from token
        auth_service: Auth service instance

    Returns:
        Success message

    Raises:
        HTTPException: If current password is incorrect
    """
    try:
        auth_service.change_password(
            user_id=current_user.id,
            current_password=request.current_password,
            new_password=request.new_password
        )

        return {"message": "Password changed successfully"}

    except AuthenticationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user)):
    """
    Logout user (client should discard tokens).

    Args:
        current_user: Current user from token

    Returns:
        Success message

    Note:
        This is a client-side operation. The server doesn't invalidate tokens
        (stateless JWT). Client should discard the tokens.
    """
    logger.info(f"User logged out: {current_user.email}")
    return {"message": "Logged out successfully"}
