# Archon Multi-Agent System - GitHub Copilot Instructions

**ALWAYS follow these instructions first and only fallback to additional search and context gathering if the information here is incomplete or found to be in error.**

## Working Effectively

Archon is a microservices-based knowledge management system with MCP (Model Context Protocol) integration that enables AI coding assistants to access custom knowledge bases and task management.

### Bootstrap, Build, and Test the Repository

**CRITICAL SETUP - Prerequisites:**
- Docker Desktop installed and running
- Node.js 18+ and npm
- Python 3.12
- uv package manager (install with: `pip install uv`)
- Supabase account (free tier works) for database

**Environment Setup:**
```bash
# 1. Copy environment template
cp .env.example .env

# 2. Edit .env and add YOUR Supabase credentials:
# SUPABASE_URL=https://your-project.supabase.co
# SUPABASE_SERVICE_KEY=your-service-key-here
# (Get these from Supabase project settings > API section)
```

**Database Setup (MANDATORY):**
```bash
# Execute in your Supabase SQL Editor (https://supabase.com/dashboard)
# Copy, paste, and execute the contents of: migration/complete_setup.sql
```

**Frontend Setup and Testing:**
```bash
cd archon-ui-main
npm install                    # Takes ~27 seconds
npm test                      # Takes ~3 seconds, may have 1 failing test (expected)
npm run build                 # Takes ~12 seconds, builds successfully
npm run lint                  # Takes ~4 seconds, shows 244 warnings/3 errors (known issues)
```

**Backend Setup and Testing:**
```bash
cd python
uv sync                       # Takes ~39 seconds, installs all dependencies
uv run pytest tests/test_api_essentials.py -v  # Takes ~16 seconds, all tests pass
uv run ruff check             # Takes <1 second, shows 809 style issues (known)
uv run mypy src/              # Takes ~88 seconds, shows 519 type errors (known)
```

**Docker Build Process:**
```bash
# WARNING: Docker builds can fail due to SSL certificate issues in some environments
# If build fails with SSL errors, this is a KNOWN LIMITATION - document it

# NEVER CANCEL: Docker builds typically take 45-60 minutes, but can take up to 90+ minutes in some environments. Set timeout to 90+ minutes to avoid premature cancellation.
docker compose build --no-cache    # Full build: 45-60 minutes typical, up to 90+ minutes in some environments
docker compose up -d               # Start all services: ~2 minutes
```

**Service Health Verification:**
```bash
# Verify all services are running
docker compose ps

# Test service endpoints
curl http://localhost:8181/health  # Server health
curl http://localhost:8051/health  # MCP health  
curl http://localhost:8052/health  # Agents health
curl http://localhost:3737         # Frontend (should return HTML)
```

### Architecture Overview

Archon uses true microservices architecture:

```
Frontend (3737) ↔ Server (8181) ↔ MCP (8051) ↔ Agents (8052)
                       ↓
                 Supabase DB + Redis (6379)
                       ↓
              Orchestrator (8053)
```

**Service Responsibilities:**
- **Frontend**: React + TypeScript + Vite + TailwindCSS (`archon-ui-main/`)
- **Server**: FastAPI + Socket.IO + crawling + business logic (`python/src/server/`)
- **MCP Server**: Lightweight HTTP MCP protocol interface (`python/src/mcp/`)
- **Agents**: PydanticAI agents for AI/ML operations (`python/src/agents/`)
- **Orchestrator**: Multi-agent coordination (`python/src/orchestrator/`)

## Validation Requirements

**NEVER CANCEL builds or long-running commands.** Always wait for completion.

**Manual Functional Testing (MANDATORY):**
After making changes, ALWAYS test actual functionality through the UI:

