"""
PDF Renderer
============
Handles Playwright PDF generation.
Single responsibility: call page.pdf with proper options.
"""
from pathlib import Path
from typing import Optional
from playwright.async_api import Page
from .utils import filter_placeholder, is_placeholder

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    OK = f"{Fore.GREEN}[OK]{Style.RESET_ALL}"
    ERR = f"{Fore.RED}[ERROR]{Style.RESET_ALL}"
except ImportError:
    OK = "[OK]"
    ERR = "[ERROR]"


# Default margins (used only if CSS extraction fails)
DEFAULT_MARGINS = {
    'top': '2cm',
    'right': '1.8cm',
    'bottom': '2cm',
    'left': '1.8cm'
}


async def render_pdf(
    page: Page,
    pdf_file: str,
    header_html: str,
    footer_html: str,
    margin_config: Optional[dict] = None,
    page_format: str = 'A4',
    verbose: bool = False
) -> bool:
    """
    Render PDF using Playwright's page.pdf with full-bleed backgrounds.
    
    Uses zero left/right margins for full-bleed backgrounds, with small
    top/bottom margins for Playwright header/footer templates.
    
    Args:
        page: Playwright page object
        pdf_file: Output PDF path
        header_html: HTML template for header (Playwright template)
        footer_html: HTML template for footer (Playwright template)
        margin_config: Margin configuration (top/bottom used for header/footer space)
        page_format: Page format (A4, Letter, etc.)
        verbose: Verbose output
    
    Returns:
        bool: True if PDF was created successfully
    """
    if margin_config is None:
        margin_config = DEFAULT_MARGINS.copy()
    
    # Full-bleed: zero left/right margins, keep top/bottom for header/footer
    pdf_margins = {
        'top': margin_config.get('top', '2cm'),
        'right': '0',  # Zero for full-bleed
        'bottom': margin_config.get('bottom', '2cm'),
        'left': '0'    # Zero for full-bleed
    }
    
    # Handle page format - Playwright supports 'A4', 'Letter', 'Legal', or custom
    if page_format in ['A4', 'Letter', 'Legal']:
        format_option = page_format
    else:
        format_option = 'A4'  # Fallback
        if verbose:
            print(f"[WARN] Custom page format '{page_format}' not fully supported, using A4")
    
    if verbose:
        print(f"{OK} Full-bleed: zero left/right margins, top/bottom for header/footer")
        print(f"{OK} PDF margins: {pdf_margins}")
        print(f"{OK} Page format: {format_option}")
    
    options = {
        'format': format_option,
        'print_background': True,
        'display_header_footer': True,
        'header_template': header_html,
        'footer_template': footer_html,
        'margin': pdf_margins
    }
    
    try:
        if verbose:
            print(f"{OK} Generating PDF...")
        
        await page.pdf(path=pdf_file, **options)
        
        if Path(pdf_file).exists():
            size_kb = Path(pdf_file).stat().st_size / 1024
            if verbose:
                print(f"{OK} Generated PDF: {pdf_file} ({size_kb:.1f} KB)")
            return True
        else:
            if verbose:
                print(f"{ERR} PDF file not created")
            return False
    except Exception as e:
        if verbose:
            print(f"{ERR} PDF rendering failed: {e}")
        return False


def build_header_footer(title: str = None, organization: str = None, 
                        author: str = None, date: str = None,
                        dark_mode: bool = False,
                        margin_left: str = '1.8cm',
                        margin_right: str = '1.8cm') -> tuple[str, str]:
    """
    Build header and footer HTML templates for Playwright PDF.
    
    Templates extend full page width for full-bleed backgrounds.
    Content is padded to align with body content margins.
    
    Args:
        title: Document title
        organization: Organization name
        author: Author name
        date: Date string
        dark_mode: Use dark theme styling
        margin_left: Left margin for content padding
        margin_right: Right margin for content padding
    
    Returns:
        tuple: (header_html, footer_html)
    """
    # Filter placeholder values using shared utility
    title = filter_placeholder(title, None)
    organization = filter_placeholder(organization, None)
    author = filter_placeholder(author, None)
    
    # Theme-aware colors
    if dark_mode:
        text_color = '#94a3b8'   # Slate-400
        border_color = '#334155' # Slate-700
        accent_color = '#64748b' # Slate-500
        bg_color = '#0f172a'     # Dark navy
    else:
        text_color = '#374151'   # Gray-700
        border_color = '#e5e7eb' # Gray-200
        accent_color = '#6b7280' # Gray-500
        bg_color = '#ffffff'     # White
    
    # Build header template
    header_parts = []
    if title:
        header_parts.append(f'<span style="font-weight: 600;">{title}</span>')
    if organization:
        header_parts.append(f'<span style="font-size: 8px;">{organization}</span>')
    
    header_content = ' | '.join(header_parts) if header_parts else '&nbsp;'
    
    # Full-width header with content padding to match body margins
    header_template = f'''<div style="font-size: 9px; width: 100%; margin: 0; text-align: center; padding: 8px {margin_right} 8px {margin_left}; background-color: {bg_color}; color: {text_color}; border-bottom: 1px solid {border_color}; -webkit-print-color-adjust: exact; print-color-adjust: exact; box-sizing: border-box;">{header_content}</div>'''
    
    # Build footer template
    footer_parts = []
    if author:
        footer_parts.append(author)
    if date:
        footer_parts.append(date)
    
    footer_left = ' | '.join(footer_parts) if footer_parts else ''
    
    # Full-width footer with content padding to match body margins
    footer_template = f'''<div style="font-size: 9px; width: 100%; margin: 0; text-align: center; padding: 8px {margin_right} 8px {margin_left}; background-color: {bg_color}; color: {text_color}; -webkit-print-color-adjust: exact; print-color-adjust: exact; box-sizing: border-box;">{footer_left}<span style="margin-left: 20px; color: {accent_color};">Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>'''
    
    return header_template, footer_template
