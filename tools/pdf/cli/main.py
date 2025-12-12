#!/usr/bin/env python3
"""
PDF Generation CLI - Primary Entry Point
=========================================

This is THE command-line interface for the docs-pipeline PDF generation system.

CLI Usage:
    # Recommended (module invocation)
    python -m tools.pdf.cli.main input.md output.pdf
    
    # Direct script
    python tools/pdf/cli/main.py input.md output.pdf
    
    # With options
    python -m tools.pdf.cli.main input.md --profile tech-whitepaper --cover --toc
    
    # Batch with parallel processing
    python -m tools.pdf.cli.main --batch doc1.md doc2.md --threads 4
    
    # With glossary highlighting
    python -m tools.pdf.cli.main input.md --glossary glossary.yaml
    
    # Export to markdown
    python -m tools.pdf.cli.main input.md output.md --format markdown
    
Library Usage:
    from tools.pdf.core import markdown_to_pdf, MarkdownExporter
    markdown_to_pdf('input.md', 'output.pdf', profile='tech-whitepaper')

Glossary Features:
    # Use glossary to highlight terms
    python -m tools.pdf.cli.main doc.md --glossary glossary.yaml
    
    # Generate glossary index
    python -m tools.pdf.cli.glossary_commands index glossary.yaml --output glossary.md

Markdown Export:
    # Export with formatting and metadata
    python -m tools.pdf.cli.main document.md output.md --format markdown
    
    # Export with table of contents
    python -m tools.pdf.cli.main document.md output.md --format markdown --toc

Docker Usage:
    docker-compose run --rm docs-pipeline-web \\
        python -m tools.pdf.cli.main input.md output.pdf --profile tech-whitepaper
"""

import sys
import warnings

# Suppress RuntimeWarning about module import order when running as -m
warnings.filterwarnings('ignore', message='.*found in sys.modules after import of package.*', 
                        category=RuntimeWarning)

import argparse
import logging
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from core import (
    markdown_to_pdf,
    markdown_to_docx,
    markdown_to_html,
    check_dependencies,
    validate_markdown,
    MarkdownExporter,
    MarkdownMetadata,
)
from core.utils import resolve_output_path
from core.glossary_processor import GlossaryProcessor
from diagram_rendering import DiagramOrchestrator

__version__ = "3.2.0"  # Bumped for markdown export support


# Global reference to diagram orchestrator for metrics reporting
_diagram_orchestrator: Optional[DiagramOrchestrator] = None


def set_diagram_orchestrator(orchestrator: DiagramOrchestrator):
    """Set global reference to diagram orchestrator for metrics reporting."""
    global _diagram_orchestrator
    _diagram_orchestrator = orchestrator


def report_cache_metrics(verbose: bool = False):
    """Report cache metrics if verbose and orchestrator is available."""
    global _diagram_orchestrator
    if verbose and _diagram_orchestrator:
        print(_diagram_orchestrator.get_cache_metrics_report())


def report_glossary_metrics(glossary_processor: Optional[GlossaryProcessor], verbose: bool = False):
    """Report glossary metrics if available."""
    if verbose and glossary_processor and glossary_processor.stats:
        print()
        print(glossary_processor.stats.report())


def apply_glossary(content: str, glossary_file: Optional[Path], verbose: bool = False) -> str:
    """
    Apply glossary highlighting to markdown content.
    
    Args:
        content: Markdown content
        glossary_file: Path to glossary YAML/JSON file
        verbose: Verbose output
    
    Returns:
        Markdown content with highlighted glossary terms
    """
    if not glossary_file:
        return content
    
    try:
        glossary_file = Path(glossary_file)
        if not glossary_file.exists():
            print(f"[WARN] Glossary file not found: {glossary_file}")
            return content
        
        processor = GlossaryProcessor(glossary_file)
        highlighted = processor.highlight_terms(content)
        
        if verbose:
            print(f"[INFO] Applied glossary: {glossary_file}")
            print(processor.report())
        
        return highlighted
    
    except Exception as e:
        print(f"[WARN] Failed to apply glossary: {e}")
        return content