1. **Access Web Interface**: Open http://localhost:3737
2. **Test Knowledge Management**:
   - Go to Knowledge Base → "Crawl Website"
   - Enter a documentation URL (e.g., https://ai.pydantic.dev/llms-full.txt)
   - Wait for crawling to complete (~2-5 minutes)
   - Test search functionality
3. **Test MCP Integration**:
   - Go to MCP Dashboard
   - Verify connection status shows "Connected"
   - Test tool execution if possible
4. **Test Settings**:
   - Go to Settings → Select LLM provider
   - Set API key if available
   - Verify settings save correctly

**CI/CD Validation:**
```bash
# Frontend validation
cd archon-ui-main
npm run test:coverage        # Full test suite with coverage
npm run lint                # ESLint (expect warnings)

# Backend validation  
cd python
uv run pytest              # All tests (expect some warnings)
uv run ruff check          # Linting (expect style issues)
uv run mypy src/           # Type checking (expect errors)
```

## Timing Expectations and Timeouts

**CRITICAL: NEVER CANCEL these operations - use these minimum timeout values:**

- **npm install**: 30 seconds (set timeout: 60+ seconds)
- **npm test**: 5 seconds (set timeout: 30+ seconds)  
- **npm run build**: 15 seconds (set timeout: 60+ seconds)
- **uv sync**: 45 seconds (set timeout: 120+ seconds)
- **pytest tests**: 20 seconds (set timeout: 60+ seconds)
- **mypy type check**: 90 seconds (set timeout: 180+ seconds)
- **Docker builds**: 45-60 minutes (set timeout: 90+ minutes)
- **Docker service startup**: 3-5 minutes (set timeout: 10+ minutes)

## Known Issues and Limitations

**Docker Build Failures:**
- SSL certificate errors with PyPI are common in some environments
- **Document this as**: "Docker build fails due to SSL certificate issues - known limitation in some environments"
- **Workaround**: Use pre-built images or fix certificates

**Linting/Type Issues:**
- Frontend: 244 warnings/3 errors in ESLint (legacy code)
- Backend: 809 style issues in ruff, 519 type errors in mypy
- **These are known issues** - document but don't require fixing

**Test Failures:**
- Frontend may have 1 failing test (onboarding detection)
- This is expected and acceptable

## Key Development Commands

**Start Development Environment:**
```bash
# Backend with hot reload
docker compose up archon-server archon-mcp archon-agents --build

# Frontend with hot reload (separate terminal)
cd archon-ui-main && npm run dev
```

**Add New API Endpoint:**
1. Create route handler in `python/src/server/api_routes/`
2. Add service logic in `python/src/server/services/`
3. Include router in `python/src/server/main.py`
4. Update frontend service in `archon-ui-main/src/services/`

**Debug MCP Issues:**
```bash
curl http://localhost:8051/health              # Check MCP health
docker compose logs archon-mcp                 # View MCP logs
curl http://localhost:8051/tools               # List available tools
```

## Important File Locations

**Configuration:**
- `.env` - Environment variables (create from `.env.example`)
- `docker-compose.yml` - Service orchestration
- `migration/complete_setup.sql` - Database schema

**Frontend Structure:**
- `archon-ui-main/src/components/` - UI components
- `archon-ui-main/src/pages/` - Main pages
- `archon-ui-main/src/services/` - API services
- `archon-ui-main/test/` - Frontend tests

**Backend Structure:**
- `python/src/server/` - Main FastAPI app
- `python/src/mcp/` - MCP server implementation  
- `python/src/agents/` - PydanticAI agents
- `python/tests/` - Backend tests

**Package Management:**
- Frontend: `npm` (see `archon-ui-main/package.json`)
- Backend: `uv` (see `python/pyproject.toml`)

## Development Patterns

**Error Handling Philosophy:**
- **Fail fast**: Service startup, missing config, database connection failures
- **Continue with logging**: Batch processing, background tasks, optional features
- **Never store corrupted data**: Skip failed items entirely

**Code Quality:**
- Python: 120 character line length, Ruff + MyPy (expect issues)
- TypeScript: ESLint configured (expect warnings)
- **Always run linting before commits** even if it shows issues

**Testing Strategy:**
- Frontend: Vitest for unit/integration tests
- Backend: pytest with async support
- Docker: Health checks and service communication tests
- **Manual validation required** - automated tests don't cover full functionality

## Supabase Integration

**Required Tables:** `sources`, `documents`, `projects`, `tasks`, `code_examples`
**Vector Search:** Uses pgvector for embeddings
**Real-time:** Socket.IO for live updates

**Setup Commands:**
```sql
-- Execute in Supabase SQL Editor
-- File: migration/complete_setup.sql (copy entire contents)
```

## MCP Tools Available

When connected to AI coding assistants:
- `archon:perform_rag_query` - Search knowledge base
- `archon:search_code_examples` - Find code snippets  
- `archon:manage_project` - Project operations
- `archon:manage_task` - Task management
- `archon:get_available_sources` - List knowledge sources

## Common Troubleshooting

**"Dependencies not found"**: Run `uv sync` in python/ or `npm install` in archon-ui-main/
**"Database connection failed"**: Check SUPABASE_URL and SUPABASE_SERVICE_KEY in .env
**"Service not responding"**: Verify Docker containers are running with `docker compose ps`
**"MCP connection issues"**: Check MCP health endpoint and service logs
**"Build timeouts"**: Increase timeout values - builds legitimately take 45+ minutes

## Security Notes

- **Never commit secrets** to version control
- **API keys stored encrypted** in database via Settings UI
- **Service-to-service communication** uses Docker internal networks
- **Frontend proxies API calls** via Vite in development

---

**Remember**: Archon is in alpha development - expect rough edges. Focus on functionality over perfect code quality. Always test actual user workflows after making changes.