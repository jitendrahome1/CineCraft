# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

CineCraft is an AI-powered Story-to-Video automation SaaS platform. Users input a story title, and the system generates: full story, scene breakdown, character design, scene images, voice narration, background music, subtitles, and final cinematic video output.

## Architecture Principles

This project follows **Clean Architecture** with strict separation of concerns:

- **Controllers**: Handle HTTP requests/responses, WebSocket connections
- **Services**: Business logic and orchestration
- **Repositories**: Data access layer (SQLAlchemy ORM)
- **Providers**: AI provider abstraction layer (allows swapping AI APIs)
- **Infrastructure**: External services, storage, queuing

### SOLID Principles

- Every feature must be modular and independently testable
- All services must be replaceable through dependency injection
- Future modules must be pluggable without breaking existing system
- Use interfaces/abstract classes for AI providers, storage, and external services

## Tech Stack

### Backend
- **Python FastAPI**: Main API framework
- **SQLAlchemy ORM**: Database abstraction
- **SQLite**: Local development database (PostgreSQL-ready schema)
- **Redis**: Caching and session management
- **Celery**: Asynchronous task queue for video rendering
- **WebSockets**: Real-time job status updates
- **FFmpeg**: Video rendering engine

### Frontend
- **Next.js (App Router)**: React framework with server components
- **TypeScript**: Type-safe development
- **TailwindCSS**: Utility-first styling

### Payments
- **Stripe**: Subscription billing (Free, Pro, Enterprise plans)
- Webhook handling for subscription events

## Core Modules

1. **Auth Module**: JWT authentication, role-based access (User, Admin), secure password hashing
2. **Project Module**: Create/manage projects and scenes, store metadata
3. **AI Orchestration Module**: Story generation, scene breakdown, image generation, voice generation, music generation, subtitle creation
4. **Video Rendering Module**: Ken Burns effect, fade transitions, audio ducking, subtitle overlay, multi-format export
5. **Subscription & Payment Module**: Plan management, usage limits, upgrade/downgrade, Stripe webhooks
6. **Admin Panel Module**: User management, plan management, analytics, feature flags, render job monitoring
7. **Analytics Module**: Video generation count, usage metrics, API tracking, revenue tracking

## Database Schema

Core tables: `users`, `roles`, `subscriptions`, `plans`, `payments`, `projects`, `scenes`, `characters`, `media_assets`, `render_jobs`, `feature_flags`, `analytics_logs`

Schema is designed to be PostgreSQL-ready from day one, even though SQLite is used locally.

## Video Pipeline Flow

1. Create render job → 2. Queue job (Celery) → 3. AI generation (parallel requests) → 4. Store media assets → 5. Create SRT subtitles → 6. Merge using FFmpeg → 7. Store final video → 8. Update job status → 9. Notify user via WebSocket

## Project Structure

The codebase follows a modular structure:

```
backend/
├── app/
│   ├── api/            # API routes (controllers)
│   ├── core/           # Config, security, dependencies
│   ├── models/         # SQLAlchemy models
│   ├── repositories/   # Data access layer
│   ├── services/       # Business logic
│   ├── providers/      # AI provider abstractions
│   ├── schemas/        # Pydantic models
│   └── tasks/          # Celery tasks
├── migrations/         # Alembic migrations
└── storage/           # Local file storage

frontend/
├── app/               # Next.js App Router pages
├── components/        # React components
├── lib/              # Utilities and API clients
└── public/           # Static assets
```

## Development Commands

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run database migrations
alembic upgrade head

# Start FastAPI server
uvicorn app.main:app --reload

# Start Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# Start Redis
redis-server
```

### Frontend

```bash
# Install dependencies
npm install

# Development server
npm run dev

# Build production
npm run build

# Run production build
npm start
```

### Docker

```bash
# Start all services
docker-compose up

# Rebuild after changes
docker-compose up --build

