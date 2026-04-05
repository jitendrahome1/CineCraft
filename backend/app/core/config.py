"""
Core configuration management for CineCraft.
All environment variables and settings are loaded here.
"""
from pydantic_settings import BaseSettings
from typing import Optional
import secrets


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # Application
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = secrets.token_urlsafe(32)
    APP_NAME: str = "CineCraft"
    API_V1_PREFIX: str = "/api/v1"

    # App Mode: "testing" or "production"
    # testing  = placeholder images, zero API cost, fast iteration
    # production = real AI image generation via OpenAI gpt-image-1
    APP_MODE: str = "testing"

    # In testing mode, generate real images for the first N scenes only.
    # Remaining scenes get placeholders. Set to 0 for all placeholders.
    TESTING_REAL_IMAGE_LIMIT: int = 0

    # Database
    DATABASE_URL: str = "sqlite:///./cinecraft.db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379"

    # JWT Authentication
    JWT_SECRET_KEY: str = secrets.token_urlsafe(32)
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_MINUTES: int = 60

    # Anthropic Claude
    ANTHROPIC_API_KEY: Optional[str] = None

    # OpenRouter (unified AI model access)
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_STORY_MODEL: str = "anthropic/claude-3.5-sonnet"
    OPENROUTER_SCENE_MODEL: str = "anthropic/claude-3.5-sonnet"
    OPENROUTER_CHARACTER_MODEL: str = "anthropic/claude-3.5-sonnet"
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"

    # OpenAI
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"

    # Google Gemini
    GEMINI_API_KEY: Optional[str] = None

    # ElevenLabs (future)
    ELEVENLABS_API_KEY: Optional[str] = None

    # Suno/Music (future)
    SUNO_API_KEY: Optional[str] = None

    # Stripe
    STRIPE_API_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    STRIPE_PRICE_FREE: Optional[str] = None
    STRIPE_PRICE_PRO: Optional[str] = None
    STRIPE_PRICE_ENTERPRISE: Optional[str] = None

    # Storage
    STORAGE_PROVIDER: str = "local"  # 'local' or 's3'
    LOCAL_STORAGE_PATH: str = "./storage"
    AWS_ACCESS_KEY_ID: Optional[str] = None
    AWS_SECRET_ACCESS_KEY: Optional[str] = None
    S3_BUCKET: Optional[str] = None
    S3_REGION: str = "us-east-1"
    S3_ENDPOINT_URL: Optional[str] = None  # For S3-compatible services

    # API Base URL (for generating file URLs)
    API_BASE_URL: str = "http://localhost:8000"

    # AI Provider Selection
    AI_PROVIDER: str = "anthropic"
    IMAGE_PROVIDER: str = "dalle"
    VOICE_PROVIDER: str = "elevenlabs"
    MUSIC_PROVIDER: str = "suno"

    # Provider API Keys (generic)
    IMAGE_PROVIDER_API_KEY: Optional[str] = None
    VOICE_PROVIDER_API_KEY: Optional[str] = None
    MUSIC_PROVIDER_API_KEY: Optional[str] = None

    # Feature Flags
    ENABLE_HD_EXPORT: bool = True
    ENABLE_4K_EXPORT: bool = False
    ENABLE_API_ACCESS: bool = False

    # Celery
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/0"

    # CORS
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:8000"

    @property
    def cors_origins_list(self) -> list[str]:
        """Convert CORS origins string to list."""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    # FFmpeg
    FFMPEG_THREADS: int = 2
    FFMPEG_PRESET: str = "medium"

    class Config:
        env_file = ".env"
        case_sensitive = True


# Global settings instance
settings = Settings()
