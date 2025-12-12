"""
Command-Line Interface
======================

CLI tools for PDF generation from markdown files.

Usage:
    python -m tools.pdf.cli.main input.md output.pdf
    python tools/pdf/cli/main.py input.md --profile tech-whitepaper
    
For backward compatibility, convert_final.py also works:
    python tools/pdf/convert_final.py input.md output.pdf
"""

from .main import main, parallel_batch_convert, __version__

__all__ = ['main', 'parallel_batch_convert', '__version__']

