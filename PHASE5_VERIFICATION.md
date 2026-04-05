# Phase 5 Verification Guide

## AI Orchestration - Story Generation - Implementation Complete

This document provides verification steps for Phase 5 implementation.

---

## Prerequisites

Before testing, ensure:

1. **Anthropic API Key configured** in `backend/.env`:
   ```bash
   ANTHROPIC_API_KEY=sk-ant-your-api-key-here
   AI_PROVIDER=anthropic
   ```

2. **Docker services running**:
   ```bash
   docker-compose up -d
   ```

3. **Database migrations applied**:
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

4. **User authenticated and project created**:
   ```bash
   # Login
   export TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login \
     -H "Content-Type: application/json" \
     -d '{"email":"test@example.com","password":"testpass123"}' \
     | jq -r '.access_token')

   # Create project
   export PROJECT_ID=$(curl -X POST http://localhost:8000/api/v1/projects \
     -H "Content-Type: application/json" \
     -H "Authorization: Bearer $TOKEN" \
     -d '{"title":"The Lost Key","description":"A fantasy adventure"}' \
     | jq -r '.id')
   ```

---

## Phase 5 Components Created

### Services
- ✅ `backend/app/services/story_generation.py` - Story generation with AI
- ✅ `backend/app/services/ai_orchestration.py` - AI orchestration coordinator

### API
- ✅ `backend/app/api/v1/ai.py` - AI generation endpoints (7 endpoints)
- ✅ `backend/app/schemas/ai.py` - AI request/response schemas

### Integration
- ✅ `backend/app/main.py` - Updated with AI routes

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/ai/generate-story` | Generate complete story with scenes and characters |
| POST | `/api/v1/ai/generate-story-only` | Generate story text only |
| POST | `/api/v1/ai/regenerate-scenes` | Regenerate scenes from existing story |
| POST | `/api/v1/ai/regenerate-characters` | Regenerate characters from existing story |
| POST | `/api/v1/ai/generate-content` | Generate all project content (orchestrated) |
| GET | `/api/v1/ai/providers/test` | Test all provider connections |
| GET | `/api/v1/ai/providers/info` | Get provider configuration info |

---

## Verification Tests

### 1. Test Provider Configuration

```bash
curl -X GET http://localhost:8000/api/v1/ai/providers/info \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "ai": {
    "configured": true,
    "type": "AnthropicProvider"
  },
  "image": {
    "configured": true,
    "type": "DallEProvider"
  },
  "voice": {
    "configured": true,
    "type": "ElevenLabsProvider"
  },
  "music": {
    "configured": true,
    "type": "SunoProvider"
  }
}
```

---

### 2. Test Provider Connections

```bash
curl -X GET http://localhost:8000/api/v1/ai/providers/test \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "ai": true,
  "image": true,
  "voice": true,
  "music": true
}
```

---

### 3. Generate Complete Story

```bash
curl -X POST http://localhost:8000/api/v1/ai/generate-story \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"project_id\": $PROJECT_ID,
    \"regenerate_scenes\": true,
    \"regenerate_characters\": true
  }"
```

**Expected Response:**
```json
{
  "project_id": 1,
  "story": "Once upon a time, in a forgotten attic...",
  "story_length": 1245,
  "scenes": [
    {
      "id": 1,
      "sequence_number": 1,
      "title": "The Discovery",
      "description": "Emma finds a mysterious key",
      "narration": "As dust motes danced...",
      "visual_description": "A dimly lit attic...",
      "duration": 10,
      "metadata": {
        "mood": "mysterious",
        "setting": "attic"
      }
    }
  ],
  "characters": [
    {
      "id": 1,
      "name": "Emma",
      "role": "protagonist",
      "description": "A brave young adventurer",
      "appearance": "Young woman in her 20s with long dark hair",
      "personality": "Brave, curious, determined"
    }
  ],
  "status": "completed"
}
```

**Note**: This will take 30-60 seconds as it makes multiple AI calls.

---

### 4. Verify Project Updated

```bash
curl -X GET http://localhost:8000/api/v1/projects/$PROJECT_ID \
  -H "Authorization: Bearer $TOKEN"
