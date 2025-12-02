#!/usr/bin/env python3
"""
Professional Markdown to PDF with Mermaid pre-rendering
Pandoc + WeasyPrint + mermaid-cli

REFACTORED VERSION using SOLID principles:
- External tools abstracted (PandocExecutor, MermaidCLI, etc.)
- Diagram rendering follows Open/Closed Principle
- Platform-independent executable resolution
- Testable components
"""
import os
import re
from pathlib import Path
import tempfile
import yaml
from datetime import datetime
from typing import Optional, Dict, Any

# Add MSYS2 GTK to PATH for WeasyPrint (Windows-specific)
if os.name == 'nt':
    msys_path = r'C:\msys64\mingw64\bin'
    if Path(msys_path).exists():
        os.environ['PATH'] = f'{msys_path};' + os.environ['PATH']

from weasyprint import HTML, CSS

# Import our new SOLID-compliant modules
from external_tools import PandocExecutor, KatexCLI, ToolNotFoundError
from diagram_rendering import DiagramOrchestrator, DiagramCache, DiagramFormat


def extract_metadata(md_content: str) -> tuple[Dict[str, Any], str]:
    """Extract YAML frontmatter from Markdown"""
    if md_content.startswith('---'):
        parts = md_content.split('---', 2)
        if len(parts) >= 3:
            try:
                metadata = yaml.safe_load(parts[1])
                content = parts[2].strip()
                return metadata if metadata else {}, content
            except:
                pass
    return {}, md_content


