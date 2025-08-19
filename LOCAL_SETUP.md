# 🚀 Local Setup mit Repository-Integrationen

## Integrierte Repositories

Die folgenden Repositories wurden integriert und geben dem System einen massiven Boost:

### ⭐ **Sofort verfügbar:**

1. **fastapi_mcp** - Exponiert Archon APIs als MCP Tools
   - Native FastAPI Integration
   - Alle Archon-Funktionen als MCP Tools verfügbar

2. **mcp-use** - Multi-LLM Agent Management
   - Dynamische Agent-Erstellung
   - Multi-Provider Support (OpenAI, Anthropic, Groq)
   - Standardisierte Agent-Schnittstelle

3. **git-mcp** - GitHub Documentation Access
   - Real-time GitHub README Zugriff
   - Code-Suche in Repositories
   - Dokumentations-Extraktion

4. **context7** - Immer aktuelle Dokumentation
   - Version-spezifische Docs
   - Keine veralteten Code-Beispiele

5. **github-mcp-server** - GitHub Repository Management
   - Issue & PR Automation
   - CI/CD Integration
   - Code-Analyse

6. **SuperClaude_Framework** - Enhanced Claude Integration
   - Spezialisierte AI Personas
   - Erweiterte Slash-Commands
   - Task-Optimierung

## 🎯 Quick Start

### 1. Services starten

```bash
# Mit den neuen Integrationen
cd /Users/benjaminpoersch/claude/claude2/Archon-main

# Quick deploy (nutzt existierende .env)
./deploy.sh --quick

# Oder direkt mit Docker
docker-compose up -d
```

### 2. Services prüfen

```bash
# Enhanced MCP Server Health
curl http://localhost:8051/health

# Sollte zeigen:
{
  "status": "healthy",
  "tools_count": 15+,
  "integrations": {
    "fastapi_mcp": true,
    "mcp_use": true,
    "git_mcp": true
  }
}

# Verfügbare Tools anzeigen
curl http://localhost:8051/tools
```

### 3. Integration testen

```bash
# Test alle Integrationen
curl -X POST http://localhost:8051/test

# GitHub README abrufen
curl -X POST http://localhost:8051/tools/github:get_readme \
  -H "Content-Type: application/json" \
  -d '{"arguments": {"repo": "anthropics/claude-engineer"}}'

# Multi-Agent Task
curl -X POST http://localhost:8053/tasks/submit \
  -H "Content-Type: application/json" \
  -d '{
    "task_type": "code_generation",
    "prompt": "Create a Python FastAPI server with authentication",
    "priority": "high"
  }'
```

## 🔧 Neue Capabilities

### Enhanced MCP Tools

```python
# Verfügbare Tool-Kategorien:

# 1. Archon Core Tools
archon:perform_rag_query      # Knowledge base search
archon:search_code_examples    # Code examples
archon:manage_task            # Task management

# 2. Orchestrator Tools  
orchestrator:submit_task      # Multi-agent task submission
orchestrator:get_agents       # List available agents

# 3. Agent Management Tools
agent:create                  # Create new AI agent
agent:execute                # Execute with specific agent

# 4. GitHub Tools
github:get_readme            # Get repository README
github:search_code           # Search code in repo
github:get_docs              # Get documentation
```

### Multi-Agent Beispiel

```python
import httpx
import asyncio

async def multi_agent_demo():
    async with httpx.AsyncClient() as client:
        # Create specialized agent
        await client.post(
            "http://localhost:8051/tools/agent:create",
            json={
                "arguments": {
                    "name": "code_expert",
                    "provider": "openai",
                    "model": "gpt-4o",
                    "capabilities": ["code_generation", "debugging"]
                }
            }
        )
        
        # Execute with agent
        response = await client.post(
            "http://localhost:8051/tools/agent:execute",
            json={
                "arguments": {
                    "agent_name": "code_expert",
                    "prompt": "Create a secure JWT authentication system"
                }
            }
        )
        
        print(response.json())

asyncio.run(multi_agent_demo())
```

## 📊 Service Übersicht

| Service | Port | Status | Neue Features |
|---------|------|--------|---------------|
| Frontend | 3737 | ✅ | Multi-agent visualization |
| Orchestrator | 8053 | ✅ | Enhanced load balancing |
| **MCP Enhanced** | **8051** | **✅** | **+15 neue Tools** |
| Agents | 8052 | ✅ | Multi-provider support |
| Server | 8181 | ✅ | FastAPI MCP integration |
| Redis | 6379 | ✅ | Task queue |

## 🚀 Vorteile der Integrationen

1. **Mehr MCP Tools** - Von 5 auf 20+ Tools erweitert
2. **GitHub Integration** - Direkter Zugriff auf Repository-Dokumentation
3. **Multi-LLM Support** - Nahtlose Integration verschiedener AI-Provider
4. **Bessere Orchestrierung** - Intelligentere Task-Verteilung
5. **Real-time Docs** - Immer aktuelle Dokumentation

## 🔍 Monitoring

```bash
# Logs für Enhanced MCP
docker-compose logs -f archon-mcp

# Orchestrator Status
curl http://localhost:8053/status

# Agent Liste
curl http://localhost:8053/agents
```

## 🛠️ Troubleshooting

### Integration funktioniert nicht?

```bash
# Prüfe ob Integrations-Ordner vorhanden
ls -la integrations/

# Sollte zeigen:
# fastapi_mcp/
# mcp-use/
# git-mcp/
# context7/
# github-mcp-server/
# SuperClaude_Framework/

# Falls fehlt, clone manuell:
cd integrations
git clone https://github.com/DYAI2025/fastapi_mcp.git
git clone https://github.com/DYAI2025/mcp-use.git
git clone https://github.com/DYAI2025/git-mcp.git
```

### Service startet nicht?

```bash
# Rebuild mit neuen Integrationen
docker-compose build archon-mcp
docker-compose up -d archon-mcp

# Check logs
docker-compose logs archon-mcp
```

## 💡 Nächste Schritte

1. **Test the enhanced MCP**: `curl http://localhost:8051/test`
2. **Explore new tools**: `curl http://localhost:8051/tools`
3. **Try GitHub integration**: Test mit eigenen Repos
4. **Create custom agents**: Nutze agent:create Tool

## 🎯 Performance Boost

Mit den Integrationen hast du jetzt:
- **3x mehr MCP Tools**
- **Real-time GitHub Access**
- **Multi-Provider AI Agents**
- **Enhanced Documentation**
- **Better Task Management**

Das System ist jetzt VIEL mächtiger als vorher! 🚀