```

**Expected Response:**
```json
{
  "id": 1,
  "title": "The Lost Key",
  "status": "ready",
  "story": "Once upon a time...",
  "story_generated_at": "2024-02-25T12:00:00",
  "scenes_generated_at": "2024-02-25T12:00:30",
  "scenes": [
    {
      "id": 1,
      "sequence_number": 1,
      "title": "The Discovery",
      "has_image": false,
      "has_audio": false
    }
  ],
  "characters": [
    {
      "id": 1,
      "name": "Emma",
      "role": "protagonist"
    }
  ]
}
```

---

### 5. Generate Story Only (No Scenes/Characters)

```bash
# Create new project for this test
export PROJECT_ID_2=$(curl -X POST http://localhost:8000/api/v1/projects \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"The Magic Forest","description":"A children'\''s story"}' \
  | jq -r '.id')

# Generate story only
curl -X POST http://localhost:8000/api/v1/ai/generate-story-only \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"project_id\": $PROJECT_ID_2
  }"
```

**Expected Response:**
```json
{
  "project_id": 2,
  "story": "In a magical forest far away...",
  "story_length": 1150
}
```

---

### 6. Regenerate Scenes

```bash
curl -X POST http://localhost:8000/api/v1/ai/regenerate-scenes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"project_id\": $PROJECT_ID
  }"
```

**Expected Response:**
```json
{
  "project_id": 1,
  "scenes": [
    {
      "id": 4,
      "sequence_number": 1,
      "title": "Opening Scene",
      "description": "New scene description..."
    }
  ],
  "total": 5
}
```

**Note**: Old scenes are deleted and replaced with new ones.

---

### 7. Regenerate Characters

```bash
curl -X POST http://localhost:8000/api/v1/ai/regenerate-characters \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"project_id\": $PROJECT_ID
  }"
```

**Expected Response:**
```json
{
  "project_id": 1,
  "characters": [
    {
      "id": 3,
      "name": "Emma",
      "role": "protagonist"
    },
    {
      "id": 4,
      "name": "Merlin",
      "role": "mentor"
    }
  ],
  "total": 2
}
```

---

### 8. Generate All Content (Orchestrated)

```bash
curl -X POST http://localhost:8000/api/v1/ai/generate-content \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{
    \"project_id\": $PROJECT_ID,
    \"include_story\": true,
    \"include_scenes\": true,
    \"include_characters\": true,
    \"include_images\": false,
    \"include_audio\": false,
    \"include_music\": false
  }"
```

**Expected Response:**
```json
{
  "project_id": 1,
  "generated": {
    "story": "Once upon a time...",
    "scenes": [...],
    "characters": [...]
  }
}
```

**Note**: Images, audio, and music will show "skipped" status (Phase 7).

---

## Database Verification

### Check Generated Data

```bash
docker-compose exec backend python -c "
from app.db.session import SessionLocal
from app.models.project import Project
from app.models.scene import Scene
from app.models.character import Character

db = SessionLocal()

project = db.query(Project).first()
print(f'Project: {project.title}')
print(f'Status: {project.status}')
print(f'Story length: {len(project.story) if project.story else 0} chars')
print(f'Scenes: {db.query(Scene).filter(Scene.project_id == project.id).count()}')
print(f'Characters: {db.query(Character).filter(Character.project_id == project.id).count()}')

