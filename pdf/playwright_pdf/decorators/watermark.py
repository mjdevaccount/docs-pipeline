"""
Watermark Decorator
===================
Adds diagonal watermark to all pages.
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


async def add_watermark(page: Page, watermark_text: str, verbose: bool = False) -> bool:
    """
    Add diagonal watermark to all pages.
    """
    try:
        await page.evaluate(f"""
            (text) => {{
                const style = document.createElement('style');
                style.textContent = `
                    @media print {{
                        body::before {{
                            content: "${{text}}";
                            position: fixed;
                            top: 50%;
                            left: 50%;
                            transform: translate(-50%, -50%) rotate(-45deg);
                            font-size: 120pt;
                            font-weight: bold;
                            color: rgba(255, 0, 0, 0.1);
                            z-index: 9999;
                            pointer-events: none;
                            white-space: nowrap;
                        }}
                    }}
                `;
                document.head.appendChild(style);
            }}
        """, watermark_text)
        
        if verbose:
            print(f"{INFO} Added watermark: {watermark_text}")
        return True
    except Exception as e:
        if verbose:
            print(f"{WARN} Watermark addition failed: {e}")
        return False

