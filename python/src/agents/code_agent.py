"""
CodeAgent - Intelligent Code Generation Agent with Multi-LLM Support

This agent generates code across multiple programming languages and frameworks,
using context from Archon's knowledge base and supporting multiple LLM providers.
"""

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Optional

from pydantic import BaseModel, Field
from pydantic_ai import Agent, RunContext

from .base_agent import ArchonDependencies, BaseAgent, BaseAgentOutput
from .mcp_client import get_mcp_client

logger = logging.getLogger(__name__)


@dataclass
class CodeDependencies(ArchonDependencies):
    """Dependencies for code generation operations."""
    
    project_id: str = ""
    language: str = "python"  # Target programming language
    framework: str | None = None  # Optional framework specification
    context: dict[str, Any] | None = None  # Additional context for generation
    use_rag: bool = True  # Whether to use RAG for code examples
    progress_callback: Any | None = None


class CodeGenerationResult(BaseModel):
    """Result of code generation operation."""
    
    success: bool = Field(description="Whether code generation was successful")
    code: str = Field(description="Generated code")
    language: str = Field(description="Programming language used")
    explanation: str = Field(description="Explanation of the generated code")
    dependencies: list[str] = Field(default_factory=list, description="Required dependencies/imports")
    warnings: list[str] = Field(default_factory=list, description="Any warnings or caveats")
    suggestions: list[str] = Field(default_factory=list, description="Suggestions for improvement")
    examples_used: list[str] = Field(default_factory=list, description="Code examples referenced from RAG")


