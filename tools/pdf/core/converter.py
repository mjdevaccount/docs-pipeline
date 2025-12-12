"""
Core Markdown Converters
========================

Pure conversion functions with no CLI dependencies.
These are the library functions that can be imported and used programmatically.

Usage:
    from tools.pdf.core.converter import markdown_to_pdf
    success = markdown_to_pdf('input.md', 'output.pdf', profile='tech-whitepaper')
"""

import sys
from pathlib import Path
from typing import Optional, Dict, Any, List

# Add parent path for pipeline imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline import (
    process_document,
    OutputFormat,
)


def markdown_to_pdf(
    md_file: str,
    output_pdf: str,
    logo_path: Optional[str] = None,
    css_file: Optional[str] = None,
    cache_dir: Optional[str] = None,
    use_cache: bool = True,
    theme_config: Optional[str] = None,
    highlight_style: Optional[str] = None,
    crossref_config: Optional[str] = None,
    glossary_file: Optional[str] = None,
    renderer: str = 'playwright',
    generate_toc: bool = False,
    generate_cover: bool = False,
    watermark: Optional[str] = None,
    verbose: bool = False,
    profile: Optional[str] = None,
    custom_metadata: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Convert Markdown to PDF.
    
    Args:
        md_file: Path to input Markdown file
        output_pdf: Path to output PDF file
        logo_path: Optional logo image path
        css_file: Optional CSS file path
        cache_dir: Diagram cache directory
        use_cache: Enable diagram caching
        theme_config: Mermaid theme config JSON
        highlight_style: Code highlighting style
        crossref_config: Pandoc-crossref config
        glossary_file: Glossary YAML file
        renderer: PDF renderer ('playwright' - only renderer available)
        generate_toc: Generate table of contents
        generate_cover: Generate cover page
        watermark: Watermark text
        verbose: Verbose output
        profile: Profile name (e.g., 'tech-whitepaper')
        custom_metadata: Metadata overrides
    
    Returns:
        True if conversion succeeded, False otherwise
    """
    config = {
        'logo_path': logo_path,
        'css_file': css_file,
        'cache_dir': cache_dir,
        'use_cache': use_cache,
        'theme_config': theme_config,
        'highlight_style': highlight_style or 'pygments',
        'crossref_config': crossref_config,
        'glossary_file': glossary_file,
        'renderer': renderer,
        'generate_toc': generate_toc,
        'generate_cover': generate_cover,
        'watermark': watermark,
        'verbose': verbose,
        'profile': profile,
        'custom_metadata': custom_metadata or {}
    }
    
    # Remove None values
    config = {k: v for k, v in config.items() if v is not None}
    
    if verbose:
        print(f"\nConverting {md_file} to PDF...")
        print(f"  Renderer: {renderer}")
        if generate_cover:
            print(f"  Cover page: enabled")
        if generate_toc:
            print(f"  Table of contents: enabled")
    
    try:
        success = process_document(
            input_file=md_file,
            output_file=output_pdf,
            output_format=OutputFormat.PDF,
            **config
        )
        
        if success and verbose:
            print(f"[OK] Created: {output_pdf}")
        
        return success
        
    except Exception as e:
        if verbose:
            print(f"[ERROR] PDF conversion failed: {e}")
        return False


def markdown_to_docx(
    md_file: str,
    output_docx: str,
    logo_path: Optional[str] = None,
    reference_docx: Optional[str] = None,
    cache_dir: Optional[str] = None,
    use_cache: bool = True,
    theme_config: Optional[str] = None,
    highlight_style: Optional[str] = None,
    crossref_config: Optional[str] = None,
    glossary_file: Optional[str] = None,
    verbose: bool = False,
    profile: Optional[str] = None,
) -> bool:
    """
    Convert Markdown to DOCX.
    
    Args:
        md_file: Path to input Markdown file
        output_docx: Path to output DOCX file
        logo_path: Optional logo (not used in DOCX)
        reference_docx: Reference DOCX template
        cache_dir: Diagram cache directory
        use_cache: Enable diagram caching
        theme_config: Mermaid theme config JSON
        highlight_style: Code highlighting style
        crossref_config: Pandoc-crossref config
        glossary_file: Glossary YAML file
        verbose: Verbose output
        profile: Profile name
    
    Returns:
        True if conversion succeeded, False otherwise
    """
    config = {
        'reference_docx': reference_docx,
        'cache_dir': cache_dir,
        'use_cache': use_cache,
        'theme_config': theme_config,
        'highlight_style': highlight_style or 'pygments',
        'crossref_config': crossref_config,
        'glossary_file': glossary_file,
        'also_png': True,  # DOCX needs PNG diagrams
        'verbose': verbose,
        'profile': profile,
    }
    
    # Remove None values
    config = {k: v for k, v in config.items() if v is not None}
    
    if verbose:
        print(f"\nConverting {md_file} to DOCX...")
    
    try:
        success = process_document(
            input_file=md_file,
            output_file=output_docx,
            output_format=OutputFormat.DOCX,
            **config
        )
        
        if success and verbose:
            print(f"[OK] Created: {output_docx}")
        
        return success
        
    except Exception as e:
        if verbose:
            print(f"[ERROR] DOCX conversion failed: {e}")
        return False


def markdown_to_html(
    md_file: str,
    output_html: str,
    cache_dir: Optional[str] = None,
    use_cache: bool = True,
    theme_config: Optional[str] = None,
    highlight_style: Optional[str] = None,
    crossref_config: Optional[str] = None,
    glossary_file: Optional[str] = None,
    css_file: Optional[str] = None,
    verbose: bool = False,
    profile: Optional[str] = None,
) -> bool:
    """
    Convert Markdown to HTML.
    
    Args:
        md_file: Path to input Markdown file
        output_html: Path to output HTML file
        cache_dir: Diagram cache directory
        use_cache: Enable diagram caching
        theme_config: Mermaid theme config JSON
        highlight_style: Code highlighting style
        crossref_config: Pandoc-crossref config
        glossary_file: Glossary YAML file
        css_file: Custom CSS file
        verbose: Verbose output
        profile: Profile name
    
    Returns:
        True if conversion succeeded, False otherwise
    """
    config = {
        'cache_dir': cache_dir,
        'use_cache': use_cache,
        'theme_config': theme_config,
        'highlight_style': highlight_style or 'pygments',
        'crossref_config': crossref_config,
        'glossary_file': glossary_file,
        'css_file': css_file,
        'verbose': verbose,
        'profile': profile,
    }
    
    # Remove None values
    config = {k: v for k, v in config.items() if v is not None}
    
    if verbose:
        print(f"\nConverting {md_file} to HTML...")
    
    try:
        success = process_document(
            input_file=md_file,
            output_file=output_html,
            output_format=OutputFormat.HTML,
            **config
        )
        
        if success and verbose:
            print(f"[OK] Created: {output_html}")
        
        return success
        
    except Exception as e:
        if verbose:
            print(f"[ERROR] HTML conversion failed: {e}")
        return False


def batch_convert(
    input_files: List[str],
    output_format: str = 'pdf',
    verbose: bool = False,
    **kwargs
) -> Dict[str, bool]:
    """
    Batch convert multiple Markdown files (sequential).
    
    For parallel processing, use cli.parallel_batch_convert().
    
    Args:
        input_files: List of input Markdown file paths
        output_format: Output format ('pdf', 'docx', 'html')
        verbose: Verbose output
        **kwargs: Additional arguments passed to converter
    
    Returns:
        Dictionary mapping input files to success status
    """
    results = {}
    
    format_map = {
        'pdf': markdown_to_pdf,
        'docx': markdown_to_docx,
        'html': markdown_to_html
    }
    
    converter = format_map.get(output_format.lower())
    if not converter:
        raise ValueError(f"Unsupported output format: {output_format}")
    
    for input_file in input_files:
        input_path = Path(input_file)
        if not input_path.exists():
            print(f"[ERROR] File not found: {input_file}")
            results[input_file] = False
            continue
        
        output_file = str(input_path.with_suffix(f'.{output_format.lower()}'))
        
        if verbose:
            print(f"\n{'='*70}")
            print(f"Converting: {input_file}")
            print(f"Output: {output_file}")
            print(f"{'='*70}")
        
        try:
            success = converter(input_file, output_file, verbose=verbose, **kwargs)
            results[input_file] = success
        except Exception as e:
            print(f"[ERROR] Exception during conversion: {e}")
            results[input_file] = False
    
    # Summary
    if verbose:
        total = len(results)
        succeeded = sum(1 for s in results.values() if s)
        failed = total - succeeded
        print(f"\n{'='*70}")
        print(f"BATCH SUMMARY: {succeeded}/{total} succeeded, {failed} failed")
        print(f"{'='*70}\n")
    
    return results

