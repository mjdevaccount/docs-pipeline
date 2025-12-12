"""
PDF Generation Tool
====================

Convert Markdown documents to professional PDFs, DOCX, and HTML.

CLI Usage (Primary):
    python -m tools.pdf.cli.main input.md output.pdf
    python -m tools.pdf.cli.main input.md --profile tech-whitepaper --cover --toc
    
Library Usage:
    from tools.pdf import markdown_to_pdf
    
    # Simple conversion
    markdown_to_pdf('input.md', 'output.pdf')
    
    # With options
    markdown_to_pdf(
        'input.md',
        'output.pdf',
        profile='tech-whitepaper',
        renderer='playwright',
        generate_cover=True,
        generate_toc=True
    )

Docker Usage:
    docker-compose run --rm docs-pipeline-web \\
        python -m tools.pdf.cli.main input.md output.pdf

Architecture:
    tools/pdf/
    ├── cli/            # Command-line interface (PRIMARY ENTRY POINT)
    │   └── main.py     # CLI with argparse, parallelism, batch processing
    ├── core/           # Library functions
    │   ├── converter.py  # markdown_to_pdf, markdown_to_docx, markdown_to_html
    │   └── utils.py      # Utilities
    ├── config/         # Style profiles
    ├── pipeline.py     # Pipeline orchestration
    └── renderers/      # PDF renderers (WeasyPrint, Playwright)
"""

__version__ = "3.0.0"

# =============================================================================
# PUBLIC API - Import from core module
# =============================================================================

from .core import (
    # Converters
    markdown_to_pdf,
    markdown_to_docx,
    markdown_to_html,
    batch_convert,
    # Utilities
    extract_metadata,
    get_cache_dir,
    check_dependencies,
    validate_markdown,
)

__all__ = [
    # Version
    '__version__',
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
]
