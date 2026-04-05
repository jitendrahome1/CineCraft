"""
Custom exceptions and error handling for CineCraft.
All custom exceptions inherit from CineCraftException.
"""
from typing import Any, Optional


class CineCraftException(Exception):
    """Base exception for all CineCraft errors."""

    def __init__(
        self,
        message: str,
        code: Optional[str] = None,
        details: Optional[dict[str, Any]] = None
    ):
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)


# Authentication & Authorization Errors
class AuthenticationError(CineCraftException):
    """Authentication failed - invalid credentials."""
    pass


class AuthorizationError(CineCraftException):
    """User not authorized to perform this action."""
    pass


class TokenExpiredError(CineCraftException):
    """JWT token has expired."""
    pass


class InvalidTokenError(CineCraftException):
    """JWT token is invalid."""
    pass


# User & Account Errors
class UserNotFoundError(CineCraftException):
    """User not found in database."""
    pass


class UserAlreadyExistsError(CineCraftException):
    """User with this email already exists."""
    pass


class UserInactiveError(CineCraftException):
    """User account is inactive."""
    pass


# Subscription & Payment Errors
class SubscriptionError(CineCraftException):
    """Base subscription error."""
    pass


class SubscriptionNotFoundError(SubscriptionError):
    """Subscription not found."""
    pass


class SubscriptionLimitError(SubscriptionError):
    """User exceeded subscription limits."""
    pass


class SubscriptionInactiveError(SubscriptionError):
    """Subscription is not active."""
    pass


class PaymentError(CineCraftException):
    """Payment processing error."""
    pass


class StripeWebhookError(CineCraftException):
    """Stripe webhook validation or processing error."""
    pass


# Project & Content Errors
class ProjectNotFoundError(CineCraftException):
    """Project not found."""
    pass


class SceneNotFoundError(CineCraftException):
    """Scene not found."""
    pass


class CharacterNotFoundError(CineCraftException):
    """Character not found."""
    pass


class MediaAssetNotFoundError(CineCraftException):
    """Media asset not found."""
    pass


# AI Provider Errors
class AIProviderError(CineCraftException):
    """Base AI provider error."""
    pass


class AIProviderConfigError(AIProviderError):
    """AI provider configuration error."""
    pass


class AIProviderAPIError(AIProviderError):
    """AI provider API request failed."""
    pass


class AIProviderRateLimitError(AIProviderError):
    """AI provider rate limit exceeded."""
    pass


# Storage Errors
class StorageError(CineCraftException):
    """Base storage error."""
    pass


class FileNotFoundError(StorageError):
    """File not found in storage."""
    pass


class FileUploadError(StorageError):
    """File upload failed."""
    pass


class FileDeletionError(StorageError):
    """File deletion failed."""
    pass


# Rendering Errors
class RenderJobError(CineCraftException):
    """Base render job error."""
    pass


class RenderJobNotFoundError(RenderJobError):
    """Render job not found."""
    pass


class RenderJobFailedError(RenderJobError):
    """Render job processing failed."""
    pass


class FFmpegError(RenderJobError):
    """FFmpeg processing error."""
    pass


# Validation Errors
class ValidationError(CineCraftException):
    """Input validation error."""
    pass


# Configuration Errors
class ConfigurationError(CineCraftException):
    """Configuration or settings error."""
    pass


# Database Errors
class DatabaseError(CineCraftException):
    """Database operation error."""
    pass


class RecordNotFoundError(DatabaseError):
    """Database record not found."""
    pass


class RecordAlreadyExistsError(DatabaseError):
    """Database record already exists."""
    pass
