"""
Core PDF Generation Module
===========================

This module contains the core conversion functions that can be imported
and used as a library. No CLI dependencies, pure conversion logic.

Usage:
    from tools.pdf.core import markdown_to_pdf, markdown_to_docx, markdown_to_html
    
    # Simple conversion
    success = markdown_to_pdf('input.md', 'output.pdf')
    
    # With options
    success = markdown_to_pdf(
        'input.md', 
        'output.pdf',
        profile='tech-whitepaper',
        renderer='playwright',
        generate_cover=True,
        generate_toc=True
    )
"""

from .converter import (
    markdown_to_pdf,
    markdown_to_docx,
    markdown_to_html,
    batch_convert,
)

from .utils import (
    extract_metadata,
    get_cache_dir,
    check_dependencies,
    validate_markdown,
)

__all__ = [
    # Converters
    'markdown_to_pdf',
    'markdown_to_docx', 
    'markdown_to_html',
    'batch_convert',
    # Utilities
    'extract_metadata',
    'get_cache_dir',
    'check_dependencies',
    'validate_markdown',
]

