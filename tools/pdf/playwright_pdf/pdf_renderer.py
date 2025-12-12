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
    Render PDF using Playwright's page.pdf.
    
    Args:
        page: Playwright page object
        pdf_file: Output PDF path
        header_html: HTML template for header
        footer_html: HTML template for footer
        margin_config: Margin configuration (extracted from CSS or defaults)
        page_format: Page format (A4, Letter, etc.)
        verbose: Verbose output
    
    Returns:
        bool: True if PDF was created successfully
    """
    # Use provided margin config or defaults
    if margin_config is None:
        margin_config = DEFAULT_MARGINS.copy()
    
    # Handle page format - Playwright supports 'A4', 'Letter', 'Legal', or custom
    if page_format in ['A4', 'Letter', 'Legal']:
        format_option = page_format
    else:
        format_option = 'A4'  # Fallback
        if verbose:
            print(f"[WARN] Custom page format '{page_format}' not fully supported, using A4")
    
    # Playwright requires margins when using display_header_footer
    # Headers/footers render in the margin space
    if verbose:
        print(f"{OK} Passing margins to page.pdf(): {margin_config}")
        print(f"{OK} Page format: {format_option}")
    
    options = {
        'format': format_option,
        'print_background': True,
        'display_header_footer': True,
        'header_template': header_html,
        'footer_template': footer_html,
        'margin': margin_config
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
                        dark_mode: bool = False) -> tuple[str, str]:
    """
    Build header and footer HTML templates.
    
    Args:
        title: Document title
        organization: Organization name
        author: Author name
        date: Date string
        dark_mode: Use dark theme styling
    
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
    
    header_template = f'''<div style="font-size: 9px; width: 100%; text-align: center; padding: 8px 20px; background-color: {bg_color}; color: {text_color}; border-bottom: 1px solid {border_color}; -webkit-print-color-adjust: exact; print-color-adjust: exact;">{header_content}</div>'''
    
    # Build footer template
    footer_parts = []
    if author:
        footer_parts.append(author)
    if date:
        footer_parts.append(date)
    
    footer_left = ' | '.join(footer_parts) if footer_parts else ''
    
    footer_template = f'''<div style="font-size: 9px; width: 100%; text-align: center; padding: 8px 20px; background-color: {bg_color}; color: {text_color}; -webkit-print-color-adjust: exact; print-color-adjust: exact;">{footer_left}<span style="margin-left: 20px; color: {accent_color};">Page <span class="pageNumber"></span> of <span class="totalPages"></span></span></div>'''
    
    return header_template, footer_template
