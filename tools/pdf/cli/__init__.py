"""
PDF Generation CLI (v4.0.0) - Modern Typer-based CLI
====================================================

Usage:
    python -m tools.pdf.cli convert input.md output.pdf
    python -m tools.pdf.cli batch docs/**/*.md --format pdf
    python -m tools.pdf.cli diag env
    
For library usage, import from core:
    from tools.pdf.core import markdown_to_pdf
"""

from .app import app
from .app import __version__

__all__ = ['app', '__version__']
