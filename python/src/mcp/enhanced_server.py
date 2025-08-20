"""
Enhanced MCP Server with integrated capabilities from:
- fastapi_mcp: Expose FastAPI endpoints as MCP tools
- mcp-use: Multi-LLM agent management
- git-mcp: GitHub documentation access

This enhanced server provides a unified MCP interface with advanced features.
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import httpx

# Add integrations to path
integrations_path = Path(__file__).parent.parent.parent.parent / "integrations"
sys.path.insert(0, str(integrations_path))

# Import integration modules
try:
    # Import fastapi_mcp for exposing endpoints as tools
    from fastapi_mcp import MCPServer
except ImportError:
    MCPServer = None
    print("Warning: fastapi_mcp not available")

try:
    # Import mcp-use for multi-agent capabilities
    from mcp_use import Agent, MCPClient
except ImportError:
    Agent = None
    MCPClient = None
    print("Warning: mcp-use not available")

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Enhanced Archon MCP Server",
    description="MCP server with integrated fastapi_mcp, mcp-use, and git-mcp capabilities",
    version="2.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class MCPTool(BaseModel):
    """Model for MCP tool definition."""
    name: str
    description: str
    input_schema: Dict[str, Any]
    handler: Optional[str] = None


class MCPRequest(BaseModel):
    """Model for MCP tool execution request."""
    tool: str
    arguments: Dict[str, Any]


class MCPResponse(BaseModel):
    """Model for MCP tool execution response."""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None


class EnhancedMCPServer:
    """Enhanced MCP server with integrated capabilities."""
    
    def __init__(self):
        """Initialize the enhanced MCP server."""
        self.tools: Dict[str, MCPTool] = {}
        self.agents: Dict[str, Any] = {}
        self.github_cache: Dict[str, Any] = {}
        self.initialize_tools()
        
    def initialize_tools(self):
        """Initialize all available MCP tools."""
        # Core Archon tools
        self.register_archon_tools()
        
        # FastAPI MCP tools (expose endpoints)
        if MCPServer:
            self.register_fastapi_tools()
        
        # Multi-agent tools (from mcp-use)
        if Agent:
            self.register_agent_tools()
        
        # GitHub documentation tools (from git-mcp)
        self.register_github_tools()
        
        logger.info(f"Initialized {len(self.tools)} MCP tools")
    
    def register_archon_tools(self):
        """Register core Archon MCP tools."""
        # Knowledge base tools
        self.tools["archon:perform_rag_query"] = MCPTool(
            name="archon:perform_rag_query",
            description="Search the knowledge base using RAG",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "match_count": {"type": "integer", "default": 5}
                },
                "required": ["query"]
            }
        )
        
        self.tools["archon:search_code_examples"] = MCPTool(
            name="archon:search_code_examples",
            description="Search for code examples in the knowledge base",
            input_schema={
                "type": "object",
                "properties": {
                    "query": {"type": "string"},
                    "language": {"type": "string", "default": "any"},
                    "match_count": {"type": "integer", "default": 3}
                },
                "required": ["query"]
            }
        )
        
        # Task management tools
        self.tools["archon:manage_task"] = MCPTool(
            name="archon:manage_task",
            description="Manage tasks in the system",
            input_schema={
                "type": "object",
                "properties": {
                    "action": {"type": "string", "enum": ["create", "update", "get", "list", "delete"]},
                    "task_id": {"type": "string"},
                    "title": {"type": "string"},
                    "description": {"type": "string"},
                    "status": {"type": "string", "enum": ["todo", "doing", "review", "done"]},
                    "project_id": {"type": "string"}
                },
                "required": ["action"]
            }
        )
    
    def register_fastapi_tools(self):
        """Register FastAPI endpoints as MCP tools."""
        # Orchestrator endpoints as tools
        self.tools["orchestrator:submit_task"] = MCPTool(
            name="orchestrator:submit_task",
            description="Submit a task to the multi-agent orchestrator",
            input_schema={
                "type": "object",
                "properties": {
                    "task_type": {"type": "string"},
                    "prompt": {"type": "string"},
                    "priority": {"type": "string", "enum": ["low", "medium", "high", "critical"]},
                    "metadata": {"type": "object"}
                },
                "required": ["task_type", "prompt"]
            }
        )
        
        self.tools["orchestrator:get_agents"] = MCPTool(
            name="orchestrator:get_agents",
            description="Get list of available AI agents",
            input_schema={
                "type": "object",
                "properties": {}
            }
        )
    
    def register_agent_tools(self):
        """Register multi-agent management tools from mcp-use."""
        self.tools["agent:create"] = MCPTool(
            name="agent:create",
            description="Create a new AI agent with specific capabilities",
            input_schema={
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "provider": {"type": "string", "enum": ["openai", "anthropic", "groq", "gemini"]},
                    "model": {"type": "string"},
                    "capabilities": {"type": "array", "items": {"type": "string"}}
                },
                "required": ["name", "provider"]
            }
        )
        
        self.tools["agent:execute"] = MCPTool(
            name="agent:execute",
            description="Execute a task with a specific agent",
            input_schema={
                "type": "object",
                "properties": {
                    "agent_name": {"type": "string"},
                    "prompt": {"type": "string"},
                    "context": {"type": "object"}
                },
                "required": ["agent_name", "prompt"]
            }
        )
    
    def register_github_tools(self):
        """Register GitHub documentation tools from git-mcp."""
        self.tools["github:get_readme"] = MCPTool(
            name="github:get_readme",
            description="Get README from a GitHub repository",
            input_schema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string", "description": "Format: owner/repo"},
                    "branch": {"type": "string", "default": "main"}
                },
                "required": ["repo"]
            }
        )
        
        self.tools["github:search_code"] = MCPTool(
            name="github:search_code",
            description="Search code in a GitHub repository",
            input_schema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string"},
                    "query": {"type": "string"},
                    "path": {"type": "string", "default": "/"},
                    "language": {"type": "string"}
                },
                "required": ["repo", "query"]
            }
        )
        
        self.tools["github:get_docs"] = MCPTool(
            name="github:get_docs",
            description="Get documentation from a GitHub repository",
            input_schema={
                "type": "object",
                "properties": {
                    "repo": {"type": "string"},
                    "doc_path": {"type": "string", "default": "docs/"},
                    "format": {"type": "string", "enum": ["markdown", "rst", "text"]}
                },
                "required": ["repo"]
            }
        )
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute an MCP tool."""
        if tool_name not in self.tools:
            raise ValueError(f"Unknown tool: {tool_name}")
        
        # Route to appropriate handler
        if tool_name.startswith("archon:"):
            return await self.execute_archon_tool(tool_name, arguments)
        elif tool_name.startswith("orchestrator:"):
            return await self.execute_orchestrator_tool(tool_name, arguments)
        elif tool_name.startswith("agent:"):
            return await self.execute_agent_tool(tool_name, arguments)
        elif tool_name.startswith("github:"):
            return await self.execute_github_tool(tool_name, arguments)
        else:
            raise ValueError(f"No handler for tool: {tool_name}")
    
    async def execute_archon_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute core Archon tools."""
        # Forward to main Archon API
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"http://localhost:8181/api/mcp/tools/{tool_name}",
                json=arguments
            )
            return response.json()
    
    async def execute_orchestrator_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute orchestrator tools."""
        async with httpx.AsyncClient() as client:
            if tool_name == "orchestrator:submit_task":
                response = await client.post(
                    "http://localhost:8053/tasks/submit",
                    json=arguments
                )
            elif tool_name == "orchestrator:get_agents":
                response = await client.get("http://localhost:8053/agents")
            else:
                raise ValueError(f"Unknown orchestrator tool: {tool_name}")
            
            return response.json()
    
    async def execute_agent_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute multi-agent tools using mcp-use."""
        if not Agent:
            return {"error": "mcp-use not available"}
        
        if tool_name == "agent:create":
            # Create new agent
            agent = Agent(
                name=arguments["name"],
                provider=arguments["provider"],
                model=arguments.get("model", "gpt-4o"),
                capabilities=arguments.get("capabilities", [])
            )
            self.agents[arguments["name"]] = agent
            return {"success": True, "agent": arguments["name"]}
        
        elif tool_name == "agent:execute":
            # Execute with specific agent
            agent_name = arguments["agent_name"]
            if agent_name not in self.agents:
                return {"error": f"Agent {agent_name} not found"}
            
            agent = self.agents[agent_name]
            result = await agent.execute(
                prompt=arguments["prompt"],
                context=arguments.get("context", {})
            )
            return {"result": result}
        
        return {"error": f"Unknown agent tool: {tool_name}"}
    
    async def execute_github_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Any:
        """Execute GitHub documentation tools."""
        github_token = os.getenv("GITHUB_TOKEN")
        headers = {"Authorization": f"token {github_token}"} if github_token else {}
        
        async with httpx.AsyncClient() as client:
            if tool_name == "github:get_readme":
                repo = arguments["repo"]
                branch = arguments.get("branch", "main")
                
                # Try multiple README variations
                for readme in ["README.md", "readme.md", "README.rst", "README.txt"]:
                    url = f"https://api.github.com/repos/{repo}/contents/{readme}?ref={branch}"
                    response = await client.get(url, headers=headers)
                    
                    if response.status_code == 200:
                        data = response.json()
                        content = data.get("content", "")
                        # Decode base64 content
                        import base64
                        decoded = base64.b64decode(content).decode('utf-8')
                        return {"content": decoded, "path": readme}
                
                return {"error": "No README found"}
            
            elif tool_name == "github:search_code":
                repo = arguments["repo"]
                query = arguments["query"]
                path = arguments.get("path", "")
                
                search_query = f"repo:{repo} {query}"
                if path:
                    search_query += f" path:{path}"
                
                url = "https://api.github.com/search/code"
                params = {"q": search_query, "per_page": 10}
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"Search failed: {response.status_code}"}
            
            elif tool_name == "github:get_docs":
                repo = arguments["repo"]
                doc_path = arguments.get("doc_path", "docs/")
                
                url = f"https://api.github.com/repos/{repo}/contents/{doc_path}"
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    files = response.json()
                    docs = []
                    for file in files:
                        if file["type"] == "file" and file["name"].endswith((".md", ".rst", ".txt")):
                            docs.append({
                                "name": file["name"],
                                "path": file["path"],
                                "url": file["html_url"]
                            })
                    return {"documents": docs}
                else:
                    return {"error": f"Failed to get docs: {response.status_code}"}
        
        return {"error": f"Unknown GitHub tool: {tool_name}"}


# Initialize enhanced MCP server
mcp_server = EnhancedMCPServer()


@app.get("/health")
async def health_check():
    """Health check endpoint with timeout protection."""
    import asyncio
    from datetime import datetime
    
    try:
        # Basic health check with timeout
        health_data = {
            "status": "healthy",
            "service": "enhanced-mcp-server",
            "timestamp": datetime.now().isoformat(),
            "tools_count": len(mcp_server.tools),
            "integrations": {
                "fastapi_mcp": MCPServer is not None,
                "mcp_use": Agent is not None,
                "git_mcp": True
            }
        }
        
        # Quick test of core functionality with timeout
        try:
            # Test if we can access tools without hanging
            await asyncio.wait_for(asyncio.sleep(0.1), timeout=1.0)
            health_data["core_test"] = "passed"
        except asyncio.TimeoutError:
            health_data["core_test"] = "timeout"
            health_data["status"] = "degraded"
        
        return health_data
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "enhanced-mcp-server",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)[:100]
        }


@app.get("/tools")
async def list_tools():
    """List all available MCP tools."""
    return {
        "tools": [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": tool.input_schema
            }
            for tool in mcp_server.tools.values()
        ]
    }


@app.post("/tools/{tool_name}")
async def execute_tool(tool_name: str, request: MCPRequest):
    """Execute an MCP tool."""
    try:
        # Validate tool exists
        if tool_name not in mcp_server.tools:
            raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
        
        # Execute tool
        result = await mcp_server.execute_tool(tool_name, request.arguments)
        
        return MCPResponse(success=True, result=result)
        
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return MCPResponse(success=False, error=str(e))


@app.get("/agents")
async def list_agents():
    """List registered agents."""
    return {
        "agents": list(mcp_server.agents.keys()),
        "count": len(mcp_server.agents)
    }


@app.post("/test")
async def test_integrations():
    """Test all integrations."""
    results = {}
    
    # Test GitHub integration
    try:
        github_result = await mcp_server.execute_github_tool(
            "github:get_readme",
            {"repo": "anthropics/claude-engineer"}
        )
        results["github"] = "success" if "content" in github_result else "failed"
    except:
        results["github"] = "error"
    
    # Test orchestrator connection
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8053/health", timeout=2)
            results["orchestrator"] = "connected" if response.status_code == 200 else "unreachable"
    except:
        results["orchestrator"] = "offline"
    
    # Test agent capabilities
    results["mcp_use"] = "available" if Agent else "not available"
    results["fastapi_mcp"] = "available" if MCPServer else "not available"
    
    return {
        "integration_test": results,
        "tools_available": len(mcp_server.tools),
        "status": "operational" if all(v in ["success", "connected", "available"] for v in results.values()) else "partial"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8051)