db.close()
"
```

**Expected Output:**
```
Project: The Lost Key
Status: ready
Story length: 1245 chars
Scenes: 5
Characters: 2
```

---

## Story Generation Flow

### Step-by-Step Process

1. **User Creates Project**
   - Title: "The Lost Key"
   - Description/Prompt: "A fantasy adventure"
   - Status: DRAFT

2. **User Triggers Story Generation**
   - POST `/api/v1/ai/generate-story`
   - Status changes: DRAFT → GENERATING

3. **AI Provider (Anthropic) Generates Story**
   - Uses Claude 3.5 Sonnet
   - Generates 800-1500 word story
   - Stores in `project.story`
   - Sets `story_generated_at` timestamp

4. **AI Provider Generates Scene Breakdown**
   - Parses story into 5-15 scenes
   - Each scene: 5-15 seconds duration
   - Includes visual descriptions
   - Creates Scene records

5. **AI Provider Extracts Characters**
   - Identifies main characters
   - Extracts appearance details
   - Creates Character records

6. **Status Update**
   - Status changes: GENERATING → READY
   - Sets `scenes_generated_at` timestamp
   - Project ready for media generation (Phase 7)

---

## Error Handling

### Invalid Project ID

```bash
curl -X POST http://localhost:8000/api/v1/ai/generate-story \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"project_id": 99999}'
```

**Expected Response:**
```json
{
  "detail": "Project 99999 not found"
}
```
**Status Code:** 400

---

### Missing Anthropic API Key

If `ANTHROPIC_API_KEY` not configured:

```bash
curl -X POST http://localhost:8000/api/v1/ai/generate-story \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d "{\"project_id\": $PROJECT_ID}"
```

**Expected Response:**
```json
{
  "detail": "AI service not available. Please check configuration."
}
```
**Status Code:** 503

---

### AI Generation Failure

If Claude API fails:

**Expected Response:**
```json
{
  "detail": "Story generation failed: API error message"
}
```
**Status Code:** 500

**Project Status:** Changes to FAILED

---

## Performance Metrics

### Expected Timing

- Story generation: 15-25 seconds
- Scene breakdown: 10-15 seconds
- Character extraction: 5-10 seconds
- **Total: 30-50 seconds**

### Token Usage (Approximate)

- Story generation: 2,000-3,000 tokens
- Scene breakdown: 1,500-2,500 tokens
- Character extraction: 500-1,000 tokens
- **Total: 4,000-6,500 tokens per project**

---

## Phase 5 Features

### Story Generation Service

1. **Complete Story Generation**
   - Story + Scenes + Characters in one call
   - Atomic operations with rollback on failure
   - Status tracking throughout process

2. **Partial Generation**
   - Story only (skip scenes/characters)
   - Flexible regeneration of individual parts

3. **Regeneration**
   - Regenerate scenes without changing story
   - Regenerate characters without changing story
   - Useful for refining output

4. **Error Handling**
   - Comprehensive error catching
   - Project status updates on failure
   - Detailed error messages

### AI Orchestration Service

1. **Provider Coordination**
   - Manages all AI providers
   - Lazy loading of providers
   - Optional providers (stubs for Phase 7)

2. **Testing & Info**
   - Test all provider connections
   - Get provider configuration info
   - Health check endpoints

3. **Future-Ready**
   - Prepared for image/audio/music generation
   - Placeholder methods for Phase 7

---

## Next Steps

Phase 5 is complete! Ready to proceed with:

- **Phase 6**: Storage Abstraction & Media Management
- **Phase 7**: AI Orchestration - Media Generation (images, audio, music)
- **Phase 8**: Celery Task Queue Setup
- **Phase 9**: Video Rendering Engine

---

## Phase 5 Summary

### What Was Built

1. **Story Generation Service**
   - Complete story generation with AI
   - Scene breakdown from stories
   - Character extraction
   - Regeneration capabilities

2. **AI Orchestration Service**
   - Coordinates all AI providers
   - Provider testing and info
   - Prepared for media generation

3. **API Endpoints**
   - 7 endpoints for story generation
   - Provider testing endpoints
   - Full CRUD for AI operations

4. **Database Integration**
   - Stores generated stories
   - Creates scenes automatically
   - Creates characters automatically
   - Timestamps for tracking

5. **Status Tracking**
   - Project status: DRAFT → GENERATING → READY/FAILED
   - Timestamps for each generation step
   - Error handling with status rollback

### Files Created: 4
### Lines of Code: ~1,000
### API Endpoints: 7

### Key Benefits

1. **AI-Powered**: Uses Claude 3.5 Sonnet for high-quality stories
2. **Structured Output**: Generates scenes and characters in database format
3. **Flexible**: Generate all at once or regenerate individual parts
4. **Error Resilient**: Comprehensive error handling and status tracking
5. **Provider Agnostic**: Works with any AI provider via abstraction layer

---

**Status**: ✅ **PHASE 5 COMPLETE**

**Ready for Phase 6**: Storage abstraction for media file management!
