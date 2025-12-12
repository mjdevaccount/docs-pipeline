"""
Cover Page Decorator
====================
Generates professional cover page with guaranteed page break.
"""
from pathlib import Path
from datetime import datetime
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


async def inject_cover_page(page: Page, config: CoverConfig, verbose: bool = False) -> bool:
    """
    Generate professional cover page with GUARANTEED page break.
    Uses fixed height + explicit spacer div for Chromium PDF compatibility.
    """
    try:
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
        
        # Build classification badge if present
        classification_html = ''
        if classification:
            classification_html = f'<div class="cover-classification" style="font-size: 10pt; font-weight: 600; margin-bottom: 20px; text-transform: uppercase; letter-spacing: 1px;">{classification}</div>'
        
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
            org_html = f'<div class="cover-subtitle" style="font-size: 18pt; margin: 0 0 40px 0;">{subtitle_text}</div>'
        
        # Build author section
        author_html = ''
        if author:
            author_html = f'{author}<br/>'
        
        # Use page-break-after in style to force page break
        cover_html = f"""
            <div class="cover-page-wrapper" style="
                height: 100vh;
                min-height: 10in;
                padding: 2in 40px;
                margin-bottom: 0;
                display: flex;
                flex-direction: column;
                justify-content: center;
                align-items: center;
                text-align: center;
                box-sizing: border-box;
                page-break-after: always;
                break-after: page;
            ">
                {logo_html}
                {classification_html}
                <h1 class="cover-title" style="font-size: 36pt; margin: 0 0 20px 0; font-weight: 600; line-height: 1.2;">
                    {title}
                </h1>
                {org_html}
                <div class="cover-metadata" style="font-size: 14pt; margin: 0; line-height: 1.6;">
                    {author_html}
                    {config.date or datetime.now().strftime('%B %d, %Y')}
                </div>
                {version_type_html}
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

