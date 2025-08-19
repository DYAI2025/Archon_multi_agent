# Dockerfile für Fly.io - Enhanced MCP Server
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy Python requirements
COPY python/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install MCP enhancement packages
RUN pip install --no-cache-dir \
    fastapi \
    uvicorn \
    httpx \
    websockets \
    pydantic \
    pydantic-settings \
    aiofiles

# Copy source code
COPY python/src /app/src
COPY integrations /app/integrations

# Set environment variables
ENV PYTHONPATH=/app:/app/integrations
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

# Expose port (Fly.io uses PORT env var)
EXPOSE 8080

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# Start command for Fly.io
CMD ["python", "-m", "uvicorn", "src.mcp.enhanced_server:app", "--host", "0.0.0.0", "--port", "8080"]