"""PDF generation tool for markdown documents with Mermaid diagrams."""

__version__ = "1.0.0"

# Expose main functions for programmatic use
try:
    from .convert_final import markdown_to_pdf
    __all__ = ["markdown_to_pdf"]
except ImportError:
    # CLI-only mode if dependencies not installed
    __all__ = []

