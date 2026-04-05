# CineCraft Setup Guide

Complete setup instructions for CineCraft development environment.

## Prerequisites

- Docker and Docker Compose
- Git
- Python 3.11+ (for local development)
- Node.js 20+ (for frontend development)

## Quick Start with Docker

### 1. Clone and Configure

```bash
# Clone the repository
git clone <repository-url>
cd CineCraft

# Copy environment file
cp backend/.env.example backend/.env
```

### 2. Edit Environment Variables

Edit `backend/.env` and add your API keys:

```env
# Required for Phase 1
JWT_SECRET_KEY=your-secure-random-string-here
DATABASE_URL=postgresql://cinecraft:cinecraft_dev_password@postgres:5432/cinecraft
REDIS_URL=redis://redis:6379

# Required for Phase 5 (Story Generation)
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Required for Phase 2 (Payments)
STRIPE_API_KEY=sk_test_your-key-here
STRIPE_WEBHOOK_SECRET=whsec_your-secret-here
```

### 3. Start All Services

```bash
# Build and start all containers
docker-compose up --build

# Or run in detached mode
docker-compose up -d
```

### 4. Run Database Migrations

```bash
# Apply database migrations
docker-compose exec backend alembic upgrade head
```

### 5. Create Admin User

```bash
# Create your first admin user
docker-compose exec backend python scripts/create_admin.py
```

### 6. Access the Application

- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Frontend**: http://localhost:3000
- **Health Check**: http://localhost:8000/health

## Phase 1: Testing Authentication

### Register a New User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "full_name": "Test User"
  }'
```

### Login

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123"
  }'
```

Response:
```json
{
  "access_token": "eyJ...",
  "refresh_token": "eyJ...",
  "token_type": "bearer"
}
```

### Get Current User

```bash
curl http://localhost:8000/api/v1/auth/me \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

### Change Password

```bash
curl -X POST http://localhost:8000/api/v1/auth/change-password \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "current_password": "password123",
    "new_password": "newpassword123"
  }'
```

### Admin: List All Users

```bash
curl http://localhost:8000/api/v1/users/ \
  -H "Authorization: Bearer ADMIN_ACCESS_TOKEN"
```

## Development Without Docker

### Backend Setup

```bash
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your settings

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Start Redis (required for rate limiting)

```bash
# Using Docker
docker run -d -p 6379:6379 redis:7-alpine

# Or install locally
brew install redis  # macOS
redis-server
```

### Start PostgreSQL

```bash
# Using Docker
docker run -d \
  -p 5432:5432 \
  -e POSTGRES_USER=cinecraft \
  -e POSTGRES_PASSWORD=cinecraft_dev_password \
  -e POSTGRES_DB=cinecraft \
  postgres:15-alpine
```

## Database Migrations

### Create New Migration

```bash
# Auto-generate migration from model changes
docker-compose exec backend alembic revision --autogenerate -m "description"

# Or manually create empty migration
docker-compose exec backend alembic revision -m "description"
```

### Apply Migrations

```bash
# Apply all pending migrations
docker-compose exec backend alembic upgrade head

# Apply specific migration
docker-compose exec backend alembic upgrade <revision_id>
```

### Rollback Migration

```bash
# Rollback one migration
docker-compose exec backend alembic downgrade -1

# Rollback to specific revision
docker-compose exec backend alembic downgrade <revision_id>
```

### View Migration History

```bash
docker-compose exec backend alembic history
docker-compose exec backend alembic current
```

## Useful Docker Commands

```bash
# View logs
docker-compose logs -f
docker-compose logs -f backend
docker-compose logs -f frontend

# Restart specific service
docker-compose restart backend

# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes data)
docker-compose down -v

# Rebuild specific service
docker-compose up --build backend

# Execute command in container
docker-compose exec backend bash
docker-compose exec backend python scripts/create_admin.py

# View running containers
docker-compose ps
```

## Testing

### Run Backend Tests

```bash
# All tests
docker-compose exec backend pytest

# With coverage
docker-compose exec backend pytest --cov=app --cov-report=html

# Specific test file
docker-compose exec backend pytest tests/unit/test_auth.py

# Verbose output
docker-compose exec backend pytest -v
```

## Troubleshooting

### Database Connection Error

```bash
# Check if PostgreSQL is running
docker-compose ps postgres

# View PostgreSQL logs
docker-compose logs postgres

# Restart PostgreSQL
docker-compose restart postgres
```

### Redis Connection Error

```bash
# Check if Redis is running
docker-compose ps redis

# Test Redis connection
docker-compose exec redis redis-cli ping
# Should return: PONG
```

### Port Already in Use

```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

### Permission Errors

```bash
# Fix file permissions
chmod +x scripts/*.py

# Or run with python explicitly
docker-compose exec backend python scripts/create_admin.py
```

### Clear Docker Volumes

```bash
# Stop and remove everything (WARNING: deletes data)
docker-compose down -v

# Rebuild from scratch
docker-compose up --build
```

## What's Next?

✅ **Phase 0**: Foundation & Infrastructure - COMPLETE
✅ **Phase 1**: Authentication & User Management - COMPLETE

**Phase 2**: Subscription & Stripe Integration
- Set up Stripe account
- Add subscription plans
- Implement payment webhooks
- Usage limit enforcement

See [CLAUDE.md](./CLAUDE.md) for detailed architecture information and development phases.

## Support

For issues and questions:
- Check logs: `docker-compose logs -f`
- Review API documentation: http://localhost:8000/docs
- Create an issue on GitHub
