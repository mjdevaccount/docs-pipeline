"""
CLI Module
==========
Command-line interface for PDF generation.
Parses arguments and calls the pipeline.
"""
import sys
import asyncio
from pathlib import Path
from .pipeline import generate_pdf
from .config import PdfGenerationConfig
# check_playwright is defined locally in this file

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    ERR = f"{Fore.RED}[ERROR]{Style.RESET_ALL}"
except ImportError:
    ERR = "[ERROR]"


def check_playwright_installation():
    """Check if Playwright is installed and browsers are available"""
    try:
        from playwright.async_api import async_playwright
        PLAYWRIGHT_AVAILABLE = True
    except ImportError:
        print(f"{ERR} Playwright not installed")
        print(f"Install with: pip install playwright")
        return False
    
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                browser.close()
                print(f"Playwright Chromium available")
                return True
            except Exception as e:
                print(f"Playwright installed but Chromium not found")
                print(f"Install browsers with: playwright install chromium")
                return False
    except Exception as e:
        print(f"{ERR} Playwright check failed: {e}")
        return False


def main():
    """Main CLI entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate PDF from HTML using Playwright (FAANG-grade rendering)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic conversion
  python -m playwright_pdf.cli input.html output.pdf
  
  # With full metadata
  python -m playwright_pdf.cli input.html output.pdf \\
    --title "Reporting Manager Architecture" \\
    --author "Matt Jeffcoat" \\
    --organization "Engineering Team" \\
    --date "November 2025" \\
    --generate-cover \\
    --generate-toc
  
  # Draft with watermark
  python -m playwright_pdf.cli input.html output.pdf --watermark "DRAFT"
  
  # Check installation
  python -m playwright_pdf.cli --check
        """
    )
    
    parser.add_argument('input', nargs='?', help='Input HTML file')
    parser.add_argument('output', nargs='?', help='Output PDF file')
    parser.add_argument('--title', help='Document title')
    parser.add_argument('--author', help='Author name')
    parser.add_argument('--organization', help='Organization name')
    parser.add_argument('--subject', help='Document subject (PDF metadata)')
    parser.add_argument('--keywords', help='Keywords for PDF metadata')
    parser.add_argument('--date', help='Document date')
    parser.add_argument('--logo', type=Path, help='Path to logo image')
    parser.add_argument('--generate-cover', action='store_true', help='Generate cover page')
    parser.add_argument('--generate-toc', action='store_true', help='Generate table of contents')
    parser.add_argument('--watermark', help='Add watermark text (e.g., DRAFT)')
    parser.add_argument('--css', type=Path, help='Custom CSS file')
    parser.add_argument('--page-format', default='A4', choices=['A4', 'Letter', 'Legal'],
                       help='Page format: A4 (default), Letter (8.5x11in), or Legal (8.5x14in)')
    parser.add_argument('--check', action='store_true', help='Check Playwright installation')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.check:
        sys.exit(0 if check_playwright_installation() else 1)
    
    if not args.input or not args.output:
        parser.print_help()
        sys.exit(1)
    
    if not Path(args.input).exists():
        print(f"{ERR} Input file not found: {args.input}")
        sys.exit(1)
    
    # Build configuration
    config = PdfGenerationConfig(
        html_file=Path(args.input),
        pdf_file=Path(args.output),
        title=args.title,
        author=args.author,
        organization=args.organization,
        date=args.date,
        subject=args.subject,
        keywords=args.keywords,
        generate_cover=args.generate_cover,
        generate_toc=args.generate_toc,
        watermark=args.watermark,
        logo_path=args.logo,
        css_file=args.css,
        page_format=args.page_format,
        verbose=args.verbose
    )
    
    # Run pipeline
    success = asyncio.run(generate_pdf(config))
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()