def _validate_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize metadata fields to prevent PDF generation errors.
    
    Args:
        metadata: Dictionary of metadata fields
        
    Returns:
        Sanitized metadata dictionary
    """
    if not metadata:
        return {}
    
    validated = metadata.copy()
    
    # Sanitize version field
    if 'version' in validated and validated['version']:
        validated['version'] = re.sub(r'[<>]', '', str(validated['version']))
    
    # Validate date format (allow freeform, but try to parse if structured)
    if 'date' in validated and validated['date']:
        date_str = str(validated['date'])
        try:
            for fmt in ['%B %Y', '%Y-%m-%d', '%m/%d/%Y', '%d %B %Y']:
                try:
                    datetime.strptime(date_str, fmt)
                    break
                except ValueError:
                    continue
        except:
            pass  # Allow freeform dates
    
    # Sanitize classification
    if 'classification' in validated and validated['classification']:
        validated['classification'] = str(validated['classification']).strip().upper()
    
    # Ensure all string fields are properly encoded
    for key in ['title', 'author', 'organization', 'type']:
        if key in validated and validated[key]:
            validated[key] = str(validated[key]).strip()
    
    return validated


def expand_glossary(md_content: str, glossary_file: Optional[Path]) -> str:
    """Expand glossary terms and acronyms in markdown content"""
    if not glossary_file or not Path(glossary_file).exists():
        return md_content
    
    try:
        with open(glossary_file, 'r', encoding='utf-8') as f:
            glossary_data = yaml.safe_load(f)
        
        if not glossary_data:
            return md_content
        
        # Expand acronyms
        acronyms = glossary_data.get('acronyms', {})
        for acronym, expansion in acronyms.items():
            pattern = r'\b' + re.escape(acronym) + r'\b'
            replacement = f'{expansion} ({acronym})'
            md_content = re.sub(pattern, replacement, md_content, flags=re.IGNORECASE)
        
        # Add glossary appendix
        terms = glossary_data.get('terms', {})
        if terms:
            glossary_appendix = '\n\n## Glossary\n\n'
            for term, definition in sorted(terms.items()):
                glossary_appendix += f'**{term}**: {definition}\n\n'
            md_content += glossary_appendix
        
        return md_content
    except Exception as e:
        print(f"    ! Warning: Glossary expansion failed: {e}")
        return md_content


def render_math_with_katex(md_content: str, work_dir: Path) -> str:
    """
    Pre-render math with KaTeX server-side before Pandoc.
    Uses the new KatexCLI wrapper.
    """
    try:
        katex_cli = KatexCLI()
    except ToolNotFoundError:
        # KaTeX not available - return original content
        return md_content
    
    # Pattern: $inline$ or $$display$$
    math_pattern = r'\$\$([^\$]+)\$\$|\$([^\$]+)\$'
    
    def replace_math(match):
        is_display = match.group(1) is not None
        math_code = match.group(1) or match.group(2)
        
        try:
            if is_display:
                html_output = katex_cli.render_display(math_code)
            else:
                html_output = katex_cli.render_inline(math_code)
            
            if html_output:
                if is_display:
                    return f'<div class="math-display">{html_output}</div>'
                else:
                    return f'<span class="math-inline">{html_output}</span>'
        except Exception:
            pass
        
        # Fallback to original
        return match.group(0)
    
    return re.sub(math_pattern, replace_math, md_content)


def markdown_to_pdf(
    md_file: Path,
    output_pdf: Path,
    logo_path: Optional[Path] = None,
    css_file: Optional[Path] = None,
    cache_dir: Optional[Path] = None,
    use_cache: bool = True,
    theme_config: Optional[Path] = None,
    highlight_style: Optional[str] = None,
    crossref_config: Optional[Path] = None,
    glossary_file: Optional[Path] = None,
    renderer: str = 'weasyprint',
    generate_toc: bool = False,
    generate_cover: bool = False,
    watermark: Optional[str] = None,
    verbose: bool = False,
    profile: Optional[str] = None,
    custom_metadata: Optional[Dict[str, Any]] = None
):
    """
    Convert Markdown to PDF via Pandoc + WeasyPrint/Playwright.
    
    REFACTORED: Now uses SOLID-compliant external_tools and diagram_rendering modules.
    
    Args:
        md_file: Path to input Markdown file
        output_pdf: Path to output PDF file
        logo_path: Optional path to logo image
        css_file: Optional path to external CSS file
        cache_dir: Optional cache directory for diagrams
        use_cache: If True, use cached diagrams when available
        theme_config: Optional path to Mermaid theme config JSON
        highlight_style: Code highlighting style
        crossref_config: Optional pandoc-crossref config
        glossary_file: Optional glossary YAML file
        renderer: PDF renderer ('weasyprint' or 'playwright')
        generate_toc: Generate table of contents
        generate_cover: Generate cover page
        watermark: Optional watermark text
        verbose: Verbose output
        profile: Optional profile name
        custom_metadata: Optional metadata overrides
    """
    
    # Apply profile defaults
    if profile:
        try:
            from profiles import get_profile
            profile_obj = get_profile(profile)
            if profile_obj:
                if css_file is None and profile_obj.css:
                    css_file = profile_obj.css
                if logo_path is None and profile_obj.logo:
                    logo_path = profile_obj.logo
                if theme_config is None and profile_obj.theme_config:
                    theme_config = profile_obj.theme_config
        except ImportError:
            pass
    
    # Resolve logo path with environment variable support
    if logo_path is None:
        env_logo = os.environ.get('DOC_LOGO_PATH')
        if env_logo and Path(env_logo).exists():
            logo_path = Path(env_logo)
        else:
            possible_logos = [
                Path.home() / 'Documents' / 'logo.png',
                Path(__file__).parent.parent / 'docs' / 'logo.png',
            ]
            for loc in possible_logos:
                if loc.exists():
                    logo_path = loc
                    break
    
    md_path = Path(md_file)
    output_path = Path(output_pdf)
    
    print(f"\nConverting {md_file}...")
    
    # Create work directory
    work_dir = Path(tempfile.mkdtemp(prefix='pdf_'))
    
    try:
        # Step 0: Extract and merge metadata
        md_content = md_path.read_text(encoding='utf-8')
        metadata, md_content_clean = extract_metadata(md_content)
        
        if not metadata:
            md_content_clean = md_content
            metadata = {}
        
        # Merge custom_metadata (CLI overrides)
        if custom_metadata:
            metadata = {**metadata, **custom_metadata}
        
        # Validate metadata
        metadata = _validate_metadata(metadata)
        
        # Apply defaults with environment variable support
        if not metadata.get('author'):
            metadata['author'] = os.environ.get('USER_NAME', 'Author Name')
        if not metadata.get('organization'):
            metadata['organization'] = os.environ.get('ORGANIZATION', 'Organization')
        if not metadata.get('date'):
            metadata['date'] = datetime.now().strftime('%B %Y')
        if not metadata.get('version'):
            metadata['version'] = '1.0'
        if not metadata.get('classification'):
            metadata['classification'] = ''
        if not metadata.get('type'):
            metadata['type'] = 'Technical Document'
        
        # Step 0.5: Expand glossary
        if glossary_file:
            print("  [0.5/5] Expanding glossary terms...")
            md_content_clean = expand_glossary(md_content_clean, Path(glossary_file))
        
        # Step 0.6: Pre-render math with KaTeX
        if '$' in md_content_clean:
            print("  [0.6/5] Pre-rendering math equations with KaTeX...")
            try:
                md_content_clean = render_math_with_katex(md_content_clean, work_dir)
            except Exception as e:
                print(f"    ! Warning: Math rendering failed ({e}), continuing with raw LaTeX")
        
        # Step 1: Pre-render diagrams using DiagramOrchestrator (NEW!)
        print("  [1/5] Pre-rendering diagrams to SVG...")
        
        # Initialize diagram orchestrator with cache
        cache = DiagramCache(cache_dir) if use_cache else None
        orchestrator = DiagramOrchestrator(
            cache=cache,
            theme_config=Path(theme_config) if theme_config else None,
            optimize_svg=True
        )
        
        # Process markdown to render all diagrams
        md_with_diagrams, rendered_files = orchestrator.process_markdown(
            md_content_clean,
            work_dir,
            output_format=DiagramFormat.SVG
        )
        
        # Save preprocessed markdown
        tmp_md = work_dir / 'preprocessed.md'
        tmp_md.write_text(md_with_diagrams, encoding='utf-8')
        
        # Step 2: Pandoc conversion using PandocExecutor (NEW!)
        print(f"  [2/5] Pandoc parsing Markdown ({len(rendered_files)} diagrams embedded)...")
        tmp_html = work_dir / 'output.html'
        
        # Initialize Pandoc executor
        try:
            pandoc = PandocExecutor()
        except ToolNotFoundError as e:
            raise RuntimeError(f"Pandoc not found: {e}")
        
        # Convert to HTML using the new PandocExecutor API
        extensions = pandoc.get_default_markdown_extensions()
        success = pandoc.convert_markdown_to_html(
            tmp_md,
            tmp_html,
            extensions=extensions,
            highlight_style=highlight_style or 'pygments',
            resource_path=work_dir,
            extra_args=['--filter', 'pandoc-crossref'] if crossref_config and Path(crossref_config).exists() else None
        )
        
        if not success:
            raise RuntimeError("Pandoc conversion failed")
        
        # Step 2.5: Strip Pandoc's embedded CSS
        print("  [2.5/5] Stripping Pandoc's embedded CSS...")
        html_content = tmp_html.read_text(encoding='utf-8')
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
        tmp_html.write_text(html_content, encoding='utf-8')
        
        # Step 3-4: Post-process HTML and generate PDF
        # (Keep existing logic for title page injection, metadata, etc.)
        # This part remains largely the same as it's UI/presentation logic
        
        if renderer == 'playwright':
            print("  [3/5] HTML ready for Playwright formatting...")
            # Inject metadata as HTML meta tags
            html_content = tmp_html.read_text(encoding='utf-8')
            meta_tags = []
            for key in ['title', 'author', 'organization', 'date', 'version', 'type', 'classification']:
                if metadata.get(key):
                    meta_tags.append(f'<meta name="{key}" content="{metadata[key]}" />')
            
            if meta_tags:
                meta_html = '\n    '.join(meta_tags)
                if '<head>' in html_content:
                    html_content = html_content.replace('<head>', f'<head>\n    {meta_html}', 1)
                tmp_html.write_text(html_content, encoding='utf-8')
            
            # Call Playwright renderer
            print("  [4/5] Playwright generating professional PDF...")
            try:
                import sys
                sys.path.insert(0, str(Path(__file__).parent))
                from pdf_playwright import generate_pdf_from_html
                import asyncio
                
                success = asyncio.run(generate_pdf_from_html(
                    str(tmp_html),
                    str(output_path),
                    title=metadata.get("title", "Document"),
                    author=metadata.get("author"),
                    organization=metadata.get("organization"),
                    date=metadata.get("date"),
                    version=metadata.get("version"),
                    doc_type=metadata.get("type"),
                    classification=metadata.get("classification"),
                    logo_path=str(logo_path) if logo_path and logo_path.exists() else None,
                    generate_toc=generate_toc,
                    generate_cover=generate_cover,
                    watermark=watermark,
                    css_file=str(css_file) if css_file else None,
                    verbose=verbose
                ))
                
                if success:
                    print(f"[OK] Created: {output_pdf}")
                else:
                    raise Exception("Playwright PDF generation failed")
            except Exception as e:
                print(f"[WARN] Playwright failed ({e}), falling back to WeasyPrint")
                renderer = 'weasyprint'
        
        if renderer == 'weasyprint':
            print("  [3/4] Structuring document with logo...")
            # (Keep existing WeasyPrint title page injection logic)
            # This is UI/presentation code, not a SOLID violation
            html_content = tmp_html.read_text(encoding='utf-8')
            
            # Build title page (existing logic preserved)
            if logo_path and logo_path.exists():
                logo_url = logo_path.resolve().as_uri()
                logo_html = f'<div class="logo"><img src="{logo_url}" alt="[Organization Name]" /></div>\n'
            else:
                logo_html = ''
            
            title_match = re.search(r'<h1[^>]*>(.+?)</h1>', html_content)
            doc_title = title_match.group(1) if title_match else "Technical Specification"
            
            # Build title page HTML (existing logic)
            title_page_html = f'''<header class="title-page">
{logo_html}
<div class="title-block">
    <h1 class="doc-title">{doc_title}</h1>
    <p class="doc-type">{metadata.get("type", "Technical Document")}</p>
</div>
<div class="metadata-block">
    <p><strong>Author:</strong> {metadata.get("author", "")}</p>
    <p><strong>Organization:</strong> {metadata.get("organization", "")}</p>
    <p><strong>Date:</strong> {metadata.get("date", "")}</p>
    <p><strong>Version:</strong> {metadata.get("version", "")}</p>
</div>
</header>'''
            
            html_content = html_content.replace('<body>', f'<body>\n{title_page_html}', 1)
            tmp_html.write_text(html_content, encoding='utf-8')
            
            print("  [4/5] WeasyPrint generating professional PDF...")
            # Use default CSS (can be improved later with CSS abstraction)
            HTML(filename=str(tmp_html)).write_pdf(str(output_path))
            print(f"[OK] Created: {output_pdf}")
        
    except Exception as e:
        print(f"[ERROR] Conversion failed: {e}")
        raise
    finally:
        # Cleanup
        import shutil
        shutil.rmtree(work_dir, ignore_errors=True)


# Keep markdown_to_docx and markdown_to_html functions
# (Will refactor these next using the same pattern)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        md_file = sys.argv[1]
        pdf_file = sys.argv[2] if len(sys.argv) > 2 else str(Path(md_file).with_suffix('.pdf'))
        markdown_to_pdf(Path(md_file), Path(pdf_file))