def export_to_markdown(
    input_file: str,
    output_file: str,
    include_toc: bool = False,
    extract_metadata: bool = True,
    glossary_file: Optional[str] = None,
    verbose: bool = False
) -> bool:
    """
    Export document to markdown format.
    
    Args:
        input_file: Input markdown file
        output_file: Output markdown file
        include_toc: Generate table of contents
        extract_metadata: Extract document metadata
        glossary_file: Optional glossary file for highlighting
        verbose: Verbose output
    
    Returns:
        True if successful
    """
    try:
        # Read input
        input_path = Path(input_file)
        if not input_path.exists():
            print(f"[ERROR] Input file not found: {input_file}")
            return False
        
        content = input_path.read_text(encoding='utf-8')
        
        # Apply glossary if specified
        if glossary_file:
            content = apply_glossary(content, Path(glossary_file), verbose)
        
        # Export to markdown
        exporter = MarkdownExporter()
        md_content, metadata = exporter.html_to_markdown(
            content,
            include_toc=include_toc,
            extract_metadata=extract_metadata
        )
        
        # Write output
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if verbose:
            print(f"[INFO] Exporting to markdown: {output_file}")
            print(exporter.stats.report())
        
        exporter.export_to_file(
            md_content,
            output_path,
            metadata=metadata,
            include_toc=include_toc,
            verbose=verbose
        )
        
        return True
    
    except Exception as e:
        print(f"[ERROR] Export failed: {e}")
        if verbose:
            import traceback
            traceback.print_exc()
        return False


def load_config(config_file: str) -> dict:
    """Load configuration from JSON file."""
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)


def parallel_batch_convert(
    file_tasks: List[tuple],
    threads: int,
    verbose: bool = False
) -> Dict[str, bool]:
    """
    Parallel batch conversion using ThreadPoolExecutor.
    
    Args:
        file_tasks: List of (input_file, output_file, format, kwargs) tuples
        threads: Number of parallel threads
        verbose: Verbose output
    
    Returns:
        Dictionary mapping input files to success status
    """
    results = {}
    
    # Try to use tqdm for progress bar
    try:
        from tqdm import tqdm
        use_tqdm = True
    except ImportError:
        use_tqdm = False
    
    def convert_task(task):
        input_file, output_file, output_format, kwargs = task
        try:
            format_map = {
                'pdf': markdown_to_pdf,
                'docx': markdown_to_docx,
                'html': markdown_to_html,
                'markdown': lambda i, o, **kw: export_to_markdown(i, o, **kw)
            }
            converter = format_map[output_format]
            success = converter(input_file, output_file, **kwargs)
            return input_file, output_file, success, None
        except Exception as e:
            return input_file, output_file, False, str(e)
    
    print(f"\n[INFO] Processing {len(file_tasks)} files with {threads} threads...")
    
    with ThreadPoolExecutor(max_workers=threads) as executor:
        futures = {executor.submit(convert_task, task): task for task in file_tasks}
        
        if use_tqdm:
            iterator = tqdm(as_completed(futures), total=len(futures), desc="Converting")
        else:
            iterator = as_completed(futures)
        
        for future in iterator:
            input_file, output_file, success, error = future.result()
            results[input_file] = success
            if success:
                if not use_tqdm:
                    print(f"[OK] Generated: {output_file}")
            else:
                print(f"\n[ERROR] Failed: {input_file} -> {error}")
    
    return results


