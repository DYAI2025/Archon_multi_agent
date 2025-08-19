"""
Agent Orchestrator - Central coordination for multi-agent AI systems

This orchestrator manages multiple AI agents from different providers,
enabling seamless collaboration between Claude, GPT-4, Gemini, Grok, and others.
"""

import asyncio
import json
import logging
import time
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Callable
from datetime import datetime

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Status of an agent in the orchestrator."""
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"
    INITIALIZING = "initializing"


class TaskPriority(Enum):
    """Priority levels for tasks."""
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4


class TaskStatus(Enum):
    """Status of a task in the queue."""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


@dataclass
class AgentInfo:
    """Information about a registered agent."""
    id: str
    name: str
    provider: str  # openai, anthropic, google, xai, etc.
    capabilities: List[str]
    status: AgentStatus = AgentStatus.IDLE
    current_task: Optional[str] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    average_response_time: float = 0.0
    last_active: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Task:
    """Represents a task to be executed by an agent."""
    id: str
    type: str  # code_generation, documentation, analysis, etc.
    prompt: str
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.PENDING
    assigned_agent: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[Any] = None
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)  # Task IDs this depends on
    retry_count: int = 0
    max_retries: int = 3


class TaskResult(BaseModel):
    """Result from task execution."""
    task_id: str
    agent_id: str
    success: bool
    result: Any
    execution_time: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class AgentOrchestrator:
    """
    Central orchestrator for managing multiple AI agents.
    
    Features:
    - Dynamic agent registration and discovery
    - Intelligent task routing based on capabilities
    - Load balancing across agents
    - Failure handling and retry logic
    - Performance monitoring
    - Task dependency management
    """
    
    def __init__(self, max_concurrent_tasks: int = 10):
        """Initialize the orchestrator."""
        self.agents: Dict[str, AgentInfo] = {}
        self.tasks: Dict[str, Task] = {}
        self.task_queue: asyncio.Queue = asyncio.Queue()
        self.max_concurrent_tasks = max_concurrent_tasks
        self.active_tasks = 0
        self.task_history: List[Task] = []
        self.performance_metrics: Dict[str, Any] = defaultdict(lambda: {
            "total_tasks": 0,
            "successful_tasks": 0,
            "failed_tasks": 0,
            "total_time": 0.0,
            "average_time": 0.0
        })
        self.agent_adapters: Dict[str, Any] = {}
        self.running = False
        self.workers: List[asyncio.Task] = []
        
        logger.info("AgentOrchestrator initialized")
    
    def register_agent(
        self,
        agent_id: str,
        name: str,
        provider: str,
        capabilities: List[str],
        adapter: Any = None,
        metadata: Dict[str, Any] = None
    ) -> AgentInfo:
        """
        Register a new agent with the orchestrator.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name
            provider: Provider type (openai, anthropic, etc.)
            capabilities: List of capabilities (code, documentation, etc.)
            adapter: Optional adapter instance for the agent
            metadata: Additional metadata
            
        Returns:
            AgentInfo object for the registered agent
        """
        if agent_id in self.agents:
            logger.warning(f"Agent {agent_id} already registered, updating...")
        
        agent = AgentInfo(
            id=agent_id,
            name=name,
            provider=provider,
            capabilities=capabilities,
            metadata=metadata or {}
        )
        
        self.agents[agent_id] = agent
        
        if adapter:
            self.agent_adapters[agent_id] = adapter
        
        logger.info(f"Registered agent: {name} ({provider}) with capabilities: {capabilities}")
        return agent
    
    def unregister_agent(self, agent_id: str) -> bool:
        """
        Unregister an agent from the orchestrator.
        
        Args:
            agent_id: ID of the agent to unregister
            
        Returns:
            True if successful, False otherwise
        """
        if agent_id in self.agents:
            # Cancel any assigned tasks
            for task_id, task in self.tasks.items():
                if task.assigned_agent == agent_id and task.status in [TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS]:
                    task.status = TaskStatus.PENDING
                    task.assigned_agent = None
                    asyncio.create_task(self.task_queue.put(task))
            
            del self.agents[agent_id]
            if agent_id in self.agent_adapters:
                del self.agent_adapters[agent_id]
            
            logger.info(f"Unregistered agent: {agent_id}")
            return True
        
        return False
    
    async def submit_task(
        self,
        task_type: str,
        prompt: str,
        priority: TaskPriority = TaskPriority.MEDIUM,
        dependencies: List[str] = None,
        metadata: Dict[str, Any] = None
    ) -> str:
        """
        Submit a new task to the orchestrator.
        
        Args:
            task_type: Type of task (code_generation, documentation, etc.)
            prompt: The task prompt
            priority: Task priority
            dependencies: List of task IDs this depends on
            metadata: Additional metadata
            
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        task = Task(
            id=task_id,
            type=task_type,
            prompt=prompt,
            priority=priority,
            dependencies=dependencies or [],
            metadata=metadata or {}
        )
        
        self.tasks[task_id] = task
        
        # Check if dependencies are met
        if not self._are_dependencies_met(task):
            logger.info(f"Task {task_id} waiting for dependencies: {task.dependencies}")
        else:
            await self.task_queue.put(task)
            logger.info(f"Task {task_id} submitted to queue")
        
        return task_id
    
    def _are_dependencies_met(self, task: Task) -> bool:
        """Check if all task dependencies are completed."""
        for dep_id in task.dependencies:
            if dep_id not in self.tasks:
                return False
            dep_task = self.tasks[dep_id]
            if dep_task.status != TaskStatus.COMPLETED:
                return False
        return True
    
    async def _check_dependencies(self):
        """Periodically check for tasks with met dependencies."""
        while self.running:
            for task_id, task in list(self.tasks.items()):
                if (task.status == TaskStatus.PENDING and 
                    task.dependencies and 
                    self._are_dependencies_met(task)):
                    await self.task_queue.put(task)
                    logger.info(f"Task {task_id} dependencies met, added to queue")
            
            await asyncio.sleep(1)  # Check every second
    
    def _select_agent_for_task(self, task: Task) -> Optional[str]:
        """
        Select the best available agent for a task.
        
        Uses a scoring system based on:
        - Agent capabilities matching task type
        - Agent availability
        - Agent performance history
        - Load balancing
        
        Args:
            task: The task to assign
            
        Returns:
            Agent ID or None if no suitable agent
        """
        candidates = []
        
        for agent_id, agent in self.agents.items():
            # Skip unavailable agents
            if agent.status != AgentStatus.IDLE:
                continue
            
            # Check if agent has required capability
            if task.type not in agent.capabilities and "general" not in agent.capabilities:
                continue
            
            # Calculate score
            score = 0
            
            # Capability match
            if task.type in agent.capabilities:
                score += 10
            elif "general" in agent.capabilities:
                score += 5
            
            # Performance history
            if agent.tasks_completed > 0:
                success_rate = agent.tasks_completed / (agent.tasks_completed + agent.tasks_failed)
                score += success_rate * 5
            
            # Response time (prefer faster agents)
            if agent.average_response_time > 0:
                score += (1 / agent.average_response_time) * 2
            
            # Load balancing (prefer less used agents)
            score -= agent.tasks_completed * 0.1
            
            candidates.append((agent_id, score))
        
        if not candidates:
            return None
        
        # Sort by score and select the best
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0][0]
    
    async def _execute_task(self, task: Task, agent_id: str) -> TaskResult:
        """
        Execute a task using the specified agent.
        
        Args:
            task: The task to execute
            agent_id: The agent to use
            
        Returns:
            TaskResult object
        """
        agent = self.agents[agent_id]
        adapter = self.agent_adapters.get(agent_id)
        
        if not adapter:
            raise ValueError(f"No adapter found for agent {agent_id}")
        
        # Update agent and task status
        agent.status = AgentStatus.BUSY
        agent.current_task = task.id
        task.status = TaskStatus.IN_PROGRESS
        task.assigned_agent = agent_id
        task.started_at = datetime.now()
        
        start_time = time.time()
        
        try:
            # Execute task through adapter
            result = await adapter.execute(task.prompt, task.metadata)
            
            execution_time = time.time() - start_time
            
            # Update task
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            
            # Update agent metrics
            agent.tasks_completed += 1
            agent.average_response_time = (
                (agent.average_response_time * (agent.tasks_completed - 1) + execution_time) /
                agent.tasks_completed
            )
            
            # Update global metrics
            self._update_metrics(agent.provider, True, execution_time)
            
            logger.info(f"Task {task.id} completed by {agent.name} in {execution_time:.2f}s")
            
            return TaskResult(
                task_id=task.id,
                agent_id=agent_id,
                success=True,
                result=result,
                execution_time=execution_time
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            
            # Update task
            task.status = TaskStatus.FAILED
            task.error = str(e)
            task.completed_at = datetime.now()
            
            # Update agent metrics
            agent.tasks_failed += 1
            
            # Update global metrics
            self._update_metrics(agent.provider, False, execution_time)
            
            logger.error(f"Task {task.id} failed: {e}")
            
            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.status = TaskStatus.PENDING
                task.assigned_agent = None
                await self.task_queue.put(task)
                logger.info(f"Retrying task {task.id} (attempt {task.retry_count}/{task.max_retries})")
            
            return TaskResult(
                task_id=task.id,
                agent_id=agent_id,
                success=False,
                result={"error": str(e)},
                execution_time=execution_time
            )
            
        finally:
            # Reset agent status
            agent.status = AgentStatus.IDLE
            agent.current_task = None
            agent.last_active = datetime.now()
    
    def _update_metrics(self, provider: str, success: bool, execution_time: float):
        """Update performance metrics."""
        metrics = self.performance_metrics[provider]
        metrics["total_tasks"] += 1
        if success:
            metrics["successful_tasks"] += 1
        else:
            metrics["failed_tasks"] += 1
        metrics["total_time"] += execution_time
        metrics["average_time"] = metrics["total_time"] / metrics["total_tasks"]
    
    async def _worker(self):
        """Worker coroutine for processing tasks."""
        while self.running:
            try:
                # Get task from queue with timeout
                task = await asyncio.wait_for(self.task_queue.get(), timeout=1.0)
                
                # Select agent for task
                agent_id = self._select_agent_for_task(task)
                
                if not agent_id:
                    # No suitable agent, put task back in queue
                    await self.task_queue.put(task)
                    await asyncio.sleep(1)  # Wait before retry
                    continue
                
                # Execute task
                self.active_tasks += 1
                try:
                    result = await self._execute_task(task, agent_id)
                    
                    # Check for dependent tasks
                    for other_task_id, other_task in self.tasks.items():
                        if task.id in other_task.dependencies:
                            if self._are_dependencies_met(other_task):
                                await self.task_queue.put(other_task)
                                
                finally:
                    self.active_tasks -= 1
                    
            except asyncio.TimeoutError:
                continue  # No tasks in queue
            except Exception as e:
                logger.error(f"Worker error: {e}", exc_info=True)
    
    async def start(self):
        """Start the orchestrator."""
        if self.running:
            logger.warning("Orchestrator already running")
            return
        
        self.running = True
        
        # Start workers
        for i in range(self.max_concurrent_tasks):
            worker = asyncio.create_task(self._worker())
            self.workers.append(worker)
        
        # Start dependency checker
        asyncio.create_task(self._check_dependencies())
        
        logger.info(f"Orchestrator started with {self.max_concurrent_tasks} workers")
    
    async def stop(self):
        """Stop the orchestrator."""
        self.running = False
        
        # Wait for workers to finish
        await asyncio.gather(*self.workers, return_exceptions=True)
        self.workers.clear()
        
        logger.info("Orchestrator stopped")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current orchestrator status."""
        return {
            "running": self.running,
            "agents": {
                agent_id: {
                    "name": agent.name,
                    "provider": agent.provider,
                    "status": agent.status.value,
                    "current_task": agent.current_task,
                    "tasks_completed": agent.tasks_completed,
                    "tasks_failed": agent.tasks_failed,
                    "average_response_time": agent.average_response_time
                }
                for agent_id, agent in self.agents.items()
            },
            "tasks": {
                "total": len(self.tasks),
                "pending": sum(1 for t in self.tasks.values() if t.status == TaskStatus.PENDING),
                "in_progress": sum(1 for t in self.tasks.values() if t.status == TaskStatus.IN_PROGRESS),
                "completed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.COMPLETED),
                "failed": sum(1 for t in self.tasks.values() if t.status == TaskStatus.FAILED)
            },
            "queue_size": self.task_queue.qsize(),
            "active_tasks": self.active_tasks,
            "performance_metrics": dict(self.performance_metrics)
        }
    
    def get_task_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a specific task."""
        if task_id not in self.tasks:
            return None
        
        task = self.tasks[task_id]
        return {
            "id": task.id,
            "type": task.type,
            "status": task.status.value,
            "priority": task.priority.value,
            "assigned_agent": task.assigned_agent,
            "created_at": task.created_at.isoformat() if task.created_at else None,
            "started_at": task.started_at.isoformat() if task.started_at else None,
            "completed_at": task.completed_at.isoformat() if task.completed_at else None,
            "result": task.result,
            "error": task.error,
            "retry_count": task.retry_count
        }