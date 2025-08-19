"""
Orchestrator API Service

FastAPI service for the Multi-Agent Orchestrator.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .orchestrator import AgentOrchestrator, TaskPriority, AgentStatus
from .adapters import create_adapter

logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Archon Multi-Agent Orchestrator",
    description="Orchestration service for multiple AI agents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global orchestrator instance
orchestrator: Optional[AgentOrchestrator] = None


# Request/Response models
class AgentRegistration(BaseModel):
    """Model for agent registration."""
    agent_id: str
    name: str
    provider: str
    capabilities: List[str]
    api_key: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class TaskSubmission(BaseModel):
    """Model for task submission."""
    task_type: str
    prompt: str
    priority: str = "medium"  # low, medium, high, critical
    dependencies: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None


class TaskResponse(BaseModel):
    """Response for task submission."""
    task_id: str
    status: str
    message: str


# API Endpoints
@app.on_event("startup")
async def startup_event():
    """Initialize the orchestrator on startup."""
    global orchestrator
    
    orchestrator = AgentOrchestrator(max_concurrent_tasks=10)
    await orchestrator.start()
    
    # Auto-register available agents based on environment
    await auto_register_agents()
    
    logger.info("Orchestrator API started")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown."""
    if orchestrator:
        await orchestrator.stop()
    logger.info("Orchestrator API stopped")


async def auto_register_agents():
    """Automatically register agents based on available API keys."""
    import os
    
    # Claude Flow (always available via MCP)
    try:
        adapter = create_adapter("claude_flow")
        if await adapter.initialize():
            orchestrator.register_agent(
                agent_id="claude_flow_hive",
                name="Claude Flow Hive Mind",
                provider="claude_flow",
                capabilities=["general", "code_generation", "documentation", "analysis"],
                adapter=adapter
            )
            logger.info("Registered Claude Flow Hive Mind")
    except Exception as e:
        logger.warning(f"Could not register Claude Flow: {e}")
    
    # OpenAI GPT
    if os.getenv("OPENAI_API_KEY"):
        try:
            adapter = create_adapter("gpt", api_key=os.getenv("OPENAI_API_KEY"))
            if await adapter.initialize():
                orchestrator.register_agent(
                    agent_id="gpt4_primary",
                    name="GPT-4 Primary",
                    provider="openai",
                    capabilities=["code_generation", "documentation", "analysis"],
                    adapter=adapter
                )
                logger.info("Registered GPT-4 Primary")
        except Exception as e:
            logger.warning(f"Could not register GPT-4: {e}")
    
    # Google Gemini
    if os.getenv("GOOGLE_API_KEY"):
        try:
            adapter = create_adapter("gemini", api_key=os.getenv("GOOGLE_API_KEY"))
            if await adapter.initialize():
                orchestrator.register_agent(
                    agent_id="gemini_pro",
                    name="Gemini Pro",
                    provider="google",
                    capabilities=["analysis", "documentation", "general"],
                    adapter=adapter
                )
                logger.info("Registered Gemini Pro")
        except Exception as e:
            logger.warning(f"Could not register Gemini: {e}")
    
    # Anthropic Claude
    if os.getenv("ANTHROPIC_API_KEY"):
        try:
            adapter = create_adapter("anthropic", api_key=os.getenv("ANTHROPIC_API_KEY"))
            if await adapter.initialize():
                orchestrator.register_agent(
                    agent_id="claude3_opus",
                    name="Claude 3 Opus",
                    provider="anthropic",
                    capabilities=["code_generation", "analysis", "documentation"],
                    adapter=adapter
                )
                logger.info("Registered Claude 3 Opus")
        except Exception as e:
            logger.warning(f"Could not register Claude: {e}")
    
    # X.AI Grok
    if os.getenv("XAI_API_KEY"):
        try:
            adapter = create_adapter("grok", api_key=os.getenv("XAI_API_KEY"))
            if await adapter.initialize():
                orchestrator.register_agent(
                    agent_id="grok_beta",
                    name="Grok Beta",
                    provider="xai",
                    capabilities=["analysis", "general"],
                    adapter=adapter
                )
                logger.info("Registered Grok Beta")
        except Exception as e:
            logger.warning(f"Could not register Grok: {e}")


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    if not orchestrator:
        return {"status": "unhealthy", "reason": "Orchestrator not initialized"}
    
    status = orchestrator.get_status()
    return {
        "status": "healthy",
        "orchestrator": {
            "running": status["running"],
            "agents_count": len(status["agents"]),
            "tasks_count": status["tasks"]["total"],
            "queue_size": status["queue_size"]
        }
    }


