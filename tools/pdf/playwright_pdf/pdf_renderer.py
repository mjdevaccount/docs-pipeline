"""
PDF Renderer
============
Handles Playwright PDF generation.
Single responsibility: call page.pdf with proper options.
"""
from pathlib import Path
from typing import Optional
from playwright.async_api import Page

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    OK = f"{Fore.GREEN}[OK]{Style.RESET_ALL}"
    ERR = f"{Fore.RED}[ERROR]{Style.RESET_ALL}"
except ImportError:
    OK = "[OK]"
    ERR = "[ERROR]"


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
        verbose: Verbose output
    
    Returns:
        bool: True if PDF was created successfully
    """
    # Use provided margin config or default
    if margin_config is None:
        margin_config = {
            'top': '0.75in',
            'right': '0.75in',
            'bottom': '1in',  # Bottom margin is 1in (more space for footer)
            'left': '0.75in'
        }
    
    # Handle page format - Playwright supports 'A4', 'Letter', 'Legal', or custom
    if page_format in ['A4', 'Letter', 'Legal']:
        format_option = page_format
    else:
        # Custom size - parse and use as width/height tuple in inches
        # Format: "8.5in 11in" or "8.5x11"
        format_option = 'A4'  # Fallback
        if verbose:
            print(f"[WARN] Custom page format '{page_format}' not fully supported, using A4")
    
    # Let CSS @page rules control margins (margin_config kept for measurement only)
    # Passing margin to page.pdf() overrides CSS, so we omit it
    options = {
        'format': format_option,
        'print_background': True,
        'display_header_footer': True,
        'header_template': header_html,
        'footer_template': footer_html
        # margin intentionally omitted - CSS @page { margin: ... } now controls it
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
                        author: str = None, date: str = None) -> tuple[str, str]:
    """
    Build header and footer HTML templates.
    
    Returns:
        tuple: (header_html, footer_html)
    """
    # Build header template
    header_parts = []
    if title:
        header_parts.append(f'<span style="font-weight: 600;">{title}</span>')
    if organization:
        header_parts.append(f'<span style="color: #666; font-size: 8px;">{organization}</span>')
    
    header_template = f'''
        <div style="font-size: 9px; width: 100%; text-align: center; padding-top: 10px; border-bottom: 1px solid #ddd;">
            {' | '.join(header_parts) if header_parts else ''}
        </div>
    '''
    
    # Build footer template
    footer_parts = []
    if author:
        footer_parts.append(author)
    if date:
        footer_parts.append(date)
    
    footer_template = f'''
        <div style="font-size: 9px; width: 100%; text-align: center; padding-bottom: 10px;">
            {' | '.join(footer_parts) if footer_parts else ''}
            <span style="margin-left: 20px; color: #666;">
                Page <span class="pageNumber"></span> of <span class="totalPages"></span>
            </span>
        </div>
    '''
    
    return header_template, footer_template

