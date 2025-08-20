# Supabase Configuration Guide for Archon

This guide explains how to properly configure Supabase for the Archon multi-agent system.

## Quick Setup

1. **Create a Supabase Project**
   - Visit [supabase.com](https://supabase.com) and create a new project
   - Wait for your project to be fully provisioned

2. **Get Your Credentials**
   - Go to Settings → API in your Supabase dashboard
   - Copy your Project URL and Service Key (service_role secret)

3. **Update Environment Variables**
   ```bash
   # In your .env file
   SUPABASE_URL=https://your-project-ref.supabase.co
   SUPABASE_SERVICE_KEY=your-service-role-key-here
   ```

4. **Initialize the Database**
   - Open the SQL Editor in your Supabase dashboard
   - Copy and paste the contents of `migration/complete_setup.sql`
   - Execute the SQL script

## Configuration Files

### Required Environment Variables

The following environment variables must be set in your `.env` file:

```bash
# Supabase Configuration (REQUIRED)
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here

# Service Ports (Automatically configured)
ARCHON_SERVER_PORT=8181
ARCHON_MCP_PORT=8051
ARCHON_AGENTS_PORT=8052
ARCHON_UI_PORT=3737

# Optional Configuration
LOGFIRE_TOKEN=your-logfire-token-here
LOG_LEVEL=INFO
```

### Database Schema

The `migration/complete_setup.sql` file contains:
- Required PostgreSQL extensions (vector, pgcrypto)
- Core tables for knowledge management
- Settings and credentials tables
- Proper indexes and triggers

Key tables:
- `archon_settings` - Application settings and encrypted credentials
- `sources` - Crawled websites and uploaded documents  
- `documents` - Processed document chunks with embeddings
- `projects` - Project management data
- `tasks` - Task tracking
- `code_examples` - Extracted code snippets

## Testing Your Configuration

### 1. Basic Connection Test
```bash
python python/test_supabase_connection.py
```

### 2. Full Integration Test
```bash
python test_integration.py
```

### 3. Manual Verification
Start the services and verify connectivity:
```bash
# Start backend
cd python && python -m uvicorn src.server.main:socket_app --host 0.0.0.0 --port 8181

# Start frontend (in another terminal)
cd archon-ui-main && npm run dev

# Test health endpoint
curl http://localhost:8181/health
```

## Troubleshooting

### Common Issues

**"Invalid API key" Error**
- Verify you're using the service_role key, not the anon key
- Check that your Supabase project is active
- Ensure the key is correctly copied (no extra spaces)

**Database Connection Timeout**
- Check your internet connection
- Verify the Supabase URL format
- Ensure your project isn't paused

**Tables Not Found**
- Run the complete_setup.sql migration script
- Check that the script executed without errors
- Verify you have the correct database permissions

### Service Status

The health endpoint provides detailed status information:

```json
{
  "status": "healthy|degraded|unhealthy",
  "service": "archon-backend", 
  "ready": true,
  "initialization_complete": true,
  "details": {
    "initialization": "complete",
    "database": "connected|disconnected|error"
  }
}
```

- `healthy`: All systems operational
- `degraded`: Core functionality works, some features limited
- `unhealthy`: Critical failures, system not usable

## Security Notes

- Never commit your actual Supabase credentials to version control
- Use environment variables or secure secret management
- The service_role key has full database access - treat it as sensitive
- Consider using Row Level Security (RLS) policies for production

## Integration Features

The Archon system integrates several MCP (Model Context Protocol) tools:

### Core Integrations
- **fastapi_mcp**: Exposes FastAPI endpoints as MCP tools
- **mcp-use**: Multi-LLM agent management capabilities  
- **Gitingest-MCP**: GitHub documentation and repository access

### Integration Status
Check integration status with:
```bash
python -c "from python.src.mcp.enhanced_server import app; print('Integrations loaded')"
```

### Configuration Complete
Once properly configured with real Supabase credentials, all features will be available:
- Knowledge base management with vector search
- Real-time project and task tracking
- Document processing and chunking
- Code extraction and analysis
- Multi-agent coordination
- MCP tool integration for AI assistants

## Next Steps

1. Update `.env` with your real Supabase credentials
2. Run the database migration script
3. Test all functionality with `python test_integration.py`
4. Start using Archon for knowledge management and project automation!

For additional help, see the main README.md and documentation in the `docs/` directory.