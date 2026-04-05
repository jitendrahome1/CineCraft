FROM python:3.11-slim

# Install system dependencies (including FFmpeg)
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libpq-dev \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements first (for layer caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create storage directories
RUN mkdir -p /app/storage/{projects,scenes,images,audio,subtitles,videos}

# Create __init__.py files for Python packages
RUN touch /app/app/__init__.py \
    && touch /app/app/core/__init__.py \
    && touch /app/app/db/__init__.py \
    && touch /app/app/models/__init__.py \
    && touch /app/app/repositories/__init__.py \
    && touch /app/app/services/__init__.py \
    && touch /app/app/providers/__init__.py \
    && touch /app/app/providers/base/__init__.py \
    && touch /app/app/providers/ai/__init__.py \
    && touch /app/app/providers/image/__init__.py \
    && touch /app/app/providers/voice/__init__.py \
    && touch /app/app/providers/music/__init__.py \
    && touch /app/app/providers/storage/__init__.py \
    && touch /app/app/api/__init__.py \
    && touch /app/app/api/v1/__init__.py \
    && touch /app/app/schemas/__init__.py \
    && touch /app/app/tasks/__init__.py \
    && touch /app/app/utils/__init__.py

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
