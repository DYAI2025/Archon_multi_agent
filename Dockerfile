# KOMPLETTES Archon System mit Frontend für Fly.io
# Alles in einem - kein localhost!

# Stage 1: Frontend bauen
FROM node:20-slim AS frontend-builder
WORKDIR /app
COPY archon-ui-main/package*.json ./
RUN npm ci --only=production
COPY archon-ui-main/ ./
# Build mit API URL zu unserem Backend
ENV VITE_API_URL=/api
RUN npm run build

# Stage 2: Production Image
FROM python:3.12-slim

# System dependencies
RUN apt-get update && apt-get install -y \
    nginx \
    supervisor \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Python packages
RUN pip install --no-cache-dir \
    fastapi==0.115.5 \
    uvicorn==0.32.1 \
    httpx==0.28.1 \
    websockets==15.0.1 \
    pydantic==2.11.7 \
    pydantic-settings==2.10.1 \
    aiofiles==24.1.0 \
    python-multipart==0.0.20 \
    python-socketio==5.14.0 \
    supabase==2.10.0 \
    openai==1.58.1 \
    langchain==0.3.16

WORKDIR /app

# Copy Python backend
COPY python/src /app/src

# Copy frontend build
COPY --from=frontend-builder /app/dist /usr/share/nginx/html

# Nginx config - Frontend + API Proxy
RUN cat > /etc/nginx/sites-enabled/default << 'EOF'
server {
    listen 8080;
    root /usr/share/nginx/html;
    
    # Frontend
    location / {
        try_files $uri /index.html;
    }
    
    # API Proxy zu Backend
    location /api {
        proxy_pass http://127.0.0.1:8181/api;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
    
    # Socket.IO Proxy
    location /socket.io {
        proxy_pass http://127.0.0.1:8181/socket.io;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
    }
    
    # Health check
    location /health {
        return 200 "OK";
        add_header Content-Type text/plain;
    }
}
EOF

# Supervisor config - Alle Services zusammen
RUN cat > /etc/supervisor/conf.d/supervisord.conf << 'EOF'
[supervisord]
nodaemon=true
user=root
logfile=/var/log/supervisor/supervisord.log
pidfile=/var/run/supervisord.pid

[program:nginx]
command=nginx -g "daemon off;"
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0

[program:backend]
command=python -m uvicorn src.server.main:socket_app --host 127.0.0.1 --port 8181
directory=/app
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
environment=PYTHONPATH="/app",PYTHONUNBUFFERED="1"

[program:mcp]
command=python -m uvicorn src.mcp.enhanced_server:app --host 127.0.0.1 --port 8051
directory=/app
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
environment=PYTHONPATH="/app",PYTHONUNBUFFERED="1"
EOF

# Environment
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV PORT=8080

EXPOSE 8080

# Start everything!
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]