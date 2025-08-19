# Dockerfile für Fly.io - Enhanced MCP Server
# BOMBENSICHER - Keine externen Files nötig!
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages - ALLE direkt hier!
RUN pip install --no-cache-dir \
    fastapi==0.115.5 \
    uvicorn==0.32.1 \
    httpx==0.28.1 \
    websockets==15.0.1 \
    pydantic==2.11.7 \
    pydantic-settings==2.10.1 \
    aiofiles==24.1.0 \
    python-multipart==0.0.20 \
    redis==5.2.1

# Copy ONLY what exists
COPY python/src /app/src

# Create integrations folder
RUN mkdir -p /app/integrations

# Environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose port für Fly.io
EXPOSE 8080

# Start command
CMD ["python", "-m", "uvicorn", "src.mcp.enhanced_server:app", "--host", "0.0.0.0", "--port", "8080"]