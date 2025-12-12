"""
Playwright PDF renderer wrapper.
Delegates to existing playwright_renderer.py for backward compatibility.
"""
import asyncio
from .base import PdfRenderer, RenderError
from .config import RenderConfig

# Check if Playwright is available
PLAYWRIGHT_AVAILABLE = False
try:
    from playwright.async_api import async_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    pass


class PlaywrightRenderer(PdfRenderer):
    """
    PDF renderer using Playwright (Chromium).
    
    Strengths:
    - Perfect SVG rendering (including <foreignObject>)
    - JavaScript execution
    - Modern CSS support
    - Industry-standard (used by Microsoft, AWS, Stripe)
    
    Limitations:
    - Requires browser installation (~200MB Chromium)
    - Slower than WeasyPrint
    - More memory-intensive
    
    Example:
        renderer = PlaywrightRenderer()
        config = RenderConfig(
            html_file='doc.html',
            output_file='doc.pdf',
            generate_cover=True,
            generate_toc=True
        )
        success = renderer.render(config)
    """
    
    def get_name(self) -> str:
        return "Playwright"
    
    def is_available(self) -> bool:
        return PLAYWRIGHT_AVAILABLE
    
    def render(self, config: RenderConfig) -> bool:
        """
        Render HTML to PDF using Playwright.
        
        Args:
            config: Rendering configuration
        
        Returns:
            True if rendering succeeded
        
        Raises:
            RenderError: If rendering fails
        """
        try:
            self.validate_config(config)
            self.log(f"Rendering {config.html_file} to {config.output_file}", config)
            
            # Import the existing Playwright renderer module
            import sys
            from pathlib import Path
            sys.path.insert(0, str(Path(__file__).parent.parent))
            
            try:
                from renderers.playwright_renderer import generate_pdf_from_html
            except ImportError:
                # Try alternative import path
                from .playwright_renderer import generate_pdf_from_html
            
            # Call existing Playwright renderer (async)
            # Pass subtitle via custom_options since the function signature doesn't include it
            success = asyncio.run(generate_pdf_from_html(
                html_file=str(config.html_file),
                pdf_file=str(config.output_file),
                title=config.title,
                author=config.author,
                organization=config.organization,
                date=config.date,
                version=config.version,
                doc_type=config.doc_type,
                classification=config.classification,
                logo_path=str(config.logo_path) if config.logo_path else None,
                generate_toc=config.generate_toc,
                generate_cover=config.generate_cover,
                watermark=config.watermark,
                css_file=str(config.css_file) if config.css_file else None,
                verbose=config.verbose,
                subtitle=getattr(config, 'subtitle', None)
            ))
            
            if success:
                self.log(f"Successfully created {config.output_file}", config)
            else:
                raise RenderError("Playwright generation returned False")
            
            return success
            
        except Exception as e:
            error_msg = f"Playwright rendering failed: {e}"
            self.log(f"ERROR: {error_msg}", config)
            raise RenderError(error_msg) from e