def build_kwargs(args, item_overrides: Optional[Dict] = None, include_markdown_opts: bool = False) -> Dict[str, Any]:
    """Build kwargs dict from CLI args with optional item-level overrides."""
    # Build custom metadata from CLI args
    custom_metadata = {}
    if args.title:
        custom_metadata['title'] = args.title
    if args.author:
        custom_metadata['author'] = args.author
    if args.organization:
        custom_metadata['organization'] = args.organization
    if args.date:
        custom_metadata['date'] = args.date
    if args.doc_version:
        custom_metadata['version'] = args.doc_version
    if args.classification:
        custom_metadata['classification'] = args.classification
    if args.doc_type:
        custom_metadata['type'] = args.doc_type
    
    kwargs = {
        'verbose': args.verbose,
        'use_cache': not args.no_cache,
        'highlight_style': args.highlight,
        'glossary_file': args.glossary,
        'theme_config': args.theme,
        'css_file': args.css,
        'logo_path': args.logo,
        'profile': args.profile,
        'crossref_config': getattr(args, 'crossref_config', None),
        'custom_metadata': custom_metadata if custom_metadata else None
    }
    
    # Add markdown-specific options
    if include_markdown_opts:
        kwargs.update({
            'include_toc': args.toc,
            'extract_metadata': True
        })
    elif args.format == 'pdf':
        kwargs.update({
            'renderer': args.renderer,
            'generate_cover': args.cover,
            'generate_toc': args.toc,
            'watermark': args.watermark
        })
    
    if args.format == 'docx' and args.reference_docx:
        kwargs['reference_docx'] = args.reference_docx
    
    # Apply item-level overrides
    if item_overrides:
        for key, value in item_overrides.items():
            if key not in ('input', 'output', 'format') and value is not None:
                kwargs[key] = value
    
    # Remove None values
    return {k: v for k, v in kwargs.items() if v is not None}


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description='Convert Markdown to PDF/DOCX/HTML/Markdown with advanced features',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Convert single file to PDF
  python -m tools.pdf.cli.main document.md document.pdf
  
  # Export to markdown with formatting
  python -m tools.pdf.cli.main document.md output.md --format markdown --toc
  
  # Show cache metrics and glossary statistics
  python -m tools.pdf.cli.main document.md output.pdf --verbose
  # Output includes:
  #   [INFO] Cache Performance Report
  #     Hit Ratio: 75.0% (3/4)
  #     Time Saved: 2340ms
  #   [INFO] Glossary Processing Report
  #     Terms Found: 45
  
  # Use glossary to highlight terms
  python -m tools.pdf.cli.main document.md --glossary glossary.yaml
  
  # Export to markdown with glossary
  python -m tools.pdf.cli.main document.md output.md --format markdown --glossary glossary.yaml
  
  # Use Playwright renderer with cover page, TOC, and glossary
  python -m tools.pdf.cli.main document.md --renderer playwright --cover --toc --glossary glossary.yaml
  
  # Batch convert with parallel processing
  python -m tools.pdf.cli.main --batch doc1.md doc2.md --threads 4 --glossary glossary.yaml
  
  # Use JSON config for complex batch jobs with glossary
  python -m tools.pdf.cli.main --config batch-config.json
  
  # Validate Markdown before conversion
  python -m tools.pdf.cli.main document.md --lint --verbose
  
  # Override metadata from command line
  python -m tools.pdf.cli.main doc.md --title "My Report" --author "Jane Doe"

Output Formats:
  - pdf (default) - Professional PDF with cover, TOC, custom styling
  - docx - Word document with formatting preserved
  - html - Web-ready HTML
  - markdown - Processed markdown with optional frontmatter and TOC

Markdown Format:
  Export documents to markdown for archival, sharing, or re-processing.
  Preserves:
  - Document structure (headings, lists, tables)
  - Code blocks with syntax highlighting
  - Images and links
  - Optional metadata in YAML frontmatter
  - Optional table of contents

