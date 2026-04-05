# CineCraft

AI-powered Story-to-Video automation SaaS platform. Transform your stories into cinematic videos with AI-generated scenes, images, voice narration, background music, and subtitles.

## Features

- 🎬 **Story Generation**: AI-powered story creation from simple titles
- 🎨 **Scene Breakdown**: Automatic scene segmentation and descriptions
- 🖼️ **Image Generation**: AI-generated scene images
- 🎙️ **Voice Narration**: Text-to-speech narration for each scene
- 🎵 **Background Music**: AI-generated ambient music
- 📝 **Subtitles**: Automatic subtitle generation
- 🎥 **Video Rendering**: Professional video compilation with effects

## Tech Stack

### Backend
- **FastAPI** - Modern Python web framework
- **PostgreSQL** - Primary database
- **Redis** - Caching and Celery broker
- **Celery** - Asynchronous task processing
- **SQLAlchemy** - ORM
- **Alembic** - Database migrations
- **FFmpeg** - Video rendering

### Frontend
- **Next.js 14** - React framework with App Router
- **TypeScript** - Type-safe development
- **TailwindCSS** - Utility-first CSS

### AI Services
- **Anthropic Claude** - Story and scene generation
- **DALL-E / Stable Diffusion** - Image generation (coming soon)
- **ElevenLabs** - Voice narration (coming soon)
- **Suno** - Music generation (coming soon)

### Payments
- **Stripe** - Subscription billing

## Getting Started

### Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development without Docker)
- Node.js 20+ (for frontend development)

### Environment Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd CineCraft
   ```

2. **Set up environment variables**
   ```bash
   cp backend/.env.example backend/.env
   ```

3. **Edit `backend/.env`** with your API keys:
   - `ANTHROPIC_API_KEY` - Get from https://console.anthropic.com
   - `STRIPE_API_KEY` - Get from https://dashboard.stripe.com
   - `JWT_SECRET_KEY` - Generate a secure random string

### Run with Docker Compose

```bash
# Build and start all services
docker-compose up --build

# Run in detached mode
docker-compose up -d

# View logs
docker-compose logs -f

# Stop all services
docker-compose down
```

**Services will be available at:**
- Backend API: http://localhost:8000
- API Documentation: http://localhost:8000/docs
- Frontend: http://localhost:3000
- PostgreSQL: localhost:5432
- Redis: localhost:6379

### Database Migrations

```bash
# Create a new migration
docker-compose exec backend alembic revision --autogenerate -m "description"

# Apply migrations
docker-compose exec backend alembic upgrade head

# Rollback migration
docker-compose exec backend alembic downgrade -1
```

### Development Without Docker

#### Backend

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload
```

#### Frontend

```bash
cd frontend

# Install dependencies
npm install

# Run development server
npm run dev
```

#### Celery Worker

```bash
cd backend

# Start Celery worker
celery -A app.tasks.celery_app worker --loglevel=info

# Start Celery Beat (scheduler)
celery -A app.tasks.celery_app beat --loglevel=info
```

## Project Structure

```
CineCraft/
├── backend/                    # Python FastAPI backend
│   ├── app/
│   │   ├── api/               # API routes
│   │   ├── core/              # Config, security, logging
│   │   ├── models/            # SQLAlchemy models
│   │   ├── repositories/      # Data access layer
│   │   ├── services/          # Business logic
│   │   ├── providers/         # AI provider abstractions
│   │   ├── schemas/           # Pydantic schemas
│   │   ├── tasks/             # Celery tasks
│   │   └── utils/             # Utilities
│   ├── migrations/            # Alembic migrations
│   ├── storage/               # Local file storage
│   └── tests/                 # Test suite
├── frontend/                   # Next.js frontend
│   ├── app/                   # Next.js App Router
│   ├── components/            # React components
│   └── lib/                   # API clients & utilities
└── docker-compose.yml         # Docker orchestration
```

## Architecture

CineCraft follows **Clean Architecture** principles:

1. **Controllers (API Layer)** - Handle HTTP requests/responses
2. **Services (Business Logic)** - Core application logic
3. **Repositories (Data Access)** - Database operations
4. **Providers (External APIs)** - AI service abstractions
5. **Infrastructure** - External services (storage, queue)

### Provider Abstraction

All AI providers implement abstract base classes, allowing easy swapping:

```python
class AIProvider(ABC):
    @abstractmethod
    async def generate_story(self, title: str) -> str: ...

    @abstractmethod
    async def generate_scene_breakdown(self, story: str) -> list: ...
```

## Development Phases

- ✅ **Phase 0**: Foundation & Infrastructure (Current)
- ⏳ **Phase 1**: Authentication & User Management
- ⏳ **Phase 2**: Subscription & Stripe Integration
- ⏳ **Phase 3**: Project & Scene Management
- ⏳ **Phase 4**: AI Provider Abstraction Layer
- ⏳ **Phase 5**: AI Orchestration - Story Generation
- ⏳ **Phase 6**: Storage Abstraction & Media Management
- ⏳ **Phase 7**: AI Orchestration - Media Generation
- ⏳ **Phase 8**: Celery Task Queue Setup
- ⏳ **Phase 9**: Video Rendering Engine
- ⏳ **Phase 10**: WebSocket Real-Time Updates
- ⏳ **Phase 11**: Admin Panel
- ⏳ **Phase 12**: Analytics & Monitoring
- ⏳ **Phase 13**: Frontend Development

## Testing

```bash
# Run all tests
docker-compose exec backend pytest

# Run with coverage
docker-compose exec backend pytest --cov=app

# Run specific test file
docker-compose exec backend pytest tests/unit/test_auth.py
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License.

## Support

For issues and questions, please open an issue on GitHub.
# CineCraft
