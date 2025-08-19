"""
AI Provider Adapters for Multi-Agent Orchestration

This module contains adapters for different AI providers to enable
seamless integration with the orchestrator.
"""

import asyncio
import json
import logging
import os
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

import httpx
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class BaseAdapter(ABC):
    """Base class for all AI provider adapters."""
    
    def __init__(self, api_key: Optional[str] = None, **kwargs):
        """Initialize the adapter."""
        self.api_key = api_key
        self.config = kwargs
        self.client = None
        
    @abstractmethod
    async def initialize(self):
        """Initialize the adapter connection."""
        pass
    
    @abstractmethod
    async def execute(self, prompt: str, metadata: Dict[str, Any] = None) -> Any:
        """Execute a prompt and return the result."""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the adapter is healthy and can accept requests."""
        pass


class ClaudeFlowAdapter(BaseAdapter):
    """
    Adapter for Claude Flow integration via MCP.
    
    This adapter connects to Claude Flow's hive-mind system
    and can spawn sub-agents for parallel task execution.
    """
    
    def __init__(self, mcp_endpoint: str = "http://localhost:8051", **kwargs):
        """Initialize Claude Flow adapter."""
        super().__init__(**kwargs)
        self.mcp_endpoint = mcp_endpoint
        self.session_id = None
        self.swarm_id = None
        
    async def initialize(self):
        """Initialize connection to Claude Flow MCP server."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.mcp_endpoint}/health")
                if response.status_code == 200:
                    logger.info("Claude Flow MCP server is healthy")
                    return True
        except Exception as e:
            logger.error(f"Failed to connect to Claude Flow MCP: {e}")
            return False
    
    async def spawn_swarm(self, objective: str, max_workers: int = 4) -> Dict[str, Any]:
        """Spawn a Claude Flow hive-mind swarm."""
        try:
            async with httpx.AsyncClient() as client:
                payload = {
                    "tool": "hive_mind_spawn",
                    "arguments": {
                        "objective": objective,
                        "queen_type": "strategic",
                        "max_workers": max_workers,
                        "consensus": "majority"
                    }
                }
                
                response = await client.post(
                    f"{self.mcp_endpoint}/tools/hive_mind_spawn",
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    self.swarm_id = result.get("swarm_id")
                    self.session_id = result.get("session_id")
                    logger.info(f"Spawned Claude Flow swarm: {self.swarm_id}")
                    return result
                    
        except Exception as e:
            logger.error(f"Failed to spawn Claude Flow swarm: {e}")
            return {"error": str(e)}
    
    async def execute(self, prompt: str, metadata: Dict[str, Any] = None) -> Any:
        """Execute a task using Claude Flow."""
        try:
            # If no swarm exists, create one
            if not self.swarm_id:
                await self.spawn_swarm(prompt[:100])  # Use first 100 chars as objective
            
            async with httpx.AsyncClient() as client:
                payload = {
                    "tool": "archon:manage_task",
                    "arguments": {
                        "action": "create",
                        "title": prompt[:100],
                        "description": prompt,
                        "metadata": metadata or {}
                    }
                }
                
                response = await client.post(
                    f"{self.mcp_endpoint}/tools/archon:manage_task",
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    return response.json()
                else:
                    return {"error": f"MCP returned {response.status_code}"}
                    
        except Exception as e:
            logger.error(f"Claude Flow execution error: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> bool:
        """Check Claude Flow MCP health."""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(f"{self.mcp_endpoint}/health", timeout=5.0)
                return response.status_code == 200
        except:
            return False


class GPTAdapter(BaseAdapter):
    """
    Adapter for OpenAI GPT models.
    
    Supports GPT-4, GPT-4o, GPT-3.5-turbo and other OpenAI models.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4o", **kwargs):
        """Initialize GPT adapter."""
        super().__init__(api_key or os.getenv("OPENAI_API_KEY"), **kwargs)
        self.model = model
        self.base_url = "https://api.openai.com/v1"
        
    async def initialize(self):
        """Initialize OpenAI client."""
        if not self.api_key:
            logger.error("OpenAI API key not provided")
            return False
        
        try:
            # Test the API key
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                if response.status_code == 200:
                    logger.info("OpenAI API key validated")
                    return True
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI: {e}")
        
        return False
    
    async def execute(self, prompt: str, metadata: Dict[str, Any] = None) -> Any:
        """Execute a prompt using OpenAI GPT."""
        try:
            async with httpx.AsyncClient() as client:
                # Prepare the request
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": metadata.get("system_prompt", "You are a helpful assistant.") if metadata else "You are a helpful assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": metadata.get("temperature", 0.7) if metadata else 0.7,
                    "max_tokens": metadata.get("max_tokens", 2000) if metadata else 2000
                }
                
                # Add any additional parameters from metadata
                if metadata:
                    for key in ["top_p", "frequency_penalty", "presence_penalty", "stop"]:
                        if key in metadata:
                            payload[key] = metadata[key]
                
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "content": result["choices"][0]["message"]["content"],
                        "usage": result.get("usage"),
                        "model": result.get("model")
                    }
                else:
                    return {"error": f"OpenAI API error: {response.status_code} - {response.text}"}
                    
        except Exception as e:
            logger.error(f"GPT execution error: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> bool:
        """Check OpenAI API health."""
        if not self.api_key:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=5.0
                )
                return response.status_code == 200
        except:
            return False


class GeminiAdapter(BaseAdapter):
    """
    Adapter for Google Gemini models.
    
    Supports Gemini Pro, Gemini 1.5 Pro, and other Google AI models.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gemini-pro", **kwargs):
        """Initialize Gemini adapter."""
        super().__init__(api_key or os.getenv("GOOGLE_API_KEY"), **kwargs)
        self.model = model
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        
    async def initialize(self):
        """Initialize Google Gemini client."""
        if not self.api_key:
            logger.error("Google API key not provided")
            return False
        
        try:
            # Test the API key
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/models?key={self.api_key}"
                )
                if response.status_code == 200:
                    logger.info("Google API key validated")
                    return True
        except Exception as e:
            logger.error(f"Failed to initialize Gemini: {e}")
        
        return False
    
    async def execute(self, prompt: str, metadata: Dict[str, Any] = None) -> Any:
        """Execute a prompt using Google Gemini."""
        try:
            async with httpx.AsyncClient() as client:
                # Prepare the request
                payload = {
                    "contents": [{
                        "parts": [{
                            "text": prompt
                        }]
                    }],
                    "generationConfig": {
                        "temperature": metadata.get("temperature", 0.7) if metadata else 0.7,
                        "maxOutputTokens": metadata.get("max_tokens", 2000) if metadata else 2000,
                        "topP": metadata.get("top_p", 0.95) if metadata else 0.95,
                        "topK": metadata.get("top_k", 40) if metadata else 40
                    }
                }
                
                # Add system instruction if provided
                if metadata and "system_prompt" in metadata:
                    payload["systemInstruction"] = {
                        "parts": [{"text": metadata["system_prompt"]}]
                    }
                
                response = await client.post(
                    f"{self.base_url}/models/{self.model}:generateContent?key={self.api_key}",
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "content": result["candidates"][0]["content"]["parts"][0]["text"],
                        "safety_ratings": result["candidates"][0].get("safetyRatings"),
                        "model": self.model
                    }
                else:
                    return {"error": f"Gemini API error: {response.status_code} - {response.text}"}
                    
        except Exception as e:
            logger.error(f"Gemini execution error: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> bool:
        """Check Google API health."""
        if not self.api_key:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/models?key={self.api_key}",
                    timeout=5.0
                )
                return response.status_code == 200
        except:
            return False


class GrokAdapter(BaseAdapter):
    """
    Adapter for X.AI Grok models.
    
    Supports Grok-beta and future Grok models.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "grok-beta", **kwargs):
        """Initialize Grok adapter."""
        super().__init__(api_key or os.getenv("XAI_API_KEY"), **kwargs)
        self.model = model
        self.base_url = "https://api.x.ai/v1"  # X.AI API endpoint
        
    async def initialize(self):
        """Initialize X.AI Grok client."""
        if not self.api_key:
            logger.error("X.AI API key not provided")
            return False
        
        try:
            # Test the API key
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                if response.status_code == 200:
                    logger.info("X.AI API key validated")
                    return True
        except Exception as e:
            logger.error(f"Failed to initialize Grok: {e}")
        
        return False
    
    async def execute(self, prompt: str, metadata: Dict[str, Any] = None) -> Any:
        """Execute a prompt using X.AI Grok."""
        try:
            async with httpx.AsyncClient() as client:
                # Grok uses OpenAI-compatible API format
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": metadata.get("system_prompt", "You are Grok, a helpful AI assistant.") if metadata else "You are Grok, a helpful AI assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": metadata.get("temperature", 0.7) if metadata else 0.7,
                    "max_tokens": metadata.get("max_tokens", 2000) if metadata else 2000
                }
                
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "content": result["choices"][0]["message"]["content"],
                        "usage": result.get("usage"),
                        "model": result.get("model")
                    }
                else:
                    return {"error": f"Grok API error: {response.status_code} - {response.text}"}
                    
        except Exception as e:
            logger.error(f"Grok execution error: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> bool:
        """Check X.AI API health."""
        if not self.api_key:
            return False
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/models",
                    headers={"Authorization": f"Bearer {self.api_key}"},
                    timeout=5.0
                )
                return response.status_code == 200
        except:
            return False


class AnthropicAdapter(BaseAdapter):
    """
    Adapter for Anthropic Claude models.
    
    Supports Claude 3 Opus, Sonnet, Haiku and other Anthropic models.
    """
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-opus-20240229", **kwargs):
        """Initialize Anthropic adapter."""
        super().__init__(api_key or os.getenv("ANTHROPIC_API_KEY"), **kwargs)
        self.model = model
        self.base_url = "https://api.anthropic.com/v1"
        
    async def initialize(self):
        """Initialize Anthropic client."""
        if not self.api_key:
            logger.error("Anthropic API key not provided")
            return False
        
        logger.info("Anthropic adapter initialized")
        return True
    
    async def execute(self, prompt: str, metadata: Dict[str, Any] = None) -> Any:
        """Execute a prompt using Anthropic Claude."""
        try:
            async with httpx.AsyncClient() as client:
                # Prepare the request
                payload = {
                    "model": self.model,
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "max_tokens": metadata.get("max_tokens", 2000) if metadata else 2000,
                    "temperature": metadata.get("temperature", 0.7) if metadata else 0.7
                }
                
                # Add system prompt if provided
                if metadata and "system_prompt" in metadata:
                    payload["system"] = metadata["system_prompt"]
                
                response = await client.post(
                    f"{self.base_url}/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": "2023-06-01",
                        "Content-Type": "application/json"
                    },
                    json=payload,
                    timeout=60.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return {
                        "content": result["content"][0]["text"],
                        "usage": result.get("usage"),
                        "model": result.get("model"),
                        "stop_reason": result.get("stop_reason")
                    }
                else:
                    return {"error": f"Anthropic API error: {response.status_code} - {response.text}"}
                    
        except Exception as e:
            logger.error(f"Anthropic execution error: {e}")
            return {"error": str(e)}
    
    async def health_check(self) -> bool:
        """Check Anthropic API health."""
        return bool(self.api_key)  # Simple check for now


# Factory function for creating adapters
def create_adapter(provider: str, **kwargs) -> BaseAdapter:
    """
    Factory function to create the appropriate adapter.
    
    Args:
        provider: Provider name (claude_flow, gpt, gemini, grok, anthropic)
        **kwargs: Additional configuration for the adapter
        
    Returns:
        Adapter instance
    """
    adapters = {
        "claude_flow": ClaudeFlowAdapter,
        "gpt": GPTAdapter,
        "openai": GPTAdapter,
        "gemini": GeminiAdapter,
        "google": GeminiAdapter,
        "grok": GrokAdapter,
        "xai": GrokAdapter,
        "anthropic": AnthropicAdapter,
        "claude": AnthropicAdapter
    }
    
    adapter_class = adapters.get(provider.lower())
    
    if not adapter_class:
        raise ValueError(f"Unknown provider: {provider}")
    
    return adapter_class(**kwargs)