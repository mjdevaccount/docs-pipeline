"""
Prompt Pipeline Interfaces
===========================
Abstract interfaces for prompt-driven document generation.
"""
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, Any, List
from .models import PromptConfig, AgentResult, DocumentContext


class IPromptLibrary(ABC):
    """Interface for loading and managing prompt templates"""
    
    @abstractmethod
    def load_prompt(self, category: str, name: str) -> str:
        """Load a prompt template by category and name"""
        pass
    
    @abstractmethod
    def list_prompts(self, category: Optional[str] = None) -> List[str]:
        """List available prompts, optionally filtered by category"""
        pass


class IDocumentAgent(ABC):
    """Interface for document processing agents"""
    
    @abstractmethod
    async def process(self, context: DocumentContext) -> AgentResult:
        """
        Process a document and return the result.
        
        Args:
            context: Current document context (content, metadata, history)
            
        Returns:
            AgentResult with processed content and metadata
        """
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Agent name for logging and tracking"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """Agent description for documentation"""
        pass


class IPromptExecutor(ABC):
    """Interface for executing prompts against an LLM"""
    
    @abstractmethod
    async def execute(
        self,
        prompt: str,
        context: Dict[str, Any],
        model: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """
        Execute a prompt with the given context.
        
        Args:
            prompt: The prompt template
            context: Variables to inject into the prompt
            model: Optional model override
            temperature: Sampling temperature
            
        Returns:
            LLM response as string
        """
        pass


class IAgentOrchestrator(ABC):
    """Interface for orchestrating multiple agents in sequence"""
    
    @abstractmethod
    async def run_pipeline(
        self,
        input_file: Path,
        output_file: Path,
        config: PromptConfig
    ) -> bool:
        """
        Run a complete agent pipeline.
        
        Args:
            input_file: Path to input markdown file (rough draft)
            output_file: Path to output markdown file (structured)
            config: Pipeline configuration
            
        Returns:
            True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def add_agent(self, agent: IDocumentAgent) -> None:
        """Add an agent to the pipeline"""
        pass

