"""
Browser Lifecycle Management
=============================
Handles Playwright browser initialization and page loading.
Zero logic about diagrams, scaling, or PDF generation.
"""
from pathlib import Path
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

@asynccontextmanager
async def open_page(html_file: Path, verbose: bool = False):
    """
    Open a Playwright page and load the HTML file.
    
    Usage:
        async with open_page(html_file, verbose=True) as (browser, page):
            # use page here
    """
    browser = None
    async with async_playwright() as playwright:
        if verbose:
            print(f"{INFO} Launching Chromium browser...")
        
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                '--disable-gpu',
                '--no-sandbox',
                '--disable-dev-shm-usage',
                '--disable-web-security',
            ]
        )
        
        page = await browser.new_page()
        
        # CRITICAL: Use large viewport to ensure SVG diagrams render at full size
        # PDF rendering uses its own dimensions, but we need accurate measurements
        # Use a large viewport so SVGs aren't constrained
        await page.set_viewport_size({"width": 1920, "height": 1080})
        
        # Load HTML file
        html_path = html_file.absolute()
        file_url = f"file:///{str(html_path).replace(chr(92), '/')}"
        
        if verbose:
            print(f"{INFO} Loading HTML: {file_url}")
        
        await page.goto(file_url, wait_until='networkidle', timeout=30000)
        
        try:
            yield browser, page
        finally:
            if browser:
                await browser.close()

