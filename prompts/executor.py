"""
Prompt Executor Implementation
===============================
Executes prompts against an LLM (OpenAI, Anthropic, etc.).
"""
from typing import Dict, Any, Optional
from .core.interfaces import IPromptExecutor
from .core.exceptions import LLMExecutionError


class OpenAIPromptExecutor(IPromptExecutor):
    """
    Prompt executor using OpenAI API.
    Supports GPT-4, GPT-3.5-turbo, etc.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize OpenAI executor.
        
        Args:
            api_key: OpenAI API key. If None, uses OPENAI_API_KEY env var.
        """
        try:
            import openai
            self._openai = openai
            
            if api_key:
                self._openai.api_key = api_key
            # Otherwise, openai will use OPENAI_API_KEY env var
            
        except ImportError:
            raise LLMExecutionError(
                "OpenAI package not installed. Install with: pip install openai"
            )
    
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
            model: Optional model override (default: gpt-4)
            temperature: Sampling temperature
            
        Returns:
            LLM response as string
        """
        try:
            # Inject context variables into prompt
            formatted_prompt = prompt.format(**context)
            
            # Use specified model or default
            model_name = model or "gpt-4"
            
            # Call OpenAI API
            response = await self._openai.ChatCompletion.acreate(
                model=model_name,
                messages=[
                    {"role": "system", "content": "You are an expert technical writer and architect."},
                    {"role": "user", "content": formatted_prompt}
                ],
                temperature=temperature,
                max_tokens=4000  # Adjust as needed
            )
            
            return response.choices[0].message.content
            
        except KeyError as e:
            raise LLMExecutionError(f"Missing context variable: {e}")
        except Exception as e:
            raise LLMExecutionError(f"OpenAI API error: {str(e)}")


class AnthropicPromptExecutor(IPromptExecutor):
    """
    Prompt executor using Anthropic API (Claude).
    """
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize Anthropic executor.
        
        Args:
            api_key: Anthropic API key. If None, uses ANTHROPIC_API_KEY env var.
        """
        try:
            import anthropic
            self._anthropic = anthropic
            
            if api_key:
                self._client = anthropic.Anthropic(api_key=api_key)
            else:
                self._client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var
            
        except ImportError:
            raise LLMExecutionError(
                "Anthropic package not installed. Install with: pip install anthropic"
            )
    
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
            model: Optional model override (default: claude-3-sonnet)
            temperature: Sampling temperature
            
        Returns:
            LLM response as string
        """
        try:
            # Inject context variables into prompt
            formatted_prompt = prompt.format(**context)
            
            # Use specified model or default
            model_name = model or "claude-3-sonnet-20240229"
            
            # Call Anthropic API
            message = self._client.messages.create(
                model=model_name,
                max_tokens=4000,
                temperature=temperature,
                messages=[
                    {"role": "user", "content": formatted_prompt}
                ]
            )
            
            return message.content[0].text
            
        except KeyError as e:
            raise LLMExecutionError(f"Missing context variable: {e}")
        except Exception as e:
            raise LLMExecutionError(f"Anthropic API error: {str(e)}")


class MockPromptExecutor(IPromptExecutor):
    """
    Mock executor for testing without calling real LLM APIs.
    """
    
    def __init__(self, mock_response: str = "Mock response"):
        self._mock_response = mock_response
    
    async def execute(
        self,
        prompt: str,
        context: Dict[str, Any],
        model: Optional[str] = None,
        temperature: float = 0.7
    ) -> str:
        """Return mock response"""
        return self._mock_response

