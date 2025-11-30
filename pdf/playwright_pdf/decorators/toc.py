"""
Table of Contents Decorator
===========================
Generates table of contents with CSS-based page break.
"""
from playwright.async_api import Page

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    INFO = f"{Fore.CYAN}[INFO]{Style.RESET_ALL}"
    WARN = f"{Fore.YELLOW}[WARN]{Style.RESET_ALL}"
except ImportError:
    INFO = "[INFO]"
    WARN = "[WARN]"


async def inject_toc(page: Page, verbose: bool = False) -> bool:
    """
    Generate table of contents with CSS-based page break.
    Uses padding-bottom + page-break-after on wrapper (most reliable for Chromium).
    """
    try:
        await page.evaluate("""
            () => {
                // Get all headings, but exclude those inside the cover page wrapper
                const coverPageWrapper = document.querySelector('.cover-page-wrapper');
                const allHeadings = document.querySelectorAll('h1, h2, h3');
                const headings = Array.from(allHeadings).filter(heading => {
                    // Skip headings that are inside the cover page wrapper
                    if (coverPageWrapper && coverPageWrapper.contains(heading)) {
                        return false;
                    }
                    return true;
                });
                
                if (headings.length === 0) return false;
                
                // Use wrapper with explicit page-break-after inline to ensure Chromium PDF respects it
                let toc = '<div class="toc-wrapper" style="page-break-after: always !important; break-after: page !important; padding-bottom: 0.5in;">';
                toc += '<h1 style="font-size: 24pt; margin: 0 0 20px 0; border-bottom: 2px solid #333; padding-bottom: 10px;">Table of Contents</h1>';
                toc += '<ul style="list-style: none; padding: 0; margin: 20px 0 40px 0;">';
                
                headings.forEach((heading, idx) => {
                    const level = parseInt(heading.tagName[1]);
                    const text = heading.textContent.trim();
                    const id = heading.id || `heading-${idx}`;
                    
                    if (!heading.id) heading.id = id;
                    
                    const indent = (level - 1) * 20;
                    const fontSize = 14 - (level - 1) * 1;
                    
                    toc += `<li style="margin: 0 0 8px ${indent}px; line-height: 1.6;">`;
                    toc += `<a href="#${id}" style="text-decoration: none; color: #1976d2; font-size: ${fontSize}pt;">`;
                    toc += text;
                    toc += '</a></li>';
                });
                
                toc += '</ul>';
                toc += '</div>'; // Close wrapper - page break happens here
                
                // Insert TOC directly after cover page
                const coverPage = document.querySelector('.cover-page-wrapper');
                if (coverPage && coverPage.parentElement) {
                    coverPage.insertAdjacentHTML('afterend', toc);
                } else {
                    // Insert at start of body
                    const firstElement = document.body.firstElementChild;
                    if (firstElement) {
                        firstElement.insertAdjacentHTML('beforebegin', toc);
                    } else {
                        document.body.insertAdjacentHTML('afterbegin', toc);
                    }
                }
                
                return true;
            }
        """)
        if verbose:
            print(f"{INFO} Generated table of contents with CSS page break")
        return True
    except Exception as e:
        if verbose:
            print(f"{WARN} TOC generation failed: {e}")
        return False

