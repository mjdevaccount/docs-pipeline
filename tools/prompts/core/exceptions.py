"""
Prompt Pipeline Exceptions
===========================
Custom exceptions for prompt pipeline operations.
"""


class PromptPipelineError(Exception):
    """Base exception for prompt pipeline errors"""
    pass


class PromptNotFoundError(PromptPipelineError):
    """Raised when a prompt template cannot be found"""
    pass


class AgentExecutionError(PromptPipelineError):
    """Raised when an agent fails to execute"""
    pass


class LLMExecutionError(PromptPipelineError):
    """Raised when LLM execution fails"""
    pass


class ValidationError(PromptPipelineError):
    """Raised when document validation fails"""
    pass


class ConfigurationError(PromptPipelineError):
    """Raised when configuration is invalid"""
    pass

