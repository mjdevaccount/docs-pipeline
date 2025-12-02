"""
PDF Rendering Backends
=======================

Provides different rendering backends for PDF generation:
- PlaywrightRenderer: High-quality rendering with perfect SVG support
- WeasyPrintRenderer: Fast rendering with good browser compatibility

Each renderer follows the Renderer interface for consistent usage.
"""

from .playwright_renderer import generate_pdf_from_html

__all__ = [
    'generate_pdf_from_html',
]

