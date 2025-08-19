"""
Multi-Agent Orchestrator for Archon

This module provides orchestration capabilities for multiple AI agents
from different providers (OpenAI, Anthropic, Google, X.AI, etc.)
"""

from .orchestrator import AgentOrchestrator
from .adapters import (
    ClaudeFlowAdapter,
    GPTAdapter, 
    GeminiAdapter,
    GrokAdapter
)

__all__ = [
    "AgentOrchestrator",
    "ClaudeFlowAdapter",
    "GPTAdapter",
    "GeminiAdapter",
    "GrokAdapter"
]