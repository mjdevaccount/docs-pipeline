#!/usr/bin/env python3
"""
Professional Markdown to PDF/DOCX Converter
===========================================

A reusable CLI wrapper for converting Markdown documents to professional PDFs or DOCX
using Pandoc + WeasyPrint + Mermaid-CLI.

Usage:
    python md2pdf.py <input.md> [output.pdf|output.docx]
    python md2pdf.py <input.md> --format pdf|docx
    python md2pdf.py --batch <file1.md> <file2.md> ...
    python md2pdf.py --config config.json

Features:
    - Pre-renders Mermaid diagrams (SVG for PDF, PNG for DOCX)
    - Extracts YAML frontmatter for dynamic title pages
    - Professional typography and page layout
    - Automatic table of contents
    - Running headers and page numbering (PDF)
    - Company logo support (PDF)
    - DOCX output with optional reference template
"""
import sys
import os
from pathlib import Path

# Support standalone execution: add current directory to path for local imports
# Check if running as script (not as module)
_script_file = Path(__file__).resolve()
_script_dir = _script_file.parent
if str(_script_dir) not in sys.path:
    sys.path.insert(0, str(_script_dir))

import argparse
import json
import logging
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Optional

# Try to import colorama for colored output
try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    OK = Fore.GREEN + "[OK]" + Style.RESET_ALL
    WARN = Fore.YELLOW + "[WARN]" + Style.RESET_ALL
    ERR = Fore.RED + "[ERROR]" + Style.RESET_ALL
    INFO = Fore.CYAN + "[INFO]" + Style.RESET_ALL
except ImportError:
    OK = "[OK]"
    WARN = "[WARN]"
    ERR = "[ERROR]"
    INFO = "[INFO]"

# Import the conversion functions from convert_final
try:
    from .convert_final import markdown_to_pdf, markdown_to_docx, markdown_to_html, extract_metadata, get_cache_dir
except ImportError:
    # Fallback for standalone execution
    from convert_final import markdown_to_pdf, markdown_to_docx, markdown_to_html, extract_metadata, get_cache_dir

# Optional: document profiles (brand/layout presets)
try:
    from .profiles import get_profile
except ImportError:
    try:
        from profiles import get_profile
    except ImportError:
        # When imported as a module or run from a different CWD, local import may fail.
        # In that case, profile support is simply unavailable.
        get_profile = None

# Version
__version__ = "2.0.0"

def find_pandoc():
    """Find Pandoc executable"""
    # Common Windows locations
    windows_paths = [
        r'C:\Program Files\Pandoc\pandoc.exe',
        r'C:\Program Files (x86)\Pandoc\pandoc.exe',
    ]
    
    for path in windows_paths:
        if Path(path).exists():
            return path
    
    # Try PATH
    import shutil
    if shutil.which('pandoc'):
        return 'pandoc'
    
    return None

def find_mermaid_cli():
    """Find Mermaid-CLI executable"""
    # Common Windows npm global location
    windows_paths = [
        Path.home() / r'AppData\Roaming\npm\mmdc.cmd',
        Path.home() / r'AppData\Roaming\npm\mmdc',
    ]
    
    for path in windows_paths:
        if Path(path).exists():
            return str(path)
    
    # Try PATH
    import shutil
    if shutil.which('mmdc'):
        return 'mmdc'
    if shutil.which('mmdc.cmd'):
        return 'mmdc.cmd'
    
    return None

