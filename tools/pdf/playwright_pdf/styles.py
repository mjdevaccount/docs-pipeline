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


async def inject_full_bleed_background(
    page: Page, 
    bg_color: str,
    margin_config: dict = None,
    verbose: bool = False
) -> None:
    """
    Inject CSS for full-bleed backgrounds in PDF printing.
    
    PDF uses zero left/right margins (with top/bottom for header/footer).
    This CSS adds left/right padding to body to create visual margins.
    Background extends to left/right paper edges.
    
    Args:
        page: Playwright page object
        bg_color: Background color to use (extracted from CSS)
        margin_config: Margin configuration (left/right used for padding)
        verbose: Enable verbose logging
    """
    # Only need left/right padding (top/bottom handled by PDF margins + header/footer)
    pad_right = margin_config.get('right', '1.8cm') if margin_config else '1.8cm'
    pad_left = margin_config.get('left', '1.8cm') if margin_config else '1.8cm'
    
    css = f"""
    /* Full-bleed background - zero left/right PDF margins, CSS padding for content */
    @media print {{
        html {{
            background: {bg_color} !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }}
        
        body {{
            background: {bg_color} !important;
            margin: 0 !important;
            /* Left/right padding for content alignment (top/bottom via PDF margins) */
            padding-left: {pad_left} !important;
            padding-right: {pad_right} !important;
            box-sizing: border-box !important;
            -webkit-print-color-adjust: exact !important;
            print-color-adjust: exact !important;
        }}
        
        /* Ensure content respects box-sizing */
        *, *::before, *::after {{
            box-sizing: border-box;
        }}
    }}
    
    /* Screen preview consistency */
    @media screen {{
        html, body {{
            background: {bg_color};
        }}
    }}
    """
    
    await page.add_style_tag(content=css)
    
    if verbose:
        print(f"{INFO} Full-bleed CSS: bg={bg_color}, left/right padding={pad_left}/{pad_right}")

