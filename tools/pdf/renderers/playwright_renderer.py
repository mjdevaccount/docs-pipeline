#!/usr/bin/env python3
"""
FAANG-Grade PDF Generator using Playwright
==========================================
Perfect SVG rendering including <foreignObject> support
Industry-standard approach used by Microsoft, AWS, Stripe

This is now a thin wrapper around the modular playwright_pdf package.
All functionality has been refactored into separate modules following SOLID principles.

For backward compatibility, this script maintains the same CLI interface.
"""
import sys
import asyncio
from pathlib import Path

# Import from the new modular package
from playwright_pdf.cli import main as cli_main

# Re-export key functions for programmatic use
from playwright_pdf.pipeline import generate_pdf
from playwright_pdf.config import PdfGenerationConfig
from playwright_pdf.browser import open_page
from playwright_pdf.dom_analyzer import analyze_layout
from playwright_pdf.layout_transformer import compute_scaling, apply_scaling
from playwright_pdf.styles import inject_fonts, inject_pagination_css
from playwright_pdf.decorators.cover import inject_cover_page
from playwright_pdf.decorators.toc import inject_toc
from playwright_pdf.decorators.watermark import add_watermark
from playwright_pdf.pdf_renderer import render_pdf, build_header_footer
from playwright_pdf.postprocess import (
    extract_headings_from_page,
    add_bookmarks_to_pdf,
    embed_metadata
)

# Backward compatibility: maintain old function signatures
async def html_to_pdf_playwright(html_file, pdf_file, options=None, verbose=False):
    """
    Legacy function for backward compatibility.
    Converts options dict to PdfGenerationConfig and calls new pipeline.
    """
    config = PdfGenerationConfig(
        html_file=Path(html_file),
        pdf_file=Path(pdf_file),
        verbose=verbose
    )
    
    if options:
        # Map old options format to new config
        if 'title' in options:
            config.title = options['title']
        if 'author' in options:
            config.author = options['author']
        # Add other option mappings as needed
    
    return await generate_pdf(config)


async def generate_pdf_from_html(
    html_file, pdf_file, title=None, subtitle=None, author=None,
    organization=None, date=None, logo_path=None,
    generate_toc=False, generate_cover=False,
    watermark=None, css_file=None, page_format='A4', verbose=False,
    version=None, doc_type=None, classification=None
):
    """
    Legacy function for backward compatibility.
    Maintains the old function signature but uses new pipeline internally.
    """
    config = PdfGenerationConfig(
        html_file=Path(html_file),
        pdf_file=Path(pdf_file),
        title=title,
        subtitle=subtitle,
        author=author,
        organization=organization,
        date=date,
        version=version,
        type=doc_type,
        classification=classification,
        logo_path=Path(logo_path) if logo_path else None,
        generate_toc=generate_toc,
        generate_cover=generate_cover,
        watermark=watermark,
        css_file=Path(css_file) if css_file else None,
        page_format=page_format,
        verbose=verbose
    )
    
    return await generate_pdf(config)


def check_playwright():
    """Check if Playwright is installed and browsers are available"""
    from playwright_pdf.cli import check_playwright_installation
    return check_playwright_installation()


async def batch_generate_pdfs(html_files, output_dir, common_options=None, verbose=False):
    """
    Legacy batch processing function.
    Maintains backward compatibility.
    """
    import os
    from playwright_pdf.pipeline import generate_pdf
    from playwright_pdf.config import PdfGenerationConfig
    
    os.makedirs(output_dir, exist_ok=True)
    
    async def generate_single(html_file):
        pdf_file = os.path.join(output_dir, Path(html_file).stem + '.pdf')
        config = PdfGenerationConfig(
            html_file=Path(html_file),
            pdf_file=Path(pdf_file),
            verbose=verbose
        )
        
        if common_options:
            # Map common_options to config
            if 'title' in common_options:
                config.title = common_options['title']
            if 'author' in common_options:
                config.author = common_options['author']
            # Add other mappings as needed
        
        success = await generate_pdf(config)
        return (html_file, success)
    
    # Process in batches of 3 (Chromium is memory-intensive)
    results = []
    for i in range(0, len(html_files), 3):
        batch = html_files[i:i+3]
        batch_results = await asyncio.gather(*[generate_single(f) for f in batch])
        results.extend(batch_results)
        
        completed = i + len(batch)
        print(f"[INFO] Progress: {completed}/{len(html_files)} PDFs generated")
    
    # Summary
    print(f"\n[INFO] Batch Generation Summary:")
    for html_file, success in results:
        status = "[OK]" if success else "[ERROR]"
        print(f"  {status} {Path(html_file).name}")
    
    return all(success for _, success in results)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Generate PDF from HTML using Playwright (FAANG-grade rendering)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic conversion
  python pdf_playwright.py input.html output.pdf
  
  # With full metadata
  python pdf_playwright.py input.html output.pdf \\
    --title "Project Documentation Architecture" \\
    --author "Matt Jeffcoat" \\
    --organization "Engineering Team" \\
    --date "November 2025" \\
    --generate-cover \\
    --generate-toc
  
  # Draft with watermark
  python pdf_playwright.py input.html output.pdf --watermark "DRAFT"
  
  # Batch processing
  python pdf_playwright.py --batch docs/*.html --output-dir output/
  
  # Check installation
  python pdf_playwright.py --check
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
    parser.add_argument('--logo', help='Path to logo image')
    parser.add_argument('--css', help='Custom CSS file')
    parser.add_argument('--page-format', default='A4', choices=['A4', 'Letter', 'Legal'],
                       help='Page format: A4 (default), Letter (8.5x11in), or Legal (8.5x14in)')
    parser.add_argument('--generate-cover', action='store_true', help='Generate cover page')
    parser.add_argument('--generate-toc', action='store_true', help='Generate table of contents')
    parser.add_argument('--watermark', help='Add watermark text (e.g., DRAFT)')
    parser.add_argument('--batch', nargs='+', help='Batch process multiple HTML files')
    parser.add_argument('--output-dir', help='Output directory for batch processing')
    parser.add_argument('--check', action='store_true', help='Check Playwright installation')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    
    args = parser.parse_args()
    
    if args.check:
        sys.exit(0 if check_playwright() else 1)
    
    if args.batch:
        if not args.output_dir:
            print("[ERROR] --output-dir required for batch processing")
            sys.exit(1)
        success = asyncio.run(batch_generate_pdfs(
            args.batch, 
            args.output_dir,
            verbose=args.verbose
        ))
        sys.exit(0 if success else 1)
    
    if not args.input or not args.output:
        parser.print_help()
        sys.exit(1)
    
    if not Path(args.input).exists():
        print(f"[ERROR] Input file not found: {args.input}")
        sys.exit(1)
    
    success = asyncio.run(generate_pdf_from_html(
        args.input,
        args.output,
        title=args.title,
        author=args.author,
        organization=args.organization,
        date=args.date,
        logo_path=args.logo,
        generate_toc=args.generate_toc,
        generate_cover=args.generate_cover,
        watermark=args.watermark,
        css_file=args.css,
        page_format=args.page_format,
        verbose=args.verbose
    ))
    
    # Embed PDF metadata if provided (already done in pipeline, but keeping for backward compatibility)
    # Metadata is already embedded by the pipeline, so this is a no-op
    
    sys.exit(0 if success else 1)