# Stop all services
docker-compose down
```

## AI Provider Abstraction

All AI providers are abstracted through a provider interface. This allows easy replacement of AI services:

```python
# All providers implement abstract base class
class AIProvider(ABC):
    @abstractmethod
    async def generate_story(self, prompt: str) -> str: ...

    @abstractmethod
    async def generate_image(self, prompt: str) -> bytes: ...
```

To add a new AI provider, create a new provider class implementing the interface and register it in the provider factory.

## Storage Abstraction

Storage is abstracted to allow easy migration from local to cloud storage (S3):

```python
class StorageProvider(ABC):
    @abstractmethod
    async def save_file(self, file: bytes, path: str) -> str: ...

    @abstractmethod
    async def get_file(self, path: str) -> bytes: ...
```

Configuration in `.env` determines which storage provider is used.

## Feature Flags

Features can be toggled via `feature_flags` table or environment variables. This allows:
- Enabling features per subscription plan
- A/B testing
- Gradual rollout of new features
- Disabling features without code changes

## Security

- **JWT Authentication**: All API endpoints require valid JWT tokens
- **Role-Based Authorization**: User vs Admin access levels
- **Rate Limiting**: Prevent API abuse
- **Stripe Webhook Validation**: Verify webhook signatures
- **Input Validation**: Pydantic schemas validate all inputs
- **SQL Injection Protection**: SQLAlchemy ORM prevents SQL injection
- **Environment-Based Config**: Secrets in `.env`, never committed

## Configuration

All configuration via `.env` file:

```env
DATABASE_URL=sqlite:///./cinecraft.db
REDIS_URL=redis://localhost:6379
JWT_SECRET_KEY=...
STRIPE_API_KEY=...
STRIPE_WEBHOOK_SECRET=...
# AI Provider API keys
OPENAI_API_KEY=...
# Storage configuration
STORAGE_PROVIDER=local  # or 's3'
```

## Future Extensibility

The architecture is designed for easy addition of:

- **AI Avatar Animation**: Add new provider in `providers/` directory
- **YouTube Auto-Publish**: Add new service in `services/` directory
- **Multi-Language Support**: Extend AI providers with language parameter
- **Team Collaboration**: Add team tables and permission system
- **API Access**: Expose REST API with rate limiting per plan
- **Microservices**: Each module can be extracted into separate service

## Important Notes

- **No Local AI Models**: All AI generation uses external APIs
- **Microservice-Ready**: Code structure allows separation into microservices later
- **Clean Architecture**: Never bypass service layer, always use dependency injection
- **Error Handling**: Centralized error handling in middleware
- **Logging**: Structured logging throughout application
- **Testing**: Each module must have unit tests in `tests/` directory

## FFmpeg Rendering

Video rendering uses FFmpeg with complex filter chains:

- Ken Burns effect: `zoompan` filter
- Transitions: `fade` and `xfade` filters
- Audio ducking: `sidechaincompress` filter
- Subtitle overlay: `subtitles` filter
- Multiple audio tracks: Background music + voice narration

Rendering is CPU-intensive and runs as Celery background tasks.

## WebSocket Status Updates

Real-time job status updates via WebSocket endpoints:

- Connect to `/ws/{job_id}`
- Receive updates: `{"status": "processing", "progress": 45, "stage": "generating_images"}`
- Disconnection handling and reconnection logic on frontend

## Subscription Plans

Three tiers with different limits:

- **Free**: Limited videos/month, SD resolution, watermark
- **Pro**: More videos, HD resolution, no watermark
- **Enterprise**: Unlimited, 4K resolution, API access, priority rendering

Limits enforced in middleware before job creation.

## Deployment

Docker Compose for local development. Production deployment:

1. PostgreSQL instead of SQLite
2. Redis cluster for high availability
3. Multiple Celery workers for parallel rendering
4. S3 for media storage
5. CDN for video delivery
6. Load balancer for API servers

## Code Quality

- Type hints on all functions
- Docstrings for all public methods
- Follow PEP 8 for Python
- ESLint + Prettier for TypeScript/React
- Pre-commit hooks for linting
