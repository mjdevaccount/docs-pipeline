"""
Core PDF Generation Module
===========================

This module contains the core conversion functions that can be imported
and used as a library. No CLI dependencies, pure conversion logic.

Main Features:
- Markdown to PDF/DOCX/HTML conversion
- Glossary term highlighting and indexing
- Markdown export and formatting
- Diagram caching and rendering
- Metadata extraction

Usage:
    from tools.pdf.core import markdown_to_pdf, MarkdownExporter, GlossaryProcessor
    
    # Simple conversion
    success = markdown_to_pdf('input.md', 'output.pdf')
    
    # With glossary highlighting
    success = markdown_to_pdf(
        'input.md', 
        'output.pdf',
        glossary_file='glossary.yaml',
        profile='tech-whitepaper',
        generate_cover=True
    )
    
    # Export to markdown
    exporter = MarkdownExporter()
    markdown, metadata = exporter.html_to_markdown(html_content)
    
    # Process glossary
    glossary = GlossaryProcessor('glossary.yaml')
    highlighted = glossary.highlight_terms(content)
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

from .markdown_exporter import (
    MarkdownExporter,
    MarkdownMetadata,
    MarkdownExportStats,
)

from .glossary_processor import (
    GlossaryProcessor,
    GlossaryTerm,
    GlossaryStats,
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
    # Markdown exporter
    'MarkdownExporter',
    'MarkdownMetadata',
    'MarkdownExportStats',
    # Glossary processor
    'GlossaryProcessor',
    'GlossaryTerm',
    'GlossaryStats',
]
