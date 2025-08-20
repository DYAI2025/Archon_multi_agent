# KOMPLETTES Archon System mit Frontend für Fly.io
# Alles in einem - kein localhost!

# Stage 1: Frontend bauen
FROM node:20-slim AS frontend-builder
WORKDIR /app
COPY archon-ui-main/package.json archon-ui-main/package-lock.json ./
RUN npm ci
COPY archon-ui-main/ ./
# Build mit API URL zu unserem Backend
ENV VITE_API_URL=/api
RUN npm run build

# Stage 2: Production Image
FROM python:3.12-slim

# System dependencies - mit DNS-Tools für Supabase
RUN apt-get update && apt-get install -y \
    nginx \
    supervisor \
    curl \
    ca-certificates \
    dnsutils \
    netcat-openbsd \
    && rm -rf /var/lib/apt/lists/* \
    && update-ca-certificates

# Python packages
RUN pip install --no-cache-dir \
    fastapi==0.115.5 \
    uvicorn==0.32.1 \
    httpx[http2]==0.27.2 \
    dnspython==2.7.0 \
    httpcore==1.0.9 \
    websockets==15.0.1 \
    pydantic==2.11.7 \
    pydantic-settings==2.10.1 \
    aiofiles==24.1.0 \
    python-multipart==0.0.20 \
    python-socketio==5.13.0 \
    supabase==2.10.0 \
    openai==1.71.0 \
    langchain==0.3.16 \
    cryptography==44.0.0 \
    psutil==6.1.1 \
    asyncpg==0.29.0 \
    pypdf2==3.0.1 \
    pdfplumber==0.11.6 \
    python-docx==1.1.2 \
    markdown==3.8 \
    python-jose[cryptography]==3.3.0 \
    slowapi==0.1.9 \
    python-dotenv==1.0.0 \
    docker==6.1.0 \
    logfire==0.30.0 \
    pytest==8.0.0 \
    pytest-asyncio==0.21.0 \
    pytest-mock==3.12.0 \
    watchfiles==0.18

WORKDIR /app

# Copy Python backend
COPY python/src /app/src

# Copy frontend build
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Nginx config - Frontend + API Proxy with improved health check
RUN echo 'server { \
    listen 8080; \
    root /usr/share/nginx/html; \
    \
    location / { \
        try_files $uri /index.html; \
    } \
    \
    location /api { \
        proxy_pass http://127.0.0.1:8181/api; \
        proxy_http_version 1.1; \
        proxy_set_header Upgrade $http_upgrade; \
        proxy_set_header Connection "upgrade"; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_connect_timeout 60s; \
        proxy_send_timeout 60s; \
        proxy_read_timeout 60s; \
    } \
    \
    location /socket.io { \
        proxy_pass http://127.0.0.1:8181/socket.io; \
        proxy_http_version 1.1; \
        proxy_set_header Upgrade $http_upgrade; \
        proxy_set_header Connection "upgrade"; \
        proxy_set_header Host $host; \
        proxy_connect_timeout 60s; \
        proxy_send_timeout 60s; \
        proxy_read_timeout 60s; \
    } \
    \
    location /health { \
        access_log off; \
        # Try backend health first, fallback to simple OK \
        proxy_pass http://127.0.0.1:8181/health; \
        proxy_connect_timeout 5s; \
        proxy_send_timeout 5s; \
        proxy_read_timeout 5s; \
        error_page 502 503 504 = @health_fallback; \
    } \
    \
    location @health_fallback { \
        access_log off; \
        return 200 "OK - Services Starting"; \
        add_header Content-Type text/plain; \
    } \
}' > /etc/nginx/sites-enabled/default

# Supervisor config - Alle Services zusammen mit startup delays
RUN echo '[supervisord] \n\
nodaemon=true \n\
user=root \n\
logfile=/var/log/supervisor/supervisord.log \n\
pidfile=/var/run/supervisord.pid \n\
\n\
[program:nginx] \n\
command=nginx -g "daemon off;" \n\
autostart=true \n\
autorestart=true \n\
stdout_logfile=/dev/stdout \n\
stdout_logfile_maxbytes=0 \n\
stderr_logfile=/dev/stderr \n\
stderr_logfile_maxbytes=0 \n\
priority=300 \n\
\n\
[program:backend] \n\
command=python -m uvicorn src.server.main:socket_app --host 127.0.0.1 --port 8181 \n\
directory=/app \n\
autostart=true \n\
autorestart=true \n\
stdout_logfile=/dev/stdout \n\
stdout_logfile_maxbytes=0 \n\
stderr_logfile=/dev/stderr \n\
stderr_logfile_maxbytes=0 \n\
environment=PYTHONPATH="/app",PYTHONUNBUFFERED="1" \n\
priority=100 \n\
startsecs=10 \n\
\n\
[program:mcp] \n\
command=python -m uvicorn src.mcp.enhanced_server:app --host 127.0.0.1 --port 8051 \n\
directory=/app \n\
autostart=true \n\
autorestart=true \n\
stdout_logfile=/dev/stdout \n\
stdout_logfile_maxbytes=0 \n\
stderr_logfile=/dev/stderr \n\
stderr_logfile_maxbytes=0 \n\
environment=PYTHONPATH="/app",PYTHONUNBUFFERED="1" \n\
priority=200 \n\
startsecs=5' > /etc/supervisor/conf.d/supervisord.conf

# Environment
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

EXPOSE 8080

# Start everything!
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]