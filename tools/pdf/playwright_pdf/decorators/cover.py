"""
Cover Page Decorator
====================
Generates professional cover page with guaranteed page break.
"""
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
from playwright.async_api import Page
from ..config import CoverConfig
from ..utils import filter_placeholder

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    INFO = f"{Fore.CYAN}[INFO]{Style.RESET_ALL}"
    WARN = f"{Fore.YELLOW}[WARN]{Style.RESET_ALL}"
except ImportError:
    INFO = "[INFO]"
    WARN = "[WARN]"


# Default margins to match dark-pro profile (fallback)
DEFAULT_PAGE_MARGINS = {
    'top': '2cm',
    'right': '1.8cm',
    'bottom': '2cm',
    'left': '1.8cm'
}


async def inject_cover_page(page: Page, config: CoverConfig, verbose: bool = False, margin_config: Optional[Dict[str, str]] = None) -> bool:
    """
    Generate professional cover page with GUARANTEED page break.
    Uses fixed height + explicit spacer div for Chromium PDF compatibility.
    
    Args:
        page: Playwright page object
        config: Cover page configuration
        verbose: Enable verbose output
        margin_config: Page margins from CSS profile (e.g. {'top': '2cm', 'left': '1.8cm', ...})
                      Used to compute negative margins for full-bleed cover page
    """
    try:
        # Use provided margins or defaults
        margins = margin_config or DEFAULT_PAGE_MARGINS
        margin_top = margins.get('top', '2cm')
        margin_left = margins.get('left', '1.8cm')
        margin_right = margins.get('right', '1.8cm')
        
        logo_html = ""
        if config.logo_path and Path(config.logo_path).exists():
            logo_data = Path(config.logo_path).read_bytes()
            import base64
            logo_b64 = base64.b64encode(logo_data).decode()
            ext = Path(config.logo_path).suffix[1:] or 'png'
            logo_html = f'<img src="data:image/{ext};base64,{logo_b64}" style="max-width: 200px; margin-bottom: 40px;" />'
        
        # Extract additional metadata from config if available
        doc_type = getattr(config, 'type', None) or ''
        classification = getattr(config, 'classification', None) or ''
        version = getattr(config, 'version', None) or ''
        
        # Filter out placeholder values using shared utility
        title = filter_placeholder(config.title, 'Documentation')
        organization = filter_placeholder(config.organization, '')
        author = filter_placeholder(config.author, '')
        subtitle = filter_placeholder(getattr(config, 'subtitle', None), '')
        
        # Build classification badge if present (industry standard: prominent, above title)
        classification_html = ''
        if classification:
            classification_html = f'''<div class="cover-classification" style="
                font-size: 11pt;
                font-weight: 700;
                margin-bottom: 40px;
                text-transform: uppercase;
                letter-spacing: 2px;
                padding: 10px 24px;
                border-radius: 4px;
                border: 2px solid currentColor;
            ">{classification}</div>'''
        
        # Build version/type info if present
        version_type_html = ''
        if version or doc_type:
            parts = []
            if doc_type:
                parts.append(doc_type)
            if version:
                parts.append(f'Version {version}')
            if parts:
                version_type_html = f'<div class="cover-version" style="font-size: 11pt; margin-top: 20px;">{" | ".join(parts)}</div>'
        
        # Build organization/subtitle section - prefer subtitle, fall back to organization
        org_html = ''
        subtitle_text = subtitle or organization
        if subtitle_text:
            org_html = f'<div class="cover-subtitle" style="font-size: 16pt; margin: 0; font-weight: 400; letter-spacing: 0.02em;">{subtitle_text}</div>'
        
        # Build author section
        author_html = ''
        if author:
            author_html = f'{author}<br/>'
        
        # Cover page with DYNAMIC negative margins to extend into page margin area
        # Uses actual CSS profile margins instead of hardcoded values
        # Industry standard: cover pages have NO running headers/footers
        # Use width: 100% on all children with text-align: center for reliable centering
        cover_html = f"""
            <div class="cover-page-wrapper" style="
                position: relative;
                width: calc(100% + {margin_left} + {margin_right});
                height: calc(100vh + {margin_top});
                min-height: 11in;
                margin-top: -{margin_top};
                margin-left: -{margin_left};
                margin-right: -{margin_right};
                padding: 2.5in 0 1.5in 0;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
                box-sizing: border-box;
                page-break-after: always;
                break-after: page;
                background: inherit;
            ">
                {logo_html}
                {classification_html}
                <h1 class="cover-title" style="
                    width: 100%;
                    max-width: none;
                    font-size: 42pt;
                    margin: 0 0 24px 0;
                    padding: 0 1in;
                    font-weight: 700;
                    line-height: 1.15;
                    letter-spacing: 0.04em;
                    text-transform: uppercase;
                    text-align: center;
                    box-sizing: border-box;
                ">
                    {title}
                </h1>
                <div class="cover-divider" style="
                    width: 60%;
                    max-width: 400px;
                    height: 3px;
                    background: linear-gradient(90deg, transparent, currentColor, transparent);
                    margin: 20px auto 30px auto;
                    opacity: 0.4;
                "></div>
                <div style="width: 100%; text-align: center; padding: 0 1in; box-sizing: border-box;">
                    {org_html}
                </div>
                <div class="cover-metadata" style="width: 100%; text-align: center; padding: 0 1in; box-sizing: border-box; font-size: 13pt; margin: 30px 0 0 0; line-height: 1.8; opacity: 0.85;">
                    {author_html}
                    {config.date or datetime.now().strftime('%B %Y')}
                </div>
                <div style="width: 100%; text-align: center; padding: 0 1in; box-sizing: border-box;">
                    {version_type_html}
                </div>
            </div>
        """
        
        await page.evaluate(f"""
            (html) => {{
                document.body.insertAdjacentHTML('afterbegin', html);
            }}
        """, cover_html)
        
        if verbose:
            print(f"{INFO} Generated cover page with forced page break")
        return True
    except Exception as e:
        if verbose:
            print(f"{WARN} Cover page generation failed: {e}")
        return False