Glossary Features:
  Use --glossary flag to highlight terminology in documents:
  - Automatic term highlighting
  - Cross-reference generation
  - Support for synonyms and variations
  - Category organization
  
  See glossary_commands.py for managing glossaries:
  - python -m tools.pdf.cli.glossary_commands validate glossary.yaml
  - python -m tools.pdf.cli.glossary_commands index glossary.yaml --output glossary.md
  - python -m tools.pdf.cli.glossary_commands search glossary.yaml API

Cache Metrics:
  Use --verbose flag to see cache performance:
  - Hit Ratio: percentage of diagrams served from cache
  - Time Saved: milliseconds saved by caching
  - Size Reduction: percentage size reduction from caching

Config File Format (JSON):
  {
    "files": [
      {"input": "doc1.md", "output": "doc1.pdf", "profile": "tech-whitepaper"},
      {"input": "doc2.md", "format": "markdown", "glossary": "glossary.yaml"}
    ],
    "glossary": "glossary.yaml",
    "profile": "default",
    "renderer": "playwright",
    "threads": 4
  }
        """
    )
    
    # Input/output arguments
    parser.add_argument('input', nargs='?', help='Input Markdown file')
    parser.add_argument('output', nargs='?', help='Output file (auto-detected if omitted)')
    
    # Batch mode
    parser.add_argument('--batch', nargs='+', metavar='FILE', help='Batch convert multiple files')
    parser.add_argument('--config', help='JSON config file for batch conversion')
    parser.add_argument('--format', default='pdf', choices=['pdf', 'docx', 'html', 'markdown'],
                       help='Output format (default: pdf)')
    parser.add_argument('--output-dir', help='Output directory for all generated files')
    parser.add_argument('--threads', type=int, default=1, 
                       help='Parallel threads for batch processing (default: 1)')
    
    # PDF options
    parser.add_argument('--renderer', default='weasyprint', choices=['weasyprint', 'playwright'],
                       help='PDF renderer (default: weasyprint)')
    parser.add_argument('--cover', '--generate-cover', action='store_true',
                       help='Generate cover page')
    parser.add_argument('--toc', '--generate-toc', action='store_true',
                       help='Generate table of contents')
    parser.add_argument('--watermark', help='Add watermark text')
    
    # Styling options
    parser.add_argument('--css', help='Custom CSS file')
    parser.add_argument('--logo', help='Logo image path')
    parser.add_argument('--profile', help='Style profile name')
    parser.add_argument('--highlight', default='pygments',
                       help='Code highlighting style (default: pygments)')
    parser.add_argument('--reference-docx', help='Reference DOCX template (for DOCX output)')
    
    # Processing options
    parser.add_argument('--glossary', help='Glossary YAML/JSON file for term highlighting')
    parser.add_argument('--theme', help='Mermaid theme config JSON')
    parser.add_argument('--crossref-config', help='Pandoc crossref config YAML')
    parser.add_argument('--no-cache', action='store_true', help='Disable diagram caching')
    
    # Metadata overrides
    parser.add_argument('--title', help='Document title (overrides frontmatter)')
    parser.add_argument('--author', help='Author name (overrides frontmatter)')
    parser.add_argument('--organization', '--org', help='Organization name')
    parser.add_argument('--date', help='Document date')
    parser.add_argument('--doc-version', help='Document version')
    parser.add_argument('--classification', help='Classification level')
    parser.add_argument('--doc-type', help='Document type')
    
    # Validation and utilities
    parser.add_argument('--check', action='store_true', help='Check dependencies and exit')
    parser.add_argument('--lint', action='store_true', help='Validate Markdown before conversion')
    parser.add_argument('--log', help='Log file path for CI/automation')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output with metrics')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    
    args = parser.parse_args()
    
    # Setup logging if requested
    if args.log:
        logging.basicConfig(
            level=logging.DEBUG if args.verbose else logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[logging.StreamHandler(), logging.FileHandler(args.log)]
        )
    
    # Check dependencies
    if args.check:
        sys.exit(0 if check_dependencies() else 1)
    
    # Markdown-specific handling
    if args.format == 'markdown':
        if not args.input:
            parser.print_help()
            print("\n[INFO] No input file specified.")
            sys.exit(0)
        
        input_path = Path(args.input)
        if not input_path.exists():
            print(f"[ERROR] Input file not found: {args.input}")
            sys.exit(1)
        
        if args.output:
            output_file = args.output
        else:
            output_file = str(input_path.with_suffix('.md'))
        
        output_file = resolve_output_path(output_file, args.output_dir)
        
        print(f"\nExporting {args.input} to {output_file}...")
        if args.toc:
            print(f"  Table of contents: enabled")
        if args.glossary:
            print(f"  Glossary: {args.glossary}")
        
        success = export_to_markdown(
            args.input,
            output_file,
            include_toc=args.toc,
            glossary_file=args.glossary,
            verbose=args.verbose
        )
        
        if success:
            print(f"[OK] Created: {output_file}")
        sys.exit(0 if success else 1)
    
    # Config file mode
    if args.config:
        config = load_config(args.config)
        files = config.get('files', [])
        threads = args.threads or config.get('threads', 1)
        output_dir = args.output_dir or config.get('output_dir')
        glossary_file = args.glossary or config.get('glossary')
        
        # Build file tasks
        file_tasks = []
        for item in files:
            try:
                if isinstance(item, dict):
                    input_file = item['input']
                    output_format = item.get('format', args.format)
                    output_file = item.get('output', str(Path(input_file).with_suffix(f'.{output_format}')))
                else:
                    input_file = item
                    output_format = args.format
                    output_file = str(Path(input_file).with_suffix(f'.{output_format}'))
                
                output_file = resolve_output_path(output_file, output_dir)
                
                if args.lint:
                    is_valid, issues = validate_markdown(input_file, args.verbose)
                    if not is_valid:
                        print(f"[ERROR] Validation failed for {input_file}:")
                        for issue in issues:
                            print(f"  - {issue}")
                        continue
                
                is_markdown = output_format == 'markdown'
                kwargs = build_kwargs(args, item if isinstance(item, dict) else None, include_markdown_opts=is_markdown)
                # Override glossary if specified in config item
                if 'glossary' in item:
                    kwargs['glossary_file'] = item['glossary']
                elif glossary_file:
                    kwargs['glossary_file'] = glossary_file
                
                file_tasks.append((input_file, output_file, output_format, kwargs))
                
            except Exception as e:
                print(f"[ERROR] Error preparing {input_file}: {e}")
        
        if threads > 1 and len(file_tasks) > 1:
            results = parallel_batch_convert(file_tasks, threads, args.verbose)
        else:
            results = {}
            for input_file, output_file, output_format, kwargs in file_tasks:
                try:
                    format_map = {
                        'pdf': markdown_to_pdf,
                        'docx': markdown_to_docx,
                        'html': markdown_to_html,
                        'markdown': export_to_markdown
                    }
                    success = format_map[output_format](input_file, output_file, **kwargs)
                    results[input_file] = success
                    if success:
                        print(f"[OK] Generated: {output_file}")
                        # Report metrics if verbose
                        report_cache_metrics(args.verbose)
                except Exception as e:
                    results[input_file] = False
                    print(f"[ERROR] Failed: {input_file} -> {e}")
        
        failed = sum(1 for v in results.values() if not v)
        if failed:
            print(f"\n[ERROR] {failed} conversion(s) failed.")
        sys.exit(0 if all(results.values()) else 1)
    
    # Batch mode
    if args.batch:
        file_tasks = []
        for input_file in args.batch:
            if not Path(input_file).exists():
                print(f"[ERROR] Not found: {input_file}")
                continue
            
            if args.lint:
                is_valid, issues = validate_markdown(input_file, args.verbose)
                if not is_valid:
                    print(f"[ERROR] Validation failed for {input_file}:")
                    for issue in issues:
                        print(f"  - {issue}")
                    continue
            
            output_file = str(Path(input_file).with_suffix(f'.{args.format}'))
            output_file = resolve_output_path(output_file, args.output_dir)
            
            is_markdown = args.format == 'markdown'
            kwargs = build_kwargs(args, include_markdown_opts=is_markdown)
            file_tasks.append((input_file, output_file, args.format, kwargs))
        
        if not file_tasks:
            print("[ERROR] No valid files to process.")
            sys.exit(1)
        
        if args.threads > 1 and len(file_tasks) > 1:
            results = parallel_batch_convert(file_tasks, args.threads, args.verbose)
        else:
            results = {}
            for input_file, output_file, output_format, kwargs in file_tasks:
                try:
                    format_map = {
                        'pdf': markdown_to_pdf,
                        'docx': markdown_to_docx,
                        'html': markdown_to_html,
                        'markdown': export_to_markdown
                    }
                    success = format_map[output_format](input_file, output_file, **kwargs)
                    results[input_file] = success
                    if success:
                        print(f"[OK] Generated: {output_file}")
                        # Report metrics if verbose
                        report_cache_metrics(args.verbose)
                except Exception as e:
                    results[input_file] = False
                    print(f"[ERROR] Failed: {input_file} -> {e}")
        
        failed = sum(1 for v in results.values() if not v)
        if failed:
            print(f"\n[ERROR] {failed} conversion(s) failed.")
        sys.exit(0 if all(results.values()) else 1)
    
    # Single file mode
    if not args.input:
        parser.print_help()
        print("\n[INFO] No input file specified.")
        print("[INFO] Use --batch for multiple files, --config for JSON config")
        print("[INFO] Use --glossary to highlight terminology")
        print("[INFO] Use --format markdown to export as markdown")
        sys.exit(0)
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"[ERROR] Input file not found: {args.input}")
        sys.exit(1)
    
    # Lint if requested
    if args.lint:
        is_valid, issues = validate_markdown(args.input, args.verbose)
        if not is_valid:
            print(f"[ERROR] Validation failed:")
            for issue in issues:
                print(f"  - {issue}")
            sys.exit(1)
        elif issues and args.verbose:
            for issue in issues:
                print(f"[WARN] {issue}")
    
    # Determine output file
    if args.output:
        output_file = args.output
    else:
        output_file = str(input_path.with_suffix(f'.{args.format}'))
    
    output_file = resolve_output_path(output_file, args.output_dir)
    
    # Show conversion info
    print(f"\nConverting {args.input} to {output_file}...")
    if args.format == 'pdf':
        print(f"  Renderer: {args.renderer}")
        if args.cover:
            print(f"  Cover page: enabled")
        if args.toc:
            print(f"  Table of contents: enabled")
        if args.profile:
            print(f"  Profile: {args.profile}")
    elif args.format == 'markdown':
        if args.toc:
            print(f"  Table of contents: enabled")
    
    if args.glossary:
        print(f"  Glossary: {args.glossary}")
    
    # Build kwargs and convert
    is_markdown = args.format == 'markdown'
    kwargs = build_kwargs(args, include_markdown_opts=is_markdown)
    
    try:
        if args.format == 'pdf':
            success = markdown_to_pdf(args.input, output_file, **kwargs)
        elif args.format == 'docx':
            success = markdown_to_docx(args.input, output_file, **kwargs)
        elif args.format == 'html':
            success = markdown_to_html(args.input, output_file, **kwargs)
        elif args.format == 'markdown':
            success = export_to_markdown(args.input, output_file, **kwargs)
        else:
            print(f"[ERROR] Unsupported format: {args.format}")
            sys.exit(1)
        
        if success:
            print(f"[OK] Created: {output_file}")
            # Report metrics if verbose
            report_cache_metrics(args.verbose)
        sys.exit(0 if success else 1)
        
    except Exception as e:
        print(f"[ERROR] Conversion failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
