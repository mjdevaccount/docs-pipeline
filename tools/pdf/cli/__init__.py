"""
PDF Generation CLI - Primary Entry Point
=========================================

This is THE command-line interface for PDF generation.

Usage:
    python -m tools.pdf.cli.main input.md output.pdf
    python -m tools.pdf.cli.main input.md --profile tech-whitepaper --cover --toc
    python -m tools.pdf.cli.main --batch doc1.md doc2.md --threads 4
    
For library usage, import from core:
    from tools.pdf.core import markdown_to_pdf
"""

from .main import main, parallel_batch_convert, __version__

__all__ = ['main', 'parallel_batch_convert', '__version__']
