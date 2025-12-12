#!/usr/bin/env python3
"""
PDF Generation - Backward Compatibility Layer
==============================================

This module provides backward compatibility for existing code.
All functionality has been refactored to:

- Core library:  tools.pdf.core (markdown_to_pdf, etc.)
- CLI:           tools.pdf.cli.main

Usage (Library):
    from tools.pdf.core import markdown_to_pdf
    markdown_to_pdf('input.md', 'output.pdf', profile='tech-whitepaper')

Usage (CLI):
    python -m tools.pdf.cli.main input.md output.pdf --profile tech-whitepaper
    
This file re-exports everything for backward compatibility:
    from tools.pdf.convert_final import markdown_to_pdf  # Still works!
"""

import sys
import warnings
from pathlib import Path

# Suppress RuntimeWarning about module import order
warnings.filterwarnings('ignore', message='.*found in sys.modules after import of package.*', 
                        category=RuntimeWarning)

# Add module path for imports
sys.path.insert(0, str(Path(__file__).parent))

# =============================================================================
# RE-EXPORTS FOR BACKWARD COMPATIBILITY
# =============================================================================

# Core converters
from core import (
    markdown_to_pdf,
    markdown_to_docx,
    markdown_to_html,
    batch_convert,
    extract_metadata,
    get_cache_dir,
    check_dependencies,
    validate_markdown,
)

# CLI components (for scripts that import main)
from cli import main, parallel_batch_convert, __version__

# Pipeline components (for advanced users)
from pipeline import (
    process_document,
    create_pdf_pipeline,
    create_docx_pipeline,
    create_html_pipeline,
    PipelineContext,
    OutputFormat,
    PipelineConfig,
)

# =============================================================================
# PUBLIC API
# =============================================================================

__all__ = [
    # Core converters
    'markdown_to_pdf',
    'markdown_to_docx',
    'markdown_to_html',
    'batch_convert',
    # Utilities
    'extract_metadata',
    'get_cache_dir',
    'check_dependencies',
    'validate_markdown',
    # CLI
    'main',
    'parallel_batch_convert',
    '__version__',
    # Pipeline (advanced)
    'process_document',
    'create_pdf_pipeline',
    'create_docx_pipeline', 
    'create_html_pipeline',
    'PipelineContext',
    'OutputFormat',
    'PipelineConfig',
]


# =============================================================================
# CLI ENTRY POINT (for backward compatibility)
# =============================================================================

if __name__ == "__main__":
    main()