@app.post("/agents/register")
async def register_agent(registration: AgentRegistration):
    """Register a new agent with the orchestrator."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        # Create adapter for the agent
        adapter = create_adapter(
            registration.provider,
            api_key=registration.api_key
        )
        
        # Initialize adapter
        if not await adapter.initialize():
            raise ValueError(f"Failed to initialize {registration.provider} adapter")
        
        # Register with orchestrator
        agent = orchestrator.register_agent(
            agent_id=registration.agent_id,
            name=registration.name,
            provider=registration.provider,
            capabilities=registration.capabilities,
            adapter=adapter,
            metadata=registration.metadata
        )
        
        return {
            "success": True,
            "agent_id": agent.id,
            "message": f"Agent {agent.name} registered successfully"
        }
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.delete("/agents/{agent_id}")
async def unregister_agent(agent_id: str):
    """Unregister an agent from the orchestrator."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    if orchestrator.unregister_agent(agent_id):
        return {"success": True, "message": f"Agent {agent_id} unregistered"}
    else:
        raise HTTPException(status_code=404, detail=f"Agent {agent_id} not found")


@app.get("/agents")
async def list_agents():
    """List all registered agents."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    status = orchestrator.get_status()
    return {"agents": status["agents"]}


@app.post("/tasks/submit")
async def submit_task(submission: TaskSubmission):
    """Submit a new task to the orchestrator."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    try:
        # Convert priority string to enum
        priority_map = {
            "low": TaskPriority.LOW,
            "medium": TaskPriority.MEDIUM,
            "high": TaskPriority.HIGH,
            "critical": TaskPriority.CRITICAL
        }
        priority = priority_map.get(submission.priority.lower(), TaskPriority.MEDIUM)
        
        # Submit task
        task_id = await orchestrator.submit_task(
            task_type=submission.task_type,
            prompt=submission.prompt,
            priority=priority,
            dependencies=submission.dependencies,
            metadata=submission.metadata
        )
        
        return TaskResponse(
            task_id=task_id,
            status="submitted",
            message=f"Task {task_id} submitted successfully"
        )
        
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.get("/tasks/{task_id}")
async def get_task_status(task_id: str):
    """Get the status of a specific task."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    status = orchestrator.get_task_status(task_id)
    
    if status:
        return status
    else:
        raise HTTPException(status_code=404, detail=f"Task {task_id} not found")


@app.get("/tasks")
async def list_tasks():
    """List all tasks in the system."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    status = orchestrator.get_status()
    return {"tasks": status["tasks"]}


@app.get("/status")
async def get_orchestrator_status():
    """Get the complete status of the orchestrator."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    return orchestrator.get_status()


@app.get("/metrics")
async def get_metrics():
    """Get performance metrics."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    status = orchestrator.get_status()
    return {"metrics": status["performance_metrics"]}


@app.post("/test")
async def test_orchestration():
    """Test endpoint to demonstrate multi-agent orchestration."""
    if not orchestrator:
        raise HTTPException(status_code=503, detail="Orchestrator not initialized")
    
    # Submit a test task
    task_id = await orchestrator.submit_task(
        task_type="code_generation",
        prompt="Generate a Python function that calculates the Fibonacci sequence",
        priority=TaskPriority.MEDIUM,
        metadata={"test": True}
    )
    
    # Wait a bit for processing
    await asyncio.sleep(2)
    
    # Get task status
    status = orchestrator.get_task_status(task_id)
    
    return {
        "message": "Test orchestration initiated",
        "task_id": task_id,
        "task_status": status
    }


# WebSocket endpoint for real-time updates (optional)
from fastapi import WebSocket, WebSocketDisconnect
from typing import Set

connected_clients: Set[WebSocket] = set()


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time orchestrator updates."""
    await websocket.accept()
    connected_clients.add(websocket)
    
    try:
        while True:
            # Send periodic status updates
            if orchestrator:
                status = orchestrator.get_status()
                await websocket.send_json(status)
            
            await asyncio.sleep(1)  # Update every second
            
    except WebSocketDisconnect:
        connected_clients.remove(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        if websocket in connected_clients:
            connected_clients.remove(websocket)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8053)