def check_dependencies():
    """Check if all required dependencies are available"""
    errors = []
    warnings = []
    
    # Check Pandoc
    pandoc = find_pandoc()
    if not pandoc:
        errors.append("Pandoc not found. Install from https://pandoc.org/installing.html")
    else:
        print(f"{OK} Pandoc found: {pandoc}")
    
    # Check Mermaid-CLI
    mmdc = find_mermaid_cli()
    if not mmdc:
        warnings.append("Mermaid-CLI not found. Diagrams will not render.")
        warnings.append("  Install: npm install -g @mermaid-js/mermaid-cli")
    else:
        print(f"{OK} Mermaid-CLI found: {mmdc}")
    
    # Check Python packages
    try:
        import weasyprint
        print(f"{OK} WeasyPrint {weasyprint.__version__}")
    except ImportError:
        errors.append("WeasyPrint not installed. Run: pip install -r requirements-pdf.txt")
    
    try:
        import yaml
        print(f"{OK} PyYAML installed")
    except ImportError:
        errors.append("PyYAML not installed. Run: pip install -r requirements-pdf.txt")
    
    # Check GTK (Windows only)
    if sys.platform == 'win32':
        gtk_path = Path(r'C:\msys64\mingw64\bin\libgobject-2.0-0.dll')
        if not gtk_path.exists():
            warnings.append("GTK runtime not found. WeasyPrint may fail on Windows.")
            warnings.append("  Install MSYS2: choco install msys2-installer")
            warnings.append("  Then: pacman -S mingw-w64-x86_64-gtk3")
            warnings.append("  Add C:\\msys64\\mingw64\\bin to PATH")
        else:
            print(f"{OK} GTK runtime found")
    
    if errors:
        print(f"\n{ERR} Missing required dependencies:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    if warnings:
        print(f"\n{WARN} Optional dependencies missing:")
        for warning in warnings:
            print(f"  - {warning}")
    
    return True

def load_config(config_file):
    """Load configuration from JSON file"""
    with open(config_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def find_default_reference_docx():
    """Find default reference DOCX template in common locations"""
    project_root = Path(__file__).parent.parent
    possible_locations = [
        project_root / 'pdf' / 'default_reference.docx',
        project_root / 'pdf' / 'reference.docx',
        project_root / 'reference.docx',
        project_root / 'default_reference.docx',
    ]
    
    for loc in possible_locations:
        if loc.exists():
            return str(loc)
    return None

def setup_logging(log_file=None, verbose=False):
    """Setup logging for automation/CI"""
    level = logging.DEBUG if verbose else logging.INFO
    handlers = [logging.StreamHandler()]
    
    if log_file:
        handlers.append(logging.FileHandler(log_file))
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=handlers
    )
    return logging.getLogger(__name__)

def detect_format(output_file, format_hint=None):
    """Detect output format from file extension or format hint
    
    Returns:
        Tuple of (format, corrected_output_file) - corrected_output_file may differ if mismatch detected
    """
    if format_hint:
        # If format hint provided, use it and potentially correct extension
        if output_file:
            ext = Path(output_file).suffix.lower()
            expected_ext = f'.{format_hint}'
            if ext != expected_ext:
                # Warn and correct
                corrected = str(Path(output_file).with_suffix(expected_ext))
                print(f"{WARN} Extension mismatch: {ext} vs format {format_hint}, using {corrected}")
                return format_hint, corrected
        return format_hint, output_file
    
    if not output_file:
        return 'pdf', None  # Default
    
    ext = Path(output_file).suffix.lower()
    if ext == '.docx':
        return 'docx', output_file
    elif ext == '.html' or ext == '.htm':
        return 'html', output_file
    elif ext == '.pdf':
        return 'pdf', output_file
    else:
        return 'pdf', output_file  # Default to PDF

def validate_markdown(md_file, verbose=False):
    """Validate Markdown file and YAML frontmatter
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    warnings = []
    
    try:
        md_path = Path(md_file)
        if not md_path.exists():
            return False, [f"File not found: {md_file}"]
        
        md_content = md_path.read_text(encoding='utf-8')
        
        # Validate YAML frontmatter
        if md_content.startswith('---'):
            try:
                metadata, _ = extract_metadata(md_content)
                
                # Check for common required fields (optional validation)
                if not metadata.get('title'):
                    warnings.append("No 'title' field in frontmatter")
                
                # Validate date format if present
                date_val = metadata.get('date')
                if date_val and isinstance(date_val, str):
                    # Basic date validation (can be enhanced)
                    pass
                
                # Check for recommended fields
                recommended_fields = ['author', 'organization', 'date', 'version']
                for field in recommended_fields:
                    if field not in metadata:
                        warnings.append(f"Missing recommended field: '{field}'")
                    
            except Exception as e:
                errors.append(f"Invalid YAML frontmatter: {e}")
        else:
            warnings.append("No YAML frontmatter found (optional but recommended)")
        
        # Basic Markdown validation
        if not md_content.strip():
            errors.append("Markdown file is empty")
        
        # Check for common issues
        mermaid_blocks = md_content.count('```mermaid')
        code_blocks = md_content.count('```')
        if mermaid_blocks > 0 and (code_blocks % 2) != 0:
            warnings.append("Possible mismatched code block delimiters")
        
        # Check for broken image references
        import re
        broken_images = re.findall(r'!\[.*?\]\([^)]+\)', md_content)
        for img in broken_images:
            # Extract path
            match = re.search(r'\(([^)]+)\)', img)
            if match:
                img_path = match.group(1)
                # Skip if it's a data URI or URL
                if not img_path.startswith(('http://', 'https://', 'data:')):
                    # Check if relative path might be broken (basic check)
                    pass  # Could enhance this
        
        return len(errors) == 0, errors + warnings
        
    except Exception as e:
        return False, [f"Validation error: {e}"]


def get_default_output_root() -> Path:
    """
    Return the default root directory for generated documents.

    Priority:
    1. DOCS_OUTPUT_ROOT environment variable (if set)
    2. <repo_root>/output (repo-relative output folder)
    """
    env_root = os.environ.get("DOCS_OUTPUT_ROOT")
    if env_root:
        return Path(env_root)

    # Default to output folder in repo root (parent of tools/pdf)
    repo_root = Path(__file__).parent.parent.parent
    output_dir = repo_root / "output"
    
    # Create output directory if it doesn't exist
    output_dir.mkdir(exist_ok=True)
    
    return output_dir


def resolve_output_path(output_file: str, output_dir: Optional[str]) -> str:
    """
    Resolve the final output path for a generated document.

    - If output_file is absolute, it is used as-is.
    - If relative, it is placed under:
        * output_dir, when provided, or
        * the default output root (get_default_output_root()).
    - Ensures the parent directory exists.
    """
    output_path = Path(output_file)

    if output_path.is_absolute():
        target = output_path
    else:
        root = Path(output_dir) if output_dir else get_default_output_root()
        target = root / output_path.name

    target.parent.mkdir(parents=True, exist_ok=True)
    return str(target)

def convert_single_file(task):
    """Wrapper function for parallel processing
    
    Args:
        task: Tuple of (md_file, output_file, output_format, logo, reference_docx, css_file, cache_dir, use_cache, theme_config, highlight_style, crossref_config, glossary_file, renderer)
    
    Returns:
        Tuple of (success: bool, md_file: str, output_file: str, error: str or None)
    """
    md_file, output_file, output_format, logo, reference_docx, css_file, cache_dir, use_cache, theme_config, highlight_style, crossref_config, glossary_file, renderer = task
    
    try:
        common_args = {
            'cache_dir': cache_dir,
            'use_cache': use_cache,
            'theme_config': theme_config,
            'highlight_style': highlight_style,
            'crossref_config': crossref_config,
            'glossary_file': glossary_file
        }
        
        if output_format == 'html':
            markdown_to_html(md_file, output_file, css_file=css_file, **common_args)
        elif output_format == 'docx':
            markdown_to_docx(md_file, output_file, reference_docx=reference_docx, **common_args)
        else:
            markdown_to_pdf(md_file, output_file, logo_path=logo, css_file=css_file, renderer=renderer, verbose=verbose, **common_args)
        return True, md_file, output_file, None
    except Exception as e:
        return False, md_file, output_file, str(e)

def main():
    parser = argparse.ArgumentParser(
        description='Convert Markdown files to professional PDFs or DOCX',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single file (output auto-detected)
  python md2pdf.py docs/report.md
  
  # Single file with custom output
  python md2pdf.py docs/report.md output/report.pdf
  
  # Batch conversion
  python md2pdf.py --batch docs/*.md
  
  # Using config file
  python md2pdf.py --config pdf-config.json

Markdown Syntax:
  - Use YAML frontmatter for document metadata:
    ---
    title: Document Title
    author: Your Name
    organization: Company Name
    date: November 2025
    version: 1.0
    type: Technical Specification
    classification: CONFIDENTIAL
    ---
  
  - Mermaid diagrams are automatically rendered:
    ```mermaid
    graph LR
      A --> B
    ```
  
  - Logo: Place logo.png in docs/ directory (or configure path)
        """
    )
    
    parser.add_argument('input', nargs='?', help='Input Markdown file')
    parser.add_argument('output', nargs='?', help='Output file (PDF or DOCX, optional, auto-detected by extension)')
    parser.add_argument('--format', choices=['pdf', 'docx', 'html'], help='Output format (auto-detected from extension if not specified)')
    parser.add_argument('--batch', nargs='+', metavar='FILE', help='Convert multiple files')
    parser.add_argument('--config', help='JSON config file with file mappings')
    parser.add_argument('--check', action='store_true', help='Check dependencies and exit')
    parser.add_argument('--logo', help='Path to logo image (overrides profile, PDF only)')
    parser.add_argument('--reference-docx', help='Reference DOCX template for custom styling (DOCX only)')
    parser.add_argument('--output-dir', help='Output directory for all generated files')
    parser.add_argument('--log', help='Log file path for automation/CI logging')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output with tracebacks')
    parser.add_argument('--version', action='version', version=f'%(prog)s {__version__}')
    parser.add_argument('--formats', action='store_true', help='List supported output formats')
    parser.add_argument('--css', help='External CSS file for PDF styling (overrides default)')
    parser.add_argument('--cache-diagrams', action='store_true', default=True, help='Enable diagram caching (default: enabled)')
    parser.add_argument('--no-cache', dest='cache_diagrams', action='store_false', help='Disable diagram caching')
    parser.add_argument('--cache-dir', help='Cache directory for diagrams (default: pdf-tools/output/pdf-diagrams/)')
    parser.add_argument('--theme-config', help='Mermaid theme config JSON file (default: pdf-tools/pdf-mermaid-theme.json)')
    parser.add_argument('--threads', type=int, default=1, help='Number of parallel threads for batch processing (default: 1)')
    parser.add_argument('--lint', action='store_true', help='Validate Markdown and YAML frontmatter before conversion')
    parser.add_argument('--highlight-style', help='Code highlighting style (e.g., github, pygments, tango, kate, monochrome). Default: github')
    parser.add_argument('--crossref-config', help='Path to pandoc-crossref config YAML file for cross-references')
    parser.add_argument('--glossary', help='Path to glossary YAML file for term/acronym expansion')
    parser.add_argument('--renderer', choices=['weasyprint', 'playwright'], default='weasyprint',
                       help='PDF renderer: weasyprint (fast, limited SVG) or playwright (perfect SVG, FAANG-grade)')
    parser.add_argument('--generate-cover', action='store_true', help='Generate professional cover page (Playwright only)')
    parser.add_argument('--generate-toc', action='store_true', help='Generate table of contents (Playwright only)')
    parser.add_argument('--watermark', help='Add watermark text (e.g., DRAFT) (Playwright only)')
    parser.add_argument('--profile', help='Document profile name (e.g., project-docs, neutral)')
    
    args = parser.parse_args()
    
    # Setup logging if requested
    logger = setup_logging(args.log, args.verbose) if args.log or args.verbose else None
    
    # List supported formats
    if args.formats:
        print("Supported output formats:")
        print("  - pdf  : Professional PDF with typography, headers, logo")
        print("  - docx : Editable Word document with PNG diagrams")
        print("  - html : Responsive HTML with navigation sidebar, MathJax, search")
        print("\nFeatures:")
        print("  - Math support: LaTeX math blocks ($...$ and $$...$$)")
        print("  - Code highlighting: Syntax highlighting with customizable styles")
        print("  - Cross-references: Figure/table references via pandoc-crossref")
        print("  - Glossary expansion: Automatic acronym/term expansion")
        print("  - Multiple diagram types: Mermaid, PlantUML, Graphviz")
        print("\nPandoc supports many more formats. Run: pandoc --list-output-formats")
        sys.exit(0)
    
    # Check dependencies
    if args.check or not (args.input or args.batch or args.config):
        if not check_dependencies():
            sys.exit(1)
        if args.check:
            sys.exit(0)
        if not (args.input or args.batch or args.config):
            parser.print_help()
            sys.exit(0)
    
    # Handle config file
    if args.config:
        config = load_config(args.config)
        files = config.get('files', [])
        config_logo = config.get('logo', args.logo)
        config_reference = config.get('reference_docx', args.reference_docx) or find_default_reference_docx()
        config_css = config.get('css', args.css)
        config_theme = config.get('theme_config', args.theme_config)
        config_highlight = config.get('highlight_style', args.highlight_style)
        config_crossref = config.get('crossref_config', args.crossref_config)
        config_glossary = config.get('glossary', args.glossary)
        config_renderer = config.get('renderer', args.renderer)
        output_dir = args.output_dir or config.get('output_dir')
        cache_dir = args.cache_dir or config.get('cache_dir')
        use_cache = args.cache_diagrams if args.cache_diagrams is not None else config.get('cache_diagrams', True)
        threads = args.threads or config.get('threads', 1)
        config_profile_name = config.get('profile', args.profile)
        failures = 0
        
        # Prepare file tasks
        file_tasks = []
        for item in files:
            try:
                if isinstance(item, dict):
                    md_file = item['input']
                    output_file = item.get('output', str(Path(md_file).with_suffix('.pdf')))
                    item_logo = item.get('logo', config_logo)
                    item_reference = item.get('reference_docx', config_reference)
                    item_css = item.get('css', config_css)
                    item_theme = item.get('theme_config', config_theme)
                    item_highlight = item.get('highlight_style', config_highlight)
                    item_crossref = item.get('crossref_config', config_crossref)
                    item_glossary = item.get('glossary', config_glossary)
                    item_profile = item.get('profile', config_profile_name)
                    item_format, output_file = detect_format(output_file, item.get('format'))
                else:
                    md_file = item
                    output_file = str(Path(md_file).with_suffix('.pdf'))
                    item_logo = config_logo
                    item_reference = config_reference
                    item_css = config_css
                    item_theme = config_theme
                    item_highlight = config_highlight
                    item_crossref = config_crossref
                    item_glossary = config_glossary
                    item_profile = config_profile_name
                    item_format, output_file = detect_format(output_file)

                # Apply profile defaults if requested and profile support is available
                if item_profile and get_profile is not None:
                    profile = get_profile(item_profile)
                    if profile:
                        if item_logo is None and profile.logo:
                            item_logo = profile.logo
                        if item_css is None and profile.css:
                            item_css = profile.css
                        if item_theme is None and profile.theme_config:
                            item_theme = profile.theme_config
                        if item_reference is None and profile.reference_docx:
                            item_reference = profile.reference_docx
                
                # Apply output directory or default root
                output_file = resolve_output_path(output_file, output_dir)
                
                if not Path(md_file).exists():
                    print(f"{ERR} Not found: {md_file}")
                    failures += 1
                    continue
                
                # Lint if requested
                if args.lint:
                    is_valid, issues = validate_markdown(md_file, args.verbose)
                    if not is_valid:
                        print(f"{ERR} Validation failed for {md_file}:")
                        for issue in issues:
                            print(f"  - {issue}")
                        failures += 1
                        continue
                
                file_tasks.append((md_file, output_file, item_format, item_logo, item_reference, item_css, cache_dir, use_cache, item_theme, item_highlight, item_crossref, item_glossary, config_renderer, item_profile))
                
            except Exception as e:
                failures += 1
                print(f"{ERR} Error preparing {md_file}: {e}")
        
        if failures:
            print(f"\n{ERR} {failures} file(s) failed preparation.")
            sys.exit(1)
        
        # Process files (parallel or sequential)
        if threads > 1 and len(file_tasks) > 1:
            try:
                from tqdm import tqdm
                use_tqdm = True
            except ImportError:
                use_tqdm = False
            
            print(f"\n{INFO} Processing {len(file_tasks)} files with {threads} threads...")
            
            with ThreadPoolExecutor(max_workers=threads) as executor:
                futures = {executor.submit(convert_single_file, task): task for task in file_tasks}
                
                if use_tqdm:
                    for future in tqdm(as_completed(futures), total=len(futures), desc="Converting"):
                        success, md_file, output_file, error = future.result()
                        if not success:
                            failures += 1
                            print(f"\n{ERR} Failed: {md_file} -> {error}")
                else:
                    for future in as_completed(futures):
                        success, md_file, output_file, error = future.result()
                        if success:
                            print(f"{OK} Generated: {output_file}")
                        else:
                            failures += 1
                            print(f"{ERR} Failed: {md_file} -> {error}")
        else:
            # Sequential processing
            for md_file, output_file, item_format, item_logo, item_reference, item_css, cache_dir, use_cache, item_theme, item_highlight, item_crossref, item_glossary, renderer, item_profile in file_tasks:
                try:
                    # Echo metadata
                    md_content = Path(md_file).read_text(encoding='utf-8')
                    metadata, _ = extract_metadata(md_content)
                    if metadata:
                        print(f"\n{INFO} Converting {md_file} -> {output_file}")
                        print(f"  Title: {metadata.get('title', 'N/A')}")
                        print(f"  Author: {metadata.get('author', 'N/A')}")
                        print(f"  Format: {item_format.upper()}")
                    else:
                        print(f"\n{INFO} Converting {md_file} -> {output_file} ({item_format.upper()})")
                    
                    common_args = {
                        'cache_dir': cache_dir,
                        'use_cache': use_cache,
                        'theme_config': item_theme,
                        'highlight_style': item_highlight,
                        'crossref_config': item_crossref,
                        'glossary_file': item_glossary,
                        'profile': item_profile
                    }
                    if item_format == 'html':
                        markdown_to_html(md_file, output_file, css_file=item_css, **common_args)
                    elif item_format == 'docx':
                        markdown_to_docx(md_file, output_file, reference_docx=item_reference, **common_args)
                    else:
                        markdown_to_pdf(md_file, output_file, logo_path=item_logo, css_file=item_css, renderer=renderer, generate_toc=args.generate_toc, generate_cover=args.generate_cover, watermark=args.watermark, verbose=args.verbose, **common_args)
                    print(f"{OK} Generated: {output_file}")
                    
                except Exception as e:
                    failures += 1
                    print(f"{ERR} Failed to convert {md_file}: {e}")
                    if args.verbose and logger:
                        logger.exception("Conversion failed")
                    elif args.verbose:
                        import traceback
                        traceback.print_exc()
        
        if failures:
            print(f"\n{ERR} {failures} conversion(s) failed.")
            sys.exit(1)
        return
    
    # Handle batch mode
    if args.batch:
        output_format = args.format or 'pdf'
        reference_docx = args.reference_docx or find_default_reference_docx()
        cache_dir = args.cache_dir
        use_cache = args.cache_diagrams
        theme_config = args.theme_config
        highlight_style = args.highlight_style
        crossref_config = args.crossref_config
        glossary_file = args.glossary
        failures = 0
        
        # Prepare file list with validation
        file_tasks = []
        for md_file in args.batch:
            if not Path(md_file).exists():
                print(f"{ERR} Not found: {md_file}")
                failures += 1
                continue
            
            # Lint if requested
            if args.lint:
                is_valid, issues = validate_markdown(md_file, args.verbose)
                if not is_valid:
                    print(f"{ERR} Validation failed for {md_file}:")
                    for issue in issues:
                        print(f"  - {issue}")
                    failures += 1
                    continue
                elif issues:  # Warnings only
                    for issue in issues:
                        print(f"{WARN} {md_file}: {issue}")
            
            if output_format == 'docx':
                output_file = str(Path(md_file).with_suffix('.docx'))
            elif output_format == 'html':
                output_file = str(Path(md_file).with_suffix('.html'))
            else:
                output_file = str(Path(md_file).with_suffix('.pdf'))
            
            # Apply output directory if specified
            output_file = resolve_output_path(output_file, args.output_dir)
            
            file_tasks.append((md_file, output_file, output_format, args.logo, reference_docx, args.css, cache_dir, use_cache, theme_config, highlight_style, crossref_config, glossary_file, args.renderer))
        
        if failures:
            print(f"\n{ERR} {failures} file(s) failed validation.")
            sys.exit(1)
        
        # Parallel or sequential processing
        if args.threads > 1 and len(file_tasks) > 1:
            # Parallel processing with progress bar
            try:
                from tqdm import tqdm
                use_tqdm = True
            except ImportError:
                use_tqdm = False
                print(f"{WARN} tqdm not installed, parallel processing without progress bar")
            
            print(f"\n{INFO} Processing {len(file_tasks)} files with {args.threads} threads...")
            
            with ThreadPoolExecutor(max_workers=args.threads) as executor:
                futures = {executor.submit(convert_single_file, task): task for task in file_tasks}
                
                if use_tqdm:
                    for future in tqdm(as_completed(futures), total=len(futures), desc="Converting"):
                        success, md_file, output_file, error = future.result()
                        if not success:
                            failures += 1
                            print(f"\n{ERR} Failed: {md_file} -> {error}")
                else:
                    for future in as_completed(futures):
                        success, md_file, output_file, error = future.result()
                        if success:
                            print(f"{OK} Generated: {output_file}")
                        else:
                            failures += 1
                            print(f"{ERR} Failed: {md_file} -> {error}")
        else:
            # Sequential processing
            for md_file, output_file, output_format, logo, reference_docx, css_file, cache_dir, use_cache, theme_config, highlight_style, crossref_config, glossary_file, renderer in file_tasks:
                try:
                    # Echo metadata
                    md_content = Path(md_file).read_text(encoding='utf-8')
                    metadata, _ = extract_metadata(md_content)
                    if metadata:
                        print(f"\n{INFO} Converting {md_file} -> {output_file}")
                        print(f"  Title: {metadata.get('title', 'N/A')}")
                        print(f"  Author: {metadata.get('author', 'N/A')}")
                    else:
                        print(f"\n{INFO} Converting {md_file} -> {output_file} ({output_format.upper()})")
                    
                    common_args = {
                        'cache_dir': cache_dir,
                        'use_cache': use_cache,
                        'theme_config': theme_config,
                        'highlight_style': highlight_style,
                        'crossref_config': crossref_config,
                        'glossary_file': glossary_file,
                        'profile': args.profile
                    }
                    if output_format == 'html':
                        markdown_to_html(md_file, output_file, css_file=css_file, **common_args)
                    elif output_format == 'docx':
                        markdown_to_docx(md_file, output_file, reference_docx=reference_docx, **common_args)
                    else:
                        markdown_to_pdf(md_file, output_file, logo_path=logo, css_file=css_file, renderer=args.renderer, generate_toc=args.generate_toc, generate_cover=args.generate_cover, watermark=args.watermark, verbose=args.verbose, **common_args)
                    print(f"{OK} Generated: {output_file}")
                    
                except Exception as e:
                    failures += 1
                    print(f"{ERR} Failed to convert {md_file}: {e}")
                    if args.verbose and logger:
                        logger.exception("Conversion failed")
                    elif args.verbose:
                        import traceback
                        traceback.print_exc()
        
        if failures:
            print(f"\n{ERR} {failures} conversion(s) failed.")
            sys.exit(1)
        return
    
    # Handle single file
    if not args.input:
        parser.print_help()
        sys.exit(1)
    
    md_file = args.input
    if not Path(md_file).exists():
        print(f"{ERR} File not found: {md_file}")
        sys.exit(1)
    
    # Lint if requested
    if args.lint:
        is_valid, issues = validate_markdown(md_file, args.verbose)
        if not is_valid:
            print(f"{ERR} Validation failed:")
            for issue in issues:
                print(f"  - {issue}")
            sys.exit(1)
        elif issues:  # Warnings only
            for issue in issues:
                print(f"{WARN} {issue}")
    
    # Apply profile defaults for single-file mode (CLI arg only)
    if args.profile and get_profile is not None:
        profile = get_profile(args.profile)
        if profile:
            if args.logo is None and profile.logo:
                args.logo = profile.logo
            if args.css is None and profile.css:
                args.css = profile.css
            if args.theme_config is None and profile.theme_config:
                args.theme_config = profile.theme_config
            if args.reference_docx is None and profile.reference_docx:
                args.reference_docx = profile.reference_docx

    # Determine output file and format
    if args.output:
        output_format, output_file = detect_format(args.output, args.format)
    else:
        output_format = args.format or 'pdf'
        if output_format == 'docx':
            output_file = str(Path(md_file).with_suffix('.docx'))
        else:
            output_file = str(Path(md_file).with_suffix('.pdf'))
    
    # Apply output directory or default root
    output_file = resolve_output_path(output_file, args.output_dir)
    
    # Echo metadata
    md_content = Path(md_file).read_text(encoding='utf-8')
    metadata, _ = extract_metadata(md_content)
    if metadata:
        print(f"\n{INFO} Converting {md_file} -> {output_file}")
        print(f"  Title: {metadata.get('title', 'N/A')}")
        print(f"  Author: {metadata.get('author', 'N/A')}")
        print(f"  Organization: {metadata.get('organization', 'N/A')}")
        print(f"  Format: {output_format.upper()}")
    else:
        print(f"\n{INFO} Converting {md_file} -> {output_file} ({output_format.upper()})")
    
    try:
        reference_docx = args.reference_docx or find_default_reference_docx()
        cache_dir = args.cache_dir
        use_cache = args.cache_diagrams
        theme_config = args.theme_config
        highlight_style = args.highlight_style
        crossref_config = args.crossref_config
        glossary_file = args.glossary
        
        common_args = {
            'cache_dir': cache_dir,
            'use_cache': use_cache,
            'theme_config': theme_config,
            'highlight_style': highlight_style,
            'crossref_config': crossref_config,
            'glossary_file': glossary_file,
            'profile': args.profile
        }
        
        if args.profile:
            print(f"  Using profile: {args.profile}")
        if reference_docx and output_format == 'docx':
            print(f"  Using reference template: {reference_docx}")
        if args.css:
            print(f"  Using external CSS: {args.css}")
        if theme_config:
            print(f"  Using Mermaid theme config: {theme_config}")
        if highlight_style:
            print(f"  Using highlight style: {highlight_style}")
        if crossref_config:
            print(f"  Using crossref config: {crossref_config}")
        if glossary_file:
            print(f"  Using glossary file: {glossary_file}")
        if use_cache and cache_dir:
            print(f"  Using cache directory: {cache_dir}")
        
        if output_format == 'html':
            markdown_to_html(md_file, output_file, css_file=args.css, **common_args)
            print(f"\n{OK} HTML generated: {output_file}")
        elif output_format == 'docx':
            markdown_to_docx(md_file, output_file, reference_docx=reference_docx, **common_args)
            print(f"\n{OK} DOCX generated: {output_file}")
        else:
            markdown_to_pdf(md_file, output_file, logo_path=args.logo, css_file=args.css, renderer=args.renderer, generate_toc=args.generate_toc, generate_cover=args.generate_cover, watermark=args.watermark, verbose=args.verbose, **common_args)
            print(f"\n{OK} PDF generated: {output_file}")
    except Exception as e:
        print(f"\n{ERR} Conversion failed: {e}")
        if args.verbose and logger:
            logger.exception("Conversion failed")
        elif args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()