class CodeAgent(BaseAgent[CodeDependencies, CodeGenerationResult]):
    """
    Agent for intelligent code generation with multi-language support.
    
    This agent can:
    - Generate code in multiple programming languages
    - Use RAG to find relevant code examples
    - Integrate with project context
    - Support multiple LLM providers (OpenAI, Gemini, Claude, etc.)
    """
    
    def __init__(self, **kwargs):
        """Initialize the CodeAgent with configuration."""
        super().__init__(**kwargs)
        self.supported_languages = [
            "python", "javascript", "typescript", "java", "go", 
            "rust", "c++", "c#", "swift", "kotlin", "ruby", "php"
        ]
        self.mcp_client = None
        
    def _create_agent(self) -> Agent[CodeDependencies, CodeGenerationResult]:
        """Create the PydanticAI agent for code generation."""
        
        # Get model from environment or use default
        model_name = os.getenv("CODE_AGENT_MODEL", "openai:gpt-4o-mini")
        logger.info(f"Creating CodeAgent with model: {model_name}")
        
        # System prompt for code generation
        system_prompt = """You are an expert code generation assistant integrated with Archon.

Your responsibilities:
1. Generate clean, idiomatic, and well-documented code
2. Follow best practices and design patterns for the target language
3. Consider security implications and performance
4. Use project context and existing patterns when available
5. Provide clear explanations of the generated code

Guidelines:
- Write production-ready code with proper error handling
- Include necessary imports and dependencies
- Follow the project's coding style if context is available
- Add helpful comments for complex logic
- Suggest improvements and alternatives when relevant

When generating code:
- Be explicit about assumptions made
- Highlight any security considerations
- Note performance implications for large-scale usage
- Provide examples of how to use the generated code
- List required dependencies or libraries
"""
        
        return Agent(
            model_name,
            system_prompt=system_prompt,
            result_type=CodeGenerationResult,
            retries=3
        )
    
    async def _execute_with_context(
        self, 
        agent: Agent[CodeDependencies, CodeGenerationResult],
        prompt: str,
        deps: CodeDependencies
    ) -> CodeGenerationResult:
        """Execute code generation with full context."""
        
        # Initialize MCP client if needed
        if self.mcp_client is None and deps.use_rag:
            self.mcp_client = await get_mcp_client()
        
        # Gather context from RAG if enabled
        code_examples = []
        if deps.use_rag and self.mcp_client:
            try:
                # Search for relevant code examples
                logger.info(f"Searching for code examples related to: {prompt[:100]}...")
                
                examples_response = await self.mcp_client.call_tool(
                    "archon:search_code_examples",
                    {"query": prompt, "match_count": 3}
                )
                
                if examples_response and "results" in examples_response:
                    code_examples = examples_response["results"]
                    logger.info(f"Found {len(code_examples)} relevant code examples")
                    
            except Exception as e:
                logger.warning(f"Failed to fetch code examples: {e}")
        
        # Build enhanced prompt with context
        enhanced_prompt = self._build_enhanced_prompt(prompt, deps, code_examples)
        
        # Generate code using the agent
        try:
            result = await agent.run(enhanced_prompt, deps=deps)
            
            # Add examples used to the result
            if code_examples and hasattr(result.data, 'examples_used'):
                result.data.examples_used = [
                    ex.get("file_path", "Unknown") for ex in code_examples[:3]
                ]
            
            return result.data
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            return CodeGenerationResult(
                success=False,
                code="",
                language=deps.language,
                explanation=f"Failed to generate code: {str(e)}",
                warnings=[str(e)]
            )
    
    def _build_enhanced_prompt(
        self, 
        prompt: str, 
        deps: CodeDependencies,
        code_examples: list[dict]
    ) -> str:
        """Build an enhanced prompt with all available context."""
        
        parts = [f"Generate {deps.language} code for the following request:\n\n{prompt}"]
        
        # Add framework context if specified
        if deps.framework:
            parts.append(f"\nFramework: {deps.framework}")
        
        # Add project context if available
        if deps.context:
            parts.append(f"\nProject Context: {json.dumps(deps.context, indent=2)}")
        
        # Add relevant code examples from RAG
        if code_examples:
            parts.append("\n\nRelevant code examples from the knowledge base:")
            for i, example in enumerate(code_examples[:3], 1):
                parts.append(f"\n{i}. From {example.get('file_path', 'Unknown')}:")
                parts.append(f"```{example.get('language', deps.language)}")
                parts.append(example.get('code', '')[:500])  # Limit example length
                parts.append("```")
        
        # Add generation instructions
        parts.append("\n\nPlease generate code that:")
        parts.append("1. Solves the requested problem effectively")
        parts.append("2. Follows best practices for " + deps.language)
        parts.append("3. Includes proper error handling")
        parts.append("4. Is well-documented with comments")
        parts.append("5. Lists any required dependencies")
        
        return "\n".join(parts)
    
    async def generate_code(
        self,
        prompt: str,
        language: str = "python",
        framework: str | None = None,
        project_id: str | None = None,
        use_rag: bool = True,
        **kwargs
    ) -> CodeGenerationResult:
        """
        Generate code based on the prompt and parameters.
        
        Args:
            prompt: Description of what code to generate
            language: Target programming language
            framework: Optional framework to use
            project_id: Optional project context
            use_rag: Whether to use RAG for finding examples
            **kwargs: Additional context parameters
            
        Returns:
            CodeGenerationResult with generated code and metadata
        """
        
        # Validate language
        if language.lower() not in self.supported_languages:
            logger.warning(f"Unsupported language: {language}, defaulting to python")
            language = "python"
        
        # Create dependencies
        deps = CodeDependencies(
            project_id=project_id or "",
            language=language.lower(),
            framework=framework,
            context=kwargs,
            use_rag=use_rag
        )
        
        # Log the generation request
        logger.info(f"Generating {language} code for: {prompt[:100]}...")
        
        # Execute generation
        agent = self._create_agent()
        result = await self._execute_with_context(agent, prompt, deps)
        
        # Log result
        if result.success:
            logger.info(f"Successfully generated {len(result.code)} characters of {language} code")
        else:
            logger.error(f"Code generation failed: {result.explanation}")
        
        return result
    
    async def run(self, prompt: str, deps: CodeDependencies | None = None) -> BaseAgentOutput:
        """
        Main entry point for the agent.
        
        Args:
            prompt: The code generation request
            deps: Optional dependencies with context
            
        Returns:
            BaseAgentOutput with the generation result
        """
        
        if deps is None:
            deps = CodeDependencies()
        
        try:
            # Parse the prompt to extract parameters if structured
            params = self._parse_prompt(prompt)
            
            # Generate code
            result = await self.generate_code(
                prompt=params.get("request", prompt),
                language=params.get("language", deps.language),
                framework=params.get("framework", deps.framework),
                project_id=deps.project_id,
                use_rag=deps.use_rag
            )
            
            # Return structured output
            return BaseAgentOutput(
                success=result.success,
                message=result.explanation,
                data={
                    "code": result.code,
                    "language": result.language,
                    "dependencies": result.dependencies,
                    "warnings": result.warnings,
                    "suggestions": result.suggestions,
                    "examples_used": result.examples_used
                }
            )
            
        except Exception as e:
            logger.error(f"Error in CodeAgent.run: {e}", exc_info=True)
            return BaseAgentOutput(
                success=False,
                message=f"Code generation failed: {str(e)}",
                errors=[str(e)]
            )
    
    def _parse_prompt(self, prompt: str) -> dict:
        """
        Parse structured prompts to extract parameters.
        
        Supports formats like:
        - "Generate Python code for..."
        - "Create a React component that..."
        - "Write a Go function to..."
        """
        
        params = {"request": prompt}
        
        # Simple language detection from prompt
        language_keywords = {
            "python": ["python", "py"],
            "javascript": ["javascript", "js", "node"],
            "typescript": ["typescript", "ts"],
            "react": ["react", "jsx", "tsx"],
            "go": ["go", "golang"],
            "rust": ["rust"],
            "java": ["java"],
            "swift": ["swift", "ios"],
            "kotlin": ["kotlin", "android"]
        }
        
        prompt_lower = prompt.lower()
        for lang, keywords in language_keywords.items():
            if any(kw in prompt_lower for kw in keywords):
                if lang == "react":
                    params["language"] = "typescript"
                    params["framework"] = "react"
                else:
                    params["language"] = lang
                break
        
        return params


# Convenience function for direct usage
async def generate_code(
    prompt: str,
    language: str = "python",
    **kwargs
) -> CodeGenerationResult:
    """
    Convenience function to generate code without instantiating the agent.
    
    Args:
        prompt: Code generation request
        language: Target programming language
        **kwargs: Additional parameters
        
    Returns:
        CodeGenerationResult with generated code
    """
    agent = CodeAgent()
    return await agent.generate_code(prompt, language, **kwargs)