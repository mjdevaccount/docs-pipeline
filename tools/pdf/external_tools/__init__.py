"""
External Tool Wrappers
=======================

Platform-independent abstractions for external command-line tools.

This module provides:
- ExternalTool: Base abstraction for all external tools
- PandocExecutor: Pandoc wrapper
- MermaidCLI: Mermaid CLI wrapper
- KatexCLI: KaTeX CLI wrapper
- SvgoCLI: SVGO optimizer wrapper

Benefits:
- Platform-independent executable resolution
- Mockable for testing
- Centralized error handling
- Consistent API
"""

from .base import ExternalTool, CommandResult, ToolNotFoundError
from .pandoc import PandocExecutor
from .mermaid_cli import MermaidCLI
from .katex import KatexCLI
from .svgo import SvgoCLI
from .executable_finder import ExecutableFinder

__all__ = [
    'ExternalTool',
    'CommandResult',
    'ToolNotFoundError',
    'PandocExecutor',
    'MermaidCLI',
    'KatexCLI',
    'SvgoCLI',
    'ExecutableFinder',
]

