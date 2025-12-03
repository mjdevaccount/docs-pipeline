"""
WeasyPrint PDF renderer implementation.
Uses WeasyPrint for CSS Paged Media rendering.
"""
from .base import PdfRenderer, RenderError
from .config import RenderConfig

try:
    from weasyprint import HTML, CSS
    WEASYPRINT_AVAILABLE = True
except ImportError:
    WEASYPRINT_AVAILABLE = False


class WeasyPrintRenderer(PdfRenderer):
    """
    PDF renderer using WeasyPrint.
    
    Strengths:
    - Excellent CSS Paged Media support (@page rules)
    - Lightweight and fast
    - Pure Python implementation
    
    Limitations:
    - Limited SVG <foreignObject> support
    - No JavaScript execution
    - Some modern CSS features unsupported
    
    Example:
        renderer = WeasyPrintRenderer()
        config = RenderConfig(html_file='doc.html', output_file='doc.pdf')
        success = renderer.render(config)
    """
    
    def __init__(self):
        """Initialize WeasyPrint renderer"""
        if not WEASYPRINT_AVAILABLE:
            raise ImportError("WeasyPrint not installed. Install with: pip install weasyprint")
    
    def get_name(self) -> str:
        return "WeasyPrint"
    
    def is_available(self) -> bool:
        return WEASYPRINT_AVAILABLE
    
    def render(self, config: RenderConfig) -> bool:
        """
        Render HTML to PDF using WeasyPrint.
        
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
            
            # Load CSS
            stylesheets = []
            if config.css_file:
                self.log(f"Using custom CSS: {config.css_file}", config)
                # Check if CSS file looks like Playwright-specific
                if 'playwright' in str(config.css_file).lower():
                    self.log("WARNING: CSS file appears to be for Playwright renderer", config)
                    self.log("         WeasyPrint may not support all properties", config)
                try:
                    stylesheets.append(CSS(filename=str(config.css_file)))
                except Exception as e:
                    self.log(f"WARNING: Failed to load CSS ({e}), using default", config)
                    stylesheets = [self._get_default_css()]
            else:
                self.log("Using default WeasyPrint CSS", config)
                stylesheets = [self._get_default_css()]
            
            # Render PDF
            html = HTML(filename=str(config.html_file))
            html.write_pdf(str(config.output_file), stylesheets=stylesheets)
            
            self.log(f"Successfully created {config.output_file}", config)
            return True
            
        except Exception as e:
            error_msg = f"WeasyPrint rendering failed: {e}"
            self.log(f"ERROR: {error_msg}", config)
            raise RenderError(error_msg) from e
    
    def _get_default_css(self) -> CSS:
        """
        Get default CSS for WeasyPrint rendering.
        Provides professional document styling with @page rules.
        """
        default_css = """
            @page {
                size: A4;
                margin: 25mm 15mm 20mm 15mm;
                @top-left {
                    content: "Project Documentation";
                    font-size: 9pt;
                    color: #666;
                    font-style: italic;
                }
                @top-right {
                    content: string(section-title);
                    font-size: 9pt;
                    color: #666;
                    font-style: italic;
                }
                @bottom-center {
                    content: "Confidential";
                    font-size: 9pt;
                    color: #888;
                }
                @bottom-right {
                    content: "Page " counter(page);
                    font-size: 9pt;
                    color: #666;
                }
            }
            @page:first {
                @top-left { content: none; }
                @top-right { content: none; }
                @bottom-center { content: none; }
                @bottom-right { content: none; }
            }
            body {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11pt;
                line-height: 1.6;
                color: #000;
            }
            h1 {
                font-size: 24pt;
                padding: 16pt 0 12pt 0;
                border-bottom: 3pt solid #000;
                page-break-before: always;
                page-break-after: avoid;
            }
            h2 {
                font-size: 18pt;
                margin-top: 24pt;
                padding-bottom: 6pt;
                border-bottom: 1.5pt solid #999;
                page-break-after: avoid;
                string-set: section-title content();
            }
            h3 {
                font-size: 14pt;
                margin-top: 18pt;
                page-break-after: avoid;
            }
            code {
                font-family: 'Consolas', 'Monaco', monospace;
                background-color: #f5f5f5;
                padding: 2pt 4pt;
                font-size: 10pt;
            }
            pre {
                background-color: #f5f5f5;
                border-left: 3pt solid #2196F3;
                padding: 12pt;
                margin: 12pt 0;
                page-break-inside: avoid;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin: 12pt 0;
                page-break-inside: avoid;
            }
            th, td {
                border: 1pt solid #333;
                padding: 8pt;
                text-align: left;
            }
            th {
                background-color: #f0f0f0;
                font-weight: bold;
            }
            img {
                max-width: 100%;
                height: auto;
                display: block;
                margin: 16pt auto;
                page-break-inside: avoid;
            }
        """
        return CSS(string=default_css)
    
    def validate_config(self, config: RenderConfig) -> None:
        """Validate WeasyPrint-specific configuration"""
        super().validate_config(config)
        
        # WeasyPrint doesn't support generate_toc/generate_cover natively
        if config.generate_toc:
            self.log("WARNING: generate_toc not supported by WeasyPrint (use Pandoc --toc instead)", config)
        if config.generate_cover:
            self.log("WARNING: generate_cover not supported by WeasyPrint (inject in HTML instead)", config)
        if config.watermark:
            self.log("WARNING: watermark not supported by WeasyPrint", config)

