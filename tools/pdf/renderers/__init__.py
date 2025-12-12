"""
PDF Renderer Strategy Module

Provides pluggable PDF rendering backends following the Strategy pattern.

Available Renderers:
    - PlaywrightRenderer: Perfect SVG + JavaScript support, FAANG-grade rendering

Usage:
    from renderers import RendererFactory, RenderConfig, RendererType
    
    # Get Playwright renderer
    renderer = RendererFactory.get_available_renderer(verbose=True)
    
    # Configure rendering
    config = RenderConfig(
        html_file='document.html',
        output_file='document.pdf',
        generate_cover=True
    )
    
    # Render
    success = renderer.render(config)
"""

from .base import PdfRenderer, RenderError
from .config import RenderConfig, RendererType, PageFormat
from .factory import RendererFactory

# Import implementations (may fail if dependencies missing)
try:
    from .playwright_wrapper import PlaywrightRenderer
except ImportError:
    PlaywrightRenderer = None

# Legacy export for backward compatibility
try:
    from .playwright_renderer import generate_pdf_from_html
except ImportError:
    generate_pdf_from_html = None

__all__ = [
    # Base classes
    'PdfRenderer',
    'RenderError',
    
    # Configuration
    'RenderConfig',
    'RendererType',
    'PageFormat',
    
    # Factory
    'RendererFactory',
    
    # Implementations
    'PlaywrightRenderer',
    
    # Legacy
    'generate_pdf_from_html',
    
    # Convenience function
    'render_pdf',
]


def render_pdf(
    html_file: str,
    output_file: str,
    renderer_type: RendererType = None,
    **kwargs
) -> bool:
    """
    Convenience function to render PDF in one line.
    
    Args:
        html_file: Path to HTML input
        output_file: Path to PDF output
        renderer_type: Renderer to use (Playwright if None)
        **kwargs: Additional RenderConfig options
    
    Returns:
        True if rendering succeeded
    
    Example:
        from renderers import render_pdf, RendererType
        
        success = render_pdf(
            'document.html',
            'document.pdf',
            generate_cover=True,
            title='My Document'
        )
    """
    from pathlib import Path
    
    if renderer_type:
        renderer = RendererFactory.get_renderer(renderer_type)
    else:
        renderer = RendererFactory.get_available_renderer()
        if not renderer:
            raise ImportError("Playwright renderer not available")
    
    config = RenderConfig(
        html_file=Path(html_file),
        output_file=Path(output_file),
        **kwargs
    )
    
    return renderer.render(config)
