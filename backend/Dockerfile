# ==============================================================================
# TravelSenseAI — Backend Production Dockerfile
# Base: Python 3.11 Slim on Debian Bookworm
# ==============================================================================

FROM python:3.11-slim as base

# Set environment flags
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# Install minimal system dependencies for healthcheck and compilation
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies first for caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app /app/app

# Create directory for persistent SQLite data
RUN mkdir -p /data && chmod 777 /data

# Expose backend service port
EXPOSE 8000

# Health check against FastAPI health endpoint
HEALTHCHECK --interval=15s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/api/health || exit 1

# Production ASGI server launch command
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]

