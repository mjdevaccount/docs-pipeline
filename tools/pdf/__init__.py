"""PDF generation tool for markdown documents with Mermaid diagrams."""

__version__ = "1.0.0"

# Expose main functions for programmatic use
# Use lazy import ONLY to avoid RuntimeWarning when running as module
# (python -m tools.pdf.convert_final)
# Never import convert_final at module level to prevent the warning
__all__ = ["markdown_to_pdf"]

def __getattr__(name):
    """Lazy import to avoid RuntimeWarning when running as module."""
    if name == "markdown_to_pdf":
        try:
            from .convert_final import markdown_to_pdf
            return markdown_to_pdf
        except ImportError:
            # CLI-only mode if dependencies not installed
            raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

