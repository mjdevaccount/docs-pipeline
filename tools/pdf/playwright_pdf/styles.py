"""
Styles Module - CSS & Fonts
============================
Handles CSS injection and web font loading.
Separate from scaling logic and DOM analysis.
"""
from pathlib import Path
from typing import List, Optional
from playwright.async_api import Page

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    INFO = f"{Fore.CYAN}[INFO]{Style.RESET_ALL}"
except ImportError:
    INFO = "[INFO]"


# Default font families
WEB_FONT_FAMILIES_DEFAULT = ["Inter", "Source Code Pro"]


def _load_adaptive_pagination_css() -> str:
    """
    Load the core pagination CSS from the shared layout.css file.

    Keeping this in a standalone asset ensures layout rules are not
    duplicated between Python and CSS, and makes it easy to tweak
    pagination behavior without touching code.
    """
    # styles.py lives in tools/pdf/playwright_pdf; layout.css is in tools/pdf/styles/
    layout_css_path = Path(__file__).parent.parent / "styles" / "layout.css"
    if layout_css_path.exists():
        return layout_css_path.read_text(encoding="utf-8")

    # Fallback: minimal pagination utilities ONLY - do NOT override @page or body
    # Profile CSS (dark-pro, etc) controls page margins, backgrounds, and body styles
    return """
    /* Pagination utilities - do not override profile styles */
    .page-break { page-break-before: always; break-before: page; }
    .avoid-break-inside { page-break-inside: avoid; break-inside: avoid-page; }
    .cover-page-wrapper { page-break-after: always; break-after: page; }
    .toc-wrapper { page-break-after: always; break-after: page; }
    """


# Adaptive pagination CSS loaded from external asset.
ADAPTIVE_PAGINATION_CSS = _load_adaptive_pagination_css()


async def inject_fonts(page: Page, font_families: Optional[List[str]] = None, verbose: bool = False) -> None:
    """
    Inject Google Fonts into page with loading detection.
    Ensures fonts are loaded before PDF generation.
    """
    if font_families is None:
        font_families = WEB_FONT_FAMILIES_DEFAULT
    
    font_links = []
    for font in font_families:
        font_name_encoded = font.replace(' ', '+')
        font_links.append(
            f'<link href="https://fonts.googleapis.com/css2?family={font_name_encoded}:wght@400;600;700&display=swap" rel="stylesheet">'
        )
    
    # Inject into head
    await page.evaluate(f"""
        () => {{
            const head = document.head;
            {(''.join([f"head.insertAdjacentHTML('beforeend', `{link}`);" for link in font_links]))}
        }}
    """)
    
    # Wait for fonts to load (critical!)
    await page.evaluate("document.fonts.ready")
    
    # DO NOT set document.body.style.fontFamily here - that overrides CSS rules with inline styles
    # Let profile CSS control font family via CSS rules (higher specificity when needed)
    # Google Fonts are now available as fallbacks in the font stack
    
    if verbose:
        print(f"{INFO} Loaded web fonts: {', '.join(font_families)}")


async def inject_pagination_css(page: Page, verbose: bool = False) -> None:
    """
    Inject adaptive pagination CSS.
    This should be called AFTER scaling is applied.
    """
    await page.add_style_tag(content=ADAPTIVE_PAGINATION_CSS)
    if verbose:
        print(f"{INFO} Injected adaptive pagination CSS with anti-collision rules")


async def inject_custom_css(page: Page, css_file: str, verbose: bool = False) -> None:
    """
    Inject custom CSS from file.
    """
    from pathlib import Path
    css_path = Path(css_file)
    if css_path.exists():
        css_content = css_path.read_text(encoding='utf-8')
        await page.add_style_tag(content=css_content)
        if verbose:
            print(f"{INFO} Loaded custom CSS: {css_file}")
    else:
        if verbose:
            print(f"{INFO} Custom CSS file not found: {css_file}")


async def inject_print_background(page: Page, is_dark_mode: bool, bg_color: str = None, verbose: bool = False) -> None:
    """
    Inject CSS to ensure background colors extend to print margins (full bleed).
    
    In PDF printing, margins are created by Playwright's print settings and the page 
    background doesn't extend into those margins - only content does. This fix uses
    a fixed pseudo-element to ensure backgrounds extend to the edges.
    
    Args:
        page: Playwright page object
        is_dark_mode: Whether dark mode is active
        bg_color: Optional explicit background color (defaults based on mode)
        verbose: Enable verbose logging
    """
    if is_dark_mode:
        color = bg_color or '#0f172a'  # Slate-950 (matches dark-pro)
        css = f"""
        @media print {{
            html, body {{
                background-color: {color} !important;
                margin: 0 !important;
                padding: 0 !important;
            }}
            
            /* Full-bleed background using fixed positioning */
            body::before {{
                content: '';
                position: fixed;
                top: 0;
                left: 0;
                right: 0;
                bottom: 0;
                background-color: {color};
                z-index: -1000;
                pointer-events: none;
                -webkit-print-color-adjust: exact;
                print-color-adjust: exact;
            }}
        }}
        """
    else:
        color = bg_color or '#ffffff'
        css = f"""
        @media print {{
            html, body {{
                background-color: {color} !important;
                margin: 0 !important;
                padding: 0 !important;
            }}
        }}
        """
    
    await page.add_style_tag(content=css)
    
    if verbose:
        print(f"{INFO} Injected print background CSS (dark_mode={is_dark_mode}, color={color})")

