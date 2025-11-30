"""
Base Document Agent
===================
Abstract base class for all document processing agents.
"""
from abc import abstractmethod
from pathlib import Path
from typing import Optional
from ..core.interfaces import IDocumentAgent, IPromptExecutor, IPromptLibrary
from ..core.models import DocumentContext, AgentResult
from ..core.exceptions import AgentExecutionError


class BaseDocumentAgent(IDocumentAgent):
    """
    Base implementation for document agents.
    Provides common functionality for loading prompts and executing them.
    """
    
    def __init__(
        self,
        prompt_library: IPromptLibrary,
        prompt_executor: IPromptExecutor,
        prompt_category: str,
        prompt_name: str,
        model: Optional[str] = None,
        temperature: float = 0.7
    ):
        self._prompt_library = prompt_library
        self._prompt_executor = prompt_executor
        self._prompt_category = prompt_category
        self._prompt_name = prompt_name
        self._model = model
        self._temperature = temperature
    
    async def process(self, context: DocumentContext) -> AgentResult:
        """
        Process a document using the agent's prompt.
        
        Template method pattern: subclasses override prepare_context() and parse_result().
        """
        try:
            # Load prompt template
            prompt_template = self._prompt_library.load_prompt(
                self._prompt_category,
                self._prompt_name
            )
            
            # Prepare context for prompt
            prompt_context = self.prepare_context(context)
            
            # Execute prompt
            response = await self._prompt_executor.execute(
                prompt=prompt_template,
                context=prompt_context,
                model=self._model,
                temperature=self._temperature
            )
            
            # Parse result
            result = self.parse_result(response, context)
            
            # Update context history
            context.add_history(self.name, f"Processed successfully")
            
            return result
            
        except Exception as e:
            error_msg = f"Agent {self.name} failed: {str(e)}"
            context.add_history(self.name, f"Failed: {str(e)}")
            raise AgentExecutionError(error_msg) from e
    
    @abstractmethod
    def prepare_context(self, context: DocumentContext) -> dict:
        """
        Prepare the context dictionary for the prompt template.
        
        Args:
            context: Current document context
            
        Returns:
            Dictionary with variables to inject into prompt
        """
        pass
    
    @abstractmethod
    def parse_result(self, response: str, context: DocumentContext) -> AgentResult:
        """
        Parse the LLM response into an AgentResult.
        
        Args:
            response: Raw LLM response
            context: Current document context
            
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

