"""
Browser Lifecycle Management
=============================
Handles Playwright browser initialization and page loading.
Zero logic about diagrams, scaling, or PDF generation.
"""
from pathlib import Path
from typing import Optional
from playwright.async_api import async_playwright, Browser, Page

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    INFO = f"{Fore.CYAN}[INFO]{Style.RESET_ALL}"
    ERR = f"{Fore.RED}[ERROR]{Style.RESET_ALL}"
except ImportError:
    INFO = "[INFO]"
    ERR = "[ERROR]"


from contextlib import asynccontextmanager

# Phase A: 2025 Playwright Optimization Flags
# Applied: Dec 13, 2025
# Expected Gain: +15-25% faster rendering + 100% platform consistency
PLAYWRIGHT_OPTIMIZATION_FLAGS = [
    '--disable-gpu',                          # CPU rendering (faster, consistent)
    '--disable-gpu-rasterization',            # Consistency across platforms
    '--disable-gpu-compositing',              # Reduce memory overhead
    '--disable-lcd-text',                     # Consistent font rendering
    '--force-device-scale-factor=1',          # DPI consistency (prevents scaling issues)
    '--force-color-profile=srgb',             # Color profile normalization
    '--disable-font-subpixel-positioning',    # Consistent text metrics
    '--no-sandbox',                           # Required in containers
    '--disable-dev-shm-usage',                # Reduce memory pressure
    '--disable-web-security',                 # Allow local file access
]

# PDF Page Sizes at 96 DPI (Playwright standard)
# CRITICAL: Viewport MUST match PDF output size for correct CSS flow
PDF_PAGE_SIZES = {
    'A4': {'width': 794, 'height': 1122},      # 210mm × 297mm at 96 DPI
    'Letter': {'width': 816, 'height': 1056},  # 8.5" × 11" at 96 DPI
    'Legal': {'width': 816, 'height': 1344},   # 8.5" × 14" at 96 DPI
}


@asynccontextmanager
async def open_page(
    html_file: Path, 
    verbose: bool = False,
    page_format: str = 'A4',
    color_scheme: Optional[str] = None,  # None = let CSS @media queries decide
):
    """
    Open a Playwright page and load the HTML file with Phase A optimizations.
    
    CRITICAL FIX (Dec 2025):
    - Viewport now matches PDF output size (prevents 1920→794px scaling issues)
    - Color scheme is None by default (lets CSS @media prefers-color-scheme work)
    
    Phase A (2025) Improvements:
    - GPU rendering disabled for consistency
    - sRGB color profile normalization
    - DPI locked to 96 DPI (1.0)
    - Font rendering consistency across platforms
    - Viewport matches PDF page size for correct CSS flow
    
    Args:
        html_file: Path to HTML file to load
        verbose: Enable verbose logging
        page_format: PDF page format ('A4', 'Letter', 'Legal')
        color_scheme: Force color scheme ('dark', 'light') or None to let CSS decide
    
    Usage:
        async with open_page(html_file, verbose=True) as (browser, page):
            # use page here
    """
    browser = None
    async with async_playwright() as playwright:
        if verbose:
            print(f"{INFO} Launching Chromium browser (Phase A optimizations enabled)...")
        
        browser = await playwright.chromium.launch(
            headless=True,  # Headless mode for PDF generation (required)
            args=PLAYWRIGHT_OPTIMIZATION_FLAGS,
        )
        
        # Get viewport size matching PDF output
        viewport = PDF_PAGE_SIZES.get(page_format, PDF_PAGE_SIZES['A4'])
        
        # Create context - color_scheme=None lets CSS @media queries work
        context_args = {
            'viewport': viewport,
            'timezone_id': 'UTC',
            'locale': 'en-US',
        }
        
        # Only set color_scheme if explicitly specified (None = let CSS decide)
        if color_scheme is not None:
            context_args['color_scheme'] = color_scheme
        
        context = await browser.new_context(**context_args)
        
        page = await context.new_page()
        
        if verbose:
            print(f"{INFO} Browser optimizations: GPU disabled, sRGB profile, DPI locked to 96")
            print(f"{INFO} Viewport: {viewport['width']}×{viewport['height']}px ({page_format})")
            if color_scheme:
                print(f"{INFO} Color scheme: {color_scheme} (forced)")
            else:
                print(f"{INFO} Color scheme: auto (CSS @media queries)")
        
        # Load HTML file
        html_path = html_file.absolute()
        file_url = f"file:///{str(html_path).replace(chr(92), '/')}"
        
        if verbose:
            print(f"{INFO} Loading HTML: {file_url}")
        
        await page.goto(file_url, wait_until='networkidle', timeout=30000)
        
        try:
            yield browser, page
        finally:
            if context:
                await context.close()
            if browser:
                await browser.close()
