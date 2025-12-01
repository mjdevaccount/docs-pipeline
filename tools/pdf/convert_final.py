#!/usr/bin/env python3
"""
Professional Markdown to PDF with Mermaid pre-rendering
Pandoc + WeasyPrint + mermaid-cli
"""
import subprocess
import os
import re
from pathlib import Path
import tempfile
import hashlib
import yaml

# Add MSYS2 GTK to PATH for WeasyPrint
os.environ['PATH'] = r'C:\msys64\mingw64\bin;' + os.environ['PATH']

from weasyprint import HTML, CSS

def extract_metadata(md_content):
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

def get_cache_dir(cache_location=None):
    """Get or create cache directory for diagrams"""
    if cache_location:
        cache_dir = Path(cache_location)
    else:
        # Default: pdf-tools/output/pdf-diagrams/
        cache_dir = Path(__file__).parent / 'output' / 'pdf-diagrams'
    
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def optimize_svg_file(svg_path):
    """
    Optimize SVG using SVGO (Node.js tool)
    Reduces file size by 30-50% without quality loss
    
    Requires: npm install -g svgo
    """
    import shutil
    svgo_exe = shutil.which('svgo') or 'svgo'
    
    try:
        result = subprocess.run(
            [svgo_exe, '--input', str(svg_path), '--output', str(svg_path), '--multipass'],
            capture_output=True,
            text=True,
            check=True,
            timeout=10
        )
        
        # SVGO reports optimization results in stdout
        if 'optimized' in result.stdout.lower() or result.returncode == 0:
            return True
        
        return False
    except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
        # SVGO not available or failed - silently continue
        return False

def render_math_with_katex(md_content, work_dir):
    """
    Pre-render math with KaTeX server-side before Pandoc
    Converts $inline$ and $$display$$ math to HTML-rendered equations
    
    Requires: npm install -g katex-cli
    """
    # Pattern: $inline$ or $$display$$
    math_pattern = r'\$\$([^\$]+)\$\$|\$([^\$]+)\$'
    
    def replace_math(match):
        is_display = match.group(1) is not None
        math_code = match.group(1) or match.group(2)
        
        # Find katex executable
        import shutil
        katex_exe = shutil.which('katex') or 'katex'
        
        try:
            # Use KaTeX CLI to render
            katex_cmd = [katex_exe]
            if is_display:
                katex_cmd.append('--display-mode')
            
            result = subprocess.run(
                katex_cmd,
                input=math_code,
                text=True,
                capture_output=True,
                timeout=5
            )
            
            if result.returncode == 0:
                # Return HTML-rendered math wrapped in span/div
                html_output = result.stdout.strip()
                if is_display:
                    return f'<div class="math-display">{html_output}</div>'
                else:
                    return f'<span class="math-inline">{html_output}</span>'
            else:
                # Fallback to original if KaTeX fails
                return match.group(0)
        except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired) as e:
            # KaTeX not available or failed - fallback to original
            return match.group(0)
    
    # Replace all math blocks
    md_with_math = re.sub(math_pattern, replace_math, md_content)
    return md_with_math

def render_mermaid_to_svg(md_content, work_dir, also_png=False, cache_dir=None, use_cache=True, theme_config=None):
    """Extract Mermaid blocks, render to SVG (and optionally PNG), replace with image refs
    
    Args:
        md_content: Markdown content with Mermaid blocks
        work_dir: Working directory for temp files
        also_png: If True, also generate PNG versions (for Word compatibility)
        cache_dir: Optional cache directory path (default: pdf-tools/output/pdf-diagrams/)
        use_cache: If True, use cached diagrams when available
        theme_config: Optional path to Mermaid theme config JSON file (default: pdf-tools/pdf-mermaid-theme.json)
    
    Returns:
        Tuple of (markdown_with_images, list_of_svg_files)
    """
    
    svg_files = []
    cache_enabled = use_cache
    
    if cache_enabled:
        cache_path = get_cache_dir(cache_dir)  # Uses default if cache_dir is None
    
    # Determine theme config path
    if theme_config:
        theme_config_path = Path(theme_config)
    else:
        # Default: pdf-tools/pdf-mermaid-theme.json
        theme_config_path = Path(__file__).parent / 'pdf-mermaid-theme.json'
    
    # Check if theme config exists
    use_theme_config = theme_config_path.exists() if theme_config_path else False
    
    def mermaid_to_svg(match):
        mermaid_code = match.group(1).strip()
        
        # Validate that this looks like actual mermaid code
        # Skip blocks that are just image references or invalid content
        mermaid_keywords = ['graph', 'flowchart', 'sequenceDiagram', 'classDiagram', 
                           'stateDiagram', 'erDiagram', 'journey', 'gantt', 'pie',
                           'gitGraph', 'mindmap', 'timeline', 'C4Context', 'C4Container']
        
        # Check if code starts with a markdown image reference or doesn't contain mermaid keywords
        if mermaid_code.startswith('![') or not any(keyword in mermaid_code for keyword in mermaid_keywords):
            print(f"    ! Skipping invalid mermaid block (appears to be image reference or invalid syntax)")
            # Return the original block as a code block so it's visible in output
            return f'```\n[Skipped invalid mermaid block: {mermaid_code[:50]}...]\n```'
        
        # Create hash for unique filename (include PNG flag in hash for cache key)
        cache_key = mermaid_code + ('_png' if also_png else '_svg')
        code_hash = hashlib.md5(cache_key.encode()).hexdigest()[:8]
        
        # Check cache first
        if cache_enabled:
            cached_svg = cache_path / f'{code_hash}.svg'
            cached_png = cache_path / f'{code_hash}.png' if also_png else None
            
            if cached_svg.exists() and (not also_png or (cached_png and cached_png.exists())):
                # Copy from cache to work directory
                work_svg = work_dir / f'diagram_{code_hash}.svg'
                import shutil
                shutil.copy2(cached_svg, work_svg)
                svg_files.append(work_svg)
                
                if also_png and cached_png.exists():
                    work_png = work_dir / f'diagram_{code_hash}.png'
                    shutil.copy2(cached_png, work_png)
                    return f'![Diagram](diagram_{code_hash}.png)'
                else:
                    return f'![Diagram]({work_svg.name})'
        
        # Not in cache, render it
        # Create temp mermaid file
        mmd_file = work_dir / f'diagram_{code_hash}.mmd'
        svg_file = work_dir / f'diagram_{code_hash}.svg'
        
        mmd_file.write_text(mermaid_code, encoding='utf-8')
        
        try:
            # Render using mermaid-cli
            # Show first few lines of diagram for debugging
            diagram_preview = mermaid_code.split('\n')[:3]
            print(f"    - Rendering diagram {code_hash} ({diagram_preview[0] if diagram_preview else 'unknown'}...)")
            
            # Find mmdc executable
            mmdc_exe = r'C:\Users\mattj\AppData\Roaming\npm\mmdc.cmd'
            if not Path(mmdc_exe).exists():
                mmdc_exe = 'mmdc'  # Try PATH
            
            # Build SVG rendering command
            # Note: Theme 'base' may not be available in all mermaid-cli versions
            # If theme config is provided, it will override the theme anyway
            svg_cmd = [
                mmdc_exe,
                '-i', str(mmd_file),
                '-o', str(svg_file),
                '-t', 'neutral',  # Use 'neutral' theme (supported by all versions)
                '-b', 'transparent'
            ]
            
            # Add theme config if available (this will apply custom styling)
            if use_theme_config:
                svg_cmd.extend(['-c', str(theme_config_path)])
            
            # Render SVG with better error capture
            result = subprocess.run(svg_cmd, check=False, capture_output=True, text=True, shell=True)
            
            # Check if rendering failed
            if result.returncode != 0:
                error_msg = result.stderr if result.stderr else result.stdout
                # Check if it's a C4Container issue
                if 'C4Container' in mermaid_code or 'C4Context' in mermaid_code:
                    print(f"    ! Warning: C4 diagram detected - may need syntax adjustment")
                    # Try without theme config as C4 diagrams can be sensitive
                    if use_theme_config:
                        print(f"    ! Retrying without theme config...")
                        svg_cmd_no_theme = [
                            mmdc_exe,
                            '-i', str(mmd_file),
                            '-o', str(svg_file),
                            '-t', 'neutral',
                            '-b', 'transparent'
                        ]
                        result = subprocess.run(svg_cmd_no_theme, check=False, capture_output=True, text=True, shell=True)
                        if result.returncode != 0:
                            raise subprocess.CalledProcessError(result.returncode, svg_cmd_no_theme, result.stdout, result.stderr)
                    else:
                        raise subprocess.CalledProcessError(result.returncode, svg_cmd, result.stdout, result.stderr)
                else:
                    raise subprocess.CalledProcessError(result.returncode, svg_cmd, result.stdout, result.stderr)
            
            # Optimize SVG file (if SVGO available)
            if svg_file.exists():
                try:
                    optimize_svg_file(svg_file)
                except Exception:
                    pass  # Optimization is optional
            
            # Optionally render PNG for Word compatibility (high-resolution)
            png_file = None
            if also_png:
                png_file = work_dir / f'diagram_{code_hash}.png'
                png_cmd = [
                    mmdc_exe,
                    '-i', str(mmd_file),
                    '-o', str(png_file),
                    '-t', 'neutral',  # Use 'neutral' theme
                    '-b', 'white',
                    '-s', '2.0'  # Scale factor 2.0 for high-resolution PNG
                ]
                
                # Add theme config if available (this will apply custom styling)
                if use_theme_config:
                    png_cmd.extend(['-c', str(theme_config_path)])
                
                subprocess.run(png_cmd, check=True, capture_output=True, text=True, shell=True)
            
            if svg_file.exists():
                svg_files.append(svg_file)
                
                # Save to cache
                if cache_enabled:
                    import shutil
                    cache_svg = cache_path / f'{code_hash}.svg'
                    shutil.copy2(svg_file, cache_svg)
                    if also_png and png_file and png_file.exists():
                        cache_png = cache_path / f'{code_hash}.png'
                        shutil.copy2(png_file, cache_png)
                
                # Return markdown image syntax (use PNG for Word if available, else SVG)
                if also_png and png_file and png_file.exists():
                    return f'![Diagram](diagram_{code_hash}.png)'
                else:
                    return f'![Diagram]({svg_file.name})'
            else:
                print(f"    ! Warning: SVG not generated for {code_hash}")
                return f'```\n[Diagram placeholder: {code_hash}]\n```'
                
        except subprocess.CalledProcessError as e:
            print(f"    ! Warning: Mermaid rendering failed for {code_hash}: {e.stderr}")
            return f'```\n[Diagram error: {code_hash}]\n```'
    
    # Replace all mermaid blocks with SVG references
    md_with_svgs = re.sub(
        r'```mermaid\n(.+?)```',
        mermaid_to_svg,
        md_content,
        flags=re.DOTALL
    )
    
    return md_with_svgs, svg_files

def render_plantuml_to_svg(plantuml_code, work_dir, code_hash, cache_path=None, use_cache=True):
    """Render PlantUML diagram to SVG"""
    try:
        import shutil
        # Check cache
        if use_cache and cache_path:
            cached_svg = cache_path / f'puml_{code_hash}.svg'
            if cached_svg.exists():
                work_svg = work_dir / f'diagram_puml_{code_hash}.svg'
                shutil.copy2(cached_svg, work_svg)
                return work_svg, True
        
        # Find PlantUML (java -jar plantuml.jar)
        plantuml_jar = Path(__file__).parent / 'plantuml.jar'
        if not plantuml_jar.exists():
            # Try common locations
            possible_locations = [
                Path.home() / 'plantuml.jar',
                Path('C:/tools/plantuml.jar'),
            ]
            for loc in possible_locations:
                if loc.exists():
                    plantuml_jar = loc
                    break
            else:
                return None, False
        
        puml_file = work_dir / f'diagram_puml_{code_hash}.puml'
        svg_file = work_dir / f'diagram_puml_{code_hash}.svg'
        puml_file.write_text(plantuml_code, encoding='utf-8')
        
        # Render: java -jar plantuml.jar -tsvg input.puml
        subprocess.run([
            'java', '-jar', str(plantuml_jar),
            '-tsvg', str(puml_file),
            '-o', str(work_dir)
        ], check=True, capture_output=True, text=True)
        
        if svg_file.exists():
            if use_cache and cache_path:
                shutil.copy2(svg_file, cache_path / f'puml_{code_hash}.svg')
            return svg_file, True
    except Exception as e:
        print(f"    ! Warning: PlantUML rendering failed: {e}")
    return None, False

def render_graphviz_to_svg(dot_code, work_dir, code_hash, cache_path=None, use_cache=True):
    """Render Graphviz/DOT diagram to SVG"""
    try:
        import shutil
        # Check cache
        if use_cache and cache_path:
            cached_svg = cache_path / f'dot_{code_hash}.svg'
            if cached_svg.exists():
                work_svg = work_dir / f'diagram_dot_{code_hash}.svg'
                shutil.copy2(cached_svg, work_svg)
                return work_svg, True
        
        dot_file = work_dir / f'diagram_dot_{code_hash}.dot'
        svg_file = work_dir / f'diagram_dot_{code_hash}.svg'
        dot_file.write_text(dot_code, encoding='utf-8')
        
        # Render: dot -Tsvg input.dot -o output.svg
        subprocess.run([
            'dot', '-Tsvg', str(dot_file), '-o', str(svg_file)
        ], check=True, capture_output=True, text=True)
        
        if svg_file.exists():
            if use_cache and cache_path:
                shutil.copy2(svg_file, cache_path / f'dot_{code_hash}.svg')
            return svg_file, True
    except Exception as e:
        print(f"    ! Warning: Graphviz rendering failed: {e}")
    return None, False

def render_all_diagrams(md_content, work_dir, also_png=False, cache_dir=None, use_cache=True, theme_config=None):
    """Render all diagram types (Mermaid, PlantUML, Graphviz) and replace with image refs"""
    svg_files = []
    cache_path = get_cache_dir(cache_dir) if use_cache else None
    
    # Process Mermaid diagrams
    md_with_mermaid, mermaid_svgs = render_mermaid_to_svg(md_content, work_dir, also_png, cache_dir, use_cache, theme_config)
    svg_files.extend(mermaid_svgs)
    
    # Process PlantUML diagrams
    def plantuml_to_svg(match):
        puml_code = match.group(1).strip()
        code_hash = hashlib.md5(puml_code.encode()).hexdigest()[:8]
        svg_file, success = render_plantuml_to_svg(puml_code, work_dir, code_hash, cache_path, use_cache)
        if success and svg_file:
            svg_files.append(svg_file)
            return f'![Diagram]({svg_file.name})'
        return f'```plantuml\n[PlantUML diagram - rendering failed]\n```'
    
    md_with_puml = re.sub(
        r'```plantuml\n(.+?)```',
        plantuml_to_svg,
        md_with_mermaid,
        flags=re.DOTALL
    )
    
    # Process Graphviz/DOT diagrams
    def graphviz_to_svg(match):
        dot_code = match.group(1).strip()
        code_hash = hashlib.md5(dot_code.encode()).hexdigest()[:8]
        svg_file, success = render_graphviz_to_svg(dot_code, work_dir, code_hash, cache_path, use_cache)
        if success and svg_file:
            svg_files.append(svg_file)
            return f'![Diagram]({svg_file.name})'
        return f'```dot\n[Graphviz diagram - rendering failed]\n```'
    
    md_with_all = re.sub(
        r'```dot\n(.+?)```|```graphviz\n(.+?)```',
        lambda m: graphviz_to_svg(m) if m.group(1) or m.group(2) else m.group(0),
        md_with_puml,
        flags=re.DOTALL
    )
    
    return md_with_all, svg_files

def expand_glossary(md_content, glossary_file=None):
    """Expand glossary terms and acronyms in markdown content"""
    if not glossary_file or not Path(glossary_file).exists():
        return md_content
    
    try:
        with open(glossary_file, 'r', encoding='utf-8') as f:
            glossary_data = yaml.safe_load(f)
        
        if not glossary_data:
            return md_content
        
        # Expand acronyms (e.g., "API" -> "Application Programming Interface (API)")
        acronyms = glossary_data.get('acronyms', {})
        for acronym, expansion in acronyms.items():
            # Match acronym as whole word (case-insensitive)
            pattern = r'\b' + re.escape(acronym) + r'\b'
            replacement = f'{expansion} ({acronym})'
            md_content = re.sub(pattern, replacement, md_content, flags=re.IGNORECASE)
        
        # Add glossary appendix if terms exist
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

def markdown_to_pdf(md_file, output_pdf, logo_path=None, css_file=None, cache_dir=None, use_cache=True, theme_config=None, highlight_style=None, crossref_config=None, glossary_file=None, renderer='weasyprint', generate_toc=False, generate_cover=False, watermark=None, verbose=False, profile=None):
    """Convert Markdown to PDF via Pandoc + WeasyPrint/Playwright with Mermaid pre-rendering
    
    Args:
        md_file: Path to input Markdown file
        output_pdf: Path to output PDF file
        logo_path: Optional path to logo image (default: docs/logo.png)
        css_file: Optional path to external CSS file (overrides default CSS and profile)
        cache_dir: Optional cache directory for diagrams (default: pdf-tools/pdf-diagrams/)
        use_cache: If True, use cached diagrams when available
        theme_config: Optional path to Mermaid theme config JSON file (default: pdf-tools/pdf-mermaid-theme.json)
        renderer: PDF renderer to use ('weasyprint' or 'playwright'). Playwright provides perfect SVG foreignObject support.
        profile: Optional profile name (e.g., 'tech-whitepaper', 'dark-pro', 'minimalist', 'enterprise-blue')
                 Profile provides CSS, theme config, and logo defaults. Explicit arguments override profile settings.
    """
    
    # If profile is specified, use it to set defaults for missing arguments
    if profile:
        try:
            from profiles import get_profile
            profile_obj = get_profile(profile)
            if profile_obj:
                # Only use profile values if explicit arguments not provided
                if css_file is None and profile_obj.css:
                    css_file = profile_obj.css
                if logo_path is None and profile_obj.logo:
                    logo_path = profile_obj.logo
                if theme_config is None and profile_obj.theme_config:
                    theme_config = profile_obj.theme_config
        except ImportError:
            # profiles module not available, continue without profile
            pass
    
    md_path = Path(md_file)
    output_path = Path(output_pdf)
    
    print(f"\nConverting {md_file}...")
    
    # Create work directory for temp files
    work_dir = Path(tempfile.mkdtemp(prefix='pdf_'))
    
    try:
        # Step 0: Extract metadata from frontmatter
        md_content = md_path.read_text(encoding='utf-8')
        metadata, md_content_clean = extract_metadata(md_content)
        
        # If no frontmatter, use original content
        if not metadata:
            md_content_clean = md_content
        
        # Step 0.5: Expand glossary terms and acronyms
        if glossary_file:
            print("  [0.5/5] Expanding glossary terms...")
            md_content_clean = expand_glossary(md_content_clean, glossary_file)
        
        # Step 0.6: Pre-render math with KaTeX (server-side rendering for PDF)
        # Check if document contains math
        if '$' in md_content_clean:
            print("  [0.6/5] Pre-rendering math equations with KaTeX...")
            try:
                md_content_clean = render_math_with_katex(md_content_clean, work_dir)
            except Exception as e:
                print(f"    ! Warning: Math rendering failed ({e}), continuing with raw LaTeX")
        
        # Step 1: Pre-render all diagrams (Mermaid, PlantUML, Graphviz) to SVG
        print("  [1/5] Pre-rendering diagrams to SVG...")
        md_with_svgs, svg_files = render_all_diagrams(md_content_clean, work_dir, also_png=False, cache_dir=cache_dir, use_cache=use_cache, theme_config=theme_config)
        
        # Save preprocessed markdown
        tmp_md = work_dir / 'preprocessed.md'
        tmp_md.write_text(md_with_svgs, encoding='utf-8')
        
        # Step 2: Pandoc: Markdown → HTML
        print(f"  [2/5] Pandoc parsing Markdown ({len(svg_files)} diagrams embedded)...")
        tmp_html = work_dir / 'output.html'
        
        # Find Pandoc executable (robust detection)
        import shutil
        pandoc_exe = None
        
        # Try common Windows locations first
        windows_paths = [
            r'C:\Program Files\Pandoc\pandoc.exe',
            r'C:\Program Files (x86)\Pandoc\pandoc.exe',
            Path.home() / 'AppData' / 'Local' / 'Pandoc' / 'pandoc.exe',
        ]
        
        for path in windows_paths:
            if Path(path).exists():
                pandoc_exe = str(path)
                break
        
        # Fallback to PATH lookup
        if not pandoc_exe:
            pandoc_exe = shutil.which('pandoc')
        
        # Final fallback
        if not pandoc_exe:
            pandoc_exe = 'pandoc'
        
        # Build Pandoc format string with all extensions
        markdown_extensions = [
            'pipe_tables',
            'backtick_code_blocks',
            'fenced_code_attributes',
            'smart',
            'tex_math_dollars',  # Math: $...$ and $$...$$
            'tex_math_double_backslash',  # Math: \[...\] and \(...\)
            'raw_html',  # Allow raw HTML
            'fenced_code_blocks',  # Explicit code blocks
            'autolink_bare_uris',  # Auto-link URLs
            'strikeout',  # ~~strikethrough~~
            'superscript',  # ^superscript^
            'subscript',  # ~subscript~
        ]
        markdown_format = 'markdown+' + '+'.join(markdown_extensions)
        
        pandoc_cmd = [
            pandoc_exe,
            str(tmp_md),
            '-f', markdown_format,
            '-t', 'html5',
            '--standalone',
            '--toc',
            '--toc-depth=3',
            '--resource-path', str(work_dir),
            '--mathjax',  # Use MathJax for math rendering in HTML
            '-o', str(tmp_html)
        ]
        
        # Add code highlighting style if specified
        if highlight_style:
            pandoc_cmd.extend(['--highlight-style', highlight_style])
        else:
            pandoc_cmd.extend(['--highlight-style', 'pygments'])  # Default to pygments style
        
        # Add pandoc-crossref filter if available and config provided
        if crossref_config and Path(crossref_config).exists():
            # Check if pandoc-crossref is available
            import shutil
            crossref_filter = shutil.which('pandoc-crossref') or 'pandoc-crossref'
            pandoc_cmd.extend(['--filter', crossref_filter])
            if Path(crossref_config).exists():
                pandoc_cmd.extend(['--metadata', f'crossrefYaml={crossref_config}'])
        
        subprocess.run(pandoc_cmd, check=True, capture_output=True, text=True, shell=False)
        
        # Step 2.5: Strip Pandoc's embedded CSS to avoid conflicts with profile CSS
        # Pandoc's --standalone flag embeds its own <style> blocks which can interfere
        # with our custom profile CSS and create specificity wars
        print("  [2.5/5] Stripping Pandoc's embedded CSS...")
        html_content = tmp_html.read_text(encoding='utf-8')
        
        # Remove all <style> blocks from Pandoc (preserves inline styles on elements)
        # Use DOTALL flag to match across newlines
        html_content = re.sub(r'<style[^>]*>.*?</style>', '', html_content, flags=re.DOTALL)
        
        # Write cleaned HTML back
        tmp_html.write_text(html_content, encoding='utf-8')
        
        # Step 3: Post-process HTML for proper structure
        # NOTE: For Playwright renderer, skip WeasyPrint-style title page injection
        # Playwright handles cover page, TOC, and formatting separately
        if renderer == 'playwright':
            print("  [3/5] HTML ready for Playwright formatting...")
            # For Playwright, we want clean HTML without WeasyPrint title page
            # Just ensure logo_path is available for Playwright cover page
            if logo_path is None:
                # Default logo path relative to project root (one level up from pdf-tools/)
                logo_path = Path(__file__).parent.parent / 'docs' / 'logo.png'
                logo_path = logo_path.resolve()
            else:
                logo_path = Path(logo_path).resolve()
            
            # Extract document title from HTML for Playwright cover page
            html_content = tmp_html.read_text(encoding='utf-8')
            title_match = re.search(r'<h1[^>]*>(.+?)</h1>', html_content)
            doc_title = title_match.group(1) if title_match else "Technical Specification"
        else:
            # WeasyPrint path: inject title page HTML
            print("  [3/4] Structuring document with logo...")
            html_content = tmp_html.read_text(encoding='utf-8')
            
            # Build professional title page
            if logo_path is None:
                # Default logo path relative to project root (one level up from pdf-tools/)
                logo_path = Path(__file__).parent.parent / 'docs' / 'logo.png'
                logo_path = logo_path.resolve()
            else:
                logo_path = Path(logo_path).resolve()
            
            if logo_path.exists():
                logo_url = logo_path.as_uri()
                logo_html = f'<div class="logo"><img src="{logo_url}" alt="[Organization Name]" /></div>\n'
            else:
                logo_html = ''
            
            # Extract document title from first h1 for title page
            title_match = re.search(r'<h1[^>]*>(.+?)</h1>', html_content)
            doc_title = title_match.group(1) if title_match else "Technical Specification"
            
            # Get metadata with defaults
            author = metadata.get("author", "Matt Jeffcoat")
            organization = metadata.get("organization", "[Organization Name]")
            date = metadata.get("date", "November 2025")
            version = metadata.get("version", "1.0")
            doc_type = metadata.get("type", "Technical Specification")
            classification = metadata.get("classification", "CONFIDENTIAL – INTERNAL USE ONLY")
            
            # Enhanced metadata fields (optional)
            department = metadata.get("department")
            review_status = metadata.get("review_status")
            doc_id = metadata.get("doc_id") or metadata.get("document_id")
            prepared_for = metadata.get("prepared_for") or metadata.get("preparedFor")
            
            # Build metadata block with standard fields
            metadata_items = [
                f'<p><strong>Author:</strong> {author}</p>',
                f'<p><strong>Organization:</strong> {organization}</p>',
                f'<p><strong>Date:</strong> {date}</p>',
                f'<p><strong>Version:</strong> {version}</p>'
            ]
            
            # Add optional enhanced fields if present
            if department:
                metadata_items.append(f'<p><strong>Department:</strong> {department}</p>')
            if review_status:
                metadata_items.append(f'<p><strong>Review Status:</strong> {review_status}</p>')
            if doc_id:
                metadata_items.append(f'<p><strong>Document ID:</strong> {doc_id}</p>')
            if prepared_for:
                metadata_items.append(f'<p><strong>Prepared for:</strong> {prepared_for}</p>')
            
            metadata_block = '\n    '.join(metadata_items)
            
            # Build structured title page
            title_page_html = f'''<header class="title-page">
{logo_html}
<div class="title-block">
    <h1 class="doc-title">{doc_title}</h1>
    <p class="doc-type">{doc_type}</p>
</div>
<div class="classification">
    <p>{classification}</p>
</div>
<div class="metadata-block">
    {metadata_block}
</div>
<div class="disclaimer">
    <p>This document is confidential and intended solely for authorized personnel and approved contractors. Unauthorized distribution is prohibited.</p>
</div>'''
            
            # Wrap title in header with enhanced structure
            html_content = html_content.replace('<body>', f'<body>\n{title_page_html}', 1)
            
            # Hide the duplicate h1 that Pandoc generated (we use it in title block)
            html_content = re.sub(
                r'(<h1[^>]*>.*?</h1>)',
                r'<!-- \1 -->',
                html_content,
                count=1
            )
            
            # Close metadata block and header before TOC
            if '<nav id="TOC"' in html_content:
                html_content = html_content.replace('<nav id="TOC"', '</div></header>\n<nav id="TOC"', 1)
            elif '<div id="TOC"' in html_content:
                html_content = html_content.replace('<div id="TOC"', '</div></header>\n<div id="TOC"', 1)
            else:
                # No TOC, close before first h2
                html_content = html_content.replace('<h2', '</div></header>\n<h2', 1)
            
            tmp_html.write_text(html_content, encoding='utf-8')
        
        # Step 4: Generate PDF using selected renderer
        # Note: CSS loading is renderer-specific to avoid compatibility issues
        
        # Define default WeasyPrint CSS (used when no CSS file provided or when Playwright CSS detected)
        default_weasyprint_css = CSS(string="""
            @page {
                size: A4;
                margin: 25mm 15mm 20mm 15mm;
                @top-left {
                    content: "Project Documentation – Phase 0";
                    font-size: 9pt;
                    color: #666;
                    font-style: italic;
                }
                @top-right {
                    content: string(section-title);
                    font-size: 9pt;
                    color: #666;
                    font-style: italic;
                }
                @bottom-center {
                    content: "[Organization Name] • Confidential • November 2025";
                    font-size: 9pt;
                    color: #888;
                }
                @bottom-right {
                    content: "Page " counter(page);
                    font-size: 9pt;
                    color: #666;
                }
            }
            @page:first {
                @top-left { content: none; }
                @top-right { content: none; }
                @bottom-center { content: none; }
                @bottom-right { content: none; }
            }
            @page toc {
                @bottom-right {
                    content: "Page " counter(page, lower-roman);
                    font-size: 9pt;
                    color: #666;
                }
                @top-left { content: none; }
                @top-right { content: none; }
            }
            body {
                font-family: 'Segoe UI', Arial, sans-serif;
                font-size: 11pt;
                line-height: 1.6;
                color: #000;
                -webkit-font-smoothing: antialiased;
            }
            /* Title page */
            header.title-page {
                page-break-after: always;
                text-align: center;
                padding: 60pt 40pt;
                min-height: 10in; /* A4 page height */
                display: flex;
                flex-direction: column;
                justify-content: center;
            }
            header.title-page .logo {
                margin-bottom: 50pt;
            }
            header.title-page .logo img {
                max-width: 220pt;
                height: auto;
            }
            header.title-page .title-block {
                margin-bottom: 40pt;
            }
            header.title-page .doc-title {
                font-size: 36pt;
                font-weight: 800;
                letter-spacing: 1pt;
                border-bottom: none;
                margin: 0 0 16pt 0;
                color: #1976d2;
                line-height: 1.2;
            }
            header.title-page .doc-type {
                font-size: 18pt;
                color: #4b4b4b;
                font-style: italic;
                margin: 0;
            }
            header.title-page .classification {
                background-color: #fff3e0;
                border: 2pt solid #f57c00;
                padding: 10pt 24pt;
                margin: 32pt auto;
                display: inline-block;
            }
            header.title-page .classification p {
                font-size: 13pt;
                font-weight: bold;
                color: #e65100;
                margin: 0;
                letter-spacing: 1.5pt;
            }
            header.title-page .metadata-block {
                border-top: 2pt solid #1976d2;
                border-bottom: 2pt solid #1976d2;
                padding: 18pt 0;
                margin: 32pt auto;
                max-width: 380pt;
            }
            header.title-page .metadata-block p {
                text-align: center;
                font-size: 12pt;
                margin: 8pt 0;
                line-height: 1.5;
            }
            header.title-page .metadata-block p strong {
                color: #1976d2;
                font-weight: 700;
                display: inline-block;
                min-width: 100pt;
                text-align: right;
                margin-right: 10pt;
            }
            header.title-page .disclaimer {
                margin-top: 40pt;
                font-size: 10pt;
                color: #888;
                font-style: italic;
                max-width: 420pt;
                margin-left: auto;
                margin-right: auto;
                line-height: 1.4;
            }
            header.title-page .disclaimer p {
                margin: 0;
                text-align: center;
            }
            header.title-page hr {
                display: none;
            }
            /* Table of Contents */
            #TOC, nav#TOC {
                page: toc;
                page-break-before: always;
                page-break-after: always;
                padding: 20pt 0;
            }
            #TOC h2, nav#TOC h2 {
                font-size: 20pt;
                text-align: center;
                border-bottom: 2pt solid #000;
                padding-bottom: 10pt;
                margin-bottom: 20pt;
            }
            #TOC ul, nav#TOC ul {
                list-style: none;
                padding-left: 0;
            }
            #TOC li, nav#TOC li {
                margin: 8pt 0;
                padding-left: 20pt;
            }
            #TOC a, nav#TOC a {
                text-decoration: none;
                color: #1976d2;
            }
            /* Content headings */
            h1 {
                font-size: 24pt;
                padding: 16pt 0 12pt 0;
                border-bottom: 3pt solid #000;
                page-break-before: always;
                page-break-after: avoid;
            }
            h2 {
                font-size: 18pt;
                margin-top: 24pt;
                padding-bottom: 6pt;
                border-bottom: 1.5pt solid #999;
                page-break-after: avoid;
                string-set: section-title content();
            }
            h3 {
                font-size: 14pt;
                margin-top: 18pt;
                page-break-after: avoid;
            }
            h4 {
                font-size: 12pt;
                margin-top: 14pt;
            }
            p {
                margin: 6pt 0;
                text-align: justify;
                orphans: 3;
                widows: 3;
            }
            table {
                border-collapse: collapse;
                width: 100%;
                margin: 12pt 0;
                page-break-inside: avoid;
            }
            th, td {
                border: 1pt solid #333;
                padding: 8pt;
                text-align: left;
            }
            th {
                background-color: #f0f0f0;
                font-weight: bold;
            }
            code {
                font-family: 'Consolas', 'Monaco', monospace;
                background-color: #f5f5f5;
                padding: 2pt 4pt;
                font-size: 10pt;
                border-radius: 2pt;
            }
            pre {
                background-color: #f5f5f5;
                border-left: 3pt solid #2196F3;
                padding: 12pt;
                margin: 12pt 0;
                page-break-inside: avoid;
                font-size: 9.5pt;
                overflow-x: auto;
                overflow-wrap: break-word;
                word-wrap: break-word;
            }
            pre code {
                background: none;
                padding: 0;
            }
            ul, ol {
                margin: 8pt 0;
                padding-left: 20pt;
            }
            li {
                margin: 4pt 0;
            }
            blockquote {
                border-left: 4pt solid #1976d2;
                background-color: #f5f5f5;
                padding: 12pt;
                margin: 12pt 0;
            }
            hr {
                border-top: 1.5pt solid #999;
                margin: 18pt 0;
            }
            /* SVG diagrams from Mermaid */
            img {
                max-width: 100%;
                height: auto;
                display: block;
                margin: 16pt auto;
                page-break-inside: avoid;
            }
            p > img {
                display: block;
                margin: 16pt auto;
            }
            /* Avoid orphan headings */
            h1, h2, h3, h4 {
                page-break-after: avoid;
            }
            h1 + *, h2 + *, h3 + * {
                page-break-before: avoid;
            }
        """)
        
        if renderer == 'playwright':
            print("  [4/5] Playwright generating professional PDF (perfect SVG rendering)...")
            try:
                # Import Playwright PDF generator
                import sys
                pdf_playwright_path = Path(__file__).parent / 'pdf_playwright.py'
                if pdf_playwright_path.exists():
                    sys.path.insert(0, str(Path(__file__).parent))
                    from pdf_playwright import generate_pdf_from_html
                    import asyncio
                    
                    # Extract metadata for header/footer
                    title = metadata.get("title") or doc_title
                    author = metadata.get("author", "Matt Jeffcoat")
                    organization = metadata.get("organization", "[Organization Name]")
                    date = metadata.get("date", "November 2025")
                    
                    # Generate PDF with Playwright - FIXED: Pass all flags!
                    success = asyncio.run(generate_pdf_from_html(
                        str(tmp_html),
                        str(output_path),
                        title=title,
                        author=author,
                        organization=organization,
                        date=date,
                        logo_path=str(logo_path) if logo_path and logo_path.exists() else None,
                        generate_toc=generate_toc,
                        generate_cover=generate_cover,
                        watermark=watermark,
                        css_file=css_file,
                        verbose=verbose
                    ))
                    
                    if success:
                        print(f"[OK] Created: {output_pdf}")
                    else:
                        raise Exception("Playwright PDF generation failed")
                else:
                    print("[WARN] Playwright module not found, falling back to WeasyPrint")
                    renderer = 'weasyprint'
            except ImportError as e:
                print(f"[WARN] Playwright not available ({e}), falling back to WeasyPrint")
                renderer = 'weasyprint'
            except Exception as e:
                print(f"[WARN] Playwright failed ({e}), falling back to WeasyPrint")
                renderer = 'weasyprint'
        
        if renderer == 'weasyprint':
            print("  [4/5] WeasyPrint generating professional PDF...")
            
            # Load CSS from file if provided, otherwise use default
            # Note: WeasyPrint doesn't support all CSS properties (e.g., -webkit-print-color-adjust, break-after/break-inside)
            # If a Playwright CSS file is provided, warn and use default CSS instead
            if css_file and Path(css_file).exists():
                css_file_lower = str(css_file).lower()
                if 'playwright' in css_file_lower:
                    print(f"    [WARN] CSS file '{css_file}' appears to be for Playwright renderer")
                    print(f"    [WARN] WeasyPrint may not support all properties in this CSS file")
                    print(f"    [WARN] Using default WeasyPrint CSS instead")
                    custom_css = default_weasyprint_css
                else:
                    print(f"    Using external CSS: {css_file}")
                    try:
                        custom_css = CSS(filename=str(css_file))
                    except Exception as e:
                        print(f"    [WARN] Failed to load CSS file: {e}")
                        print(f"    [WARN] Using default CSS instead")
                        # Use the default CSS defined above
                        custom_css = CSS(string="""
                        @page {
                            size: A4;
                            margin: 25mm 15mm 20mm 15mm;
                        }
                        body {
                            font-family: 'Segoe UI', Arial, sans-serif;
                            font-size: 11pt;
                            line-height: 1.6;
                        }
                        """)
            else:
                # Use default embedded CSS
                custom_css = default_weasyprint_css
            
            HTML(filename=str(tmp_html)).write_pdf(
                str(output_path),
                stylesheets=[custom_css]
            )
            print(f"[OK] Created: {output_pdf}")
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {e.stderr if e.stderr else e}")
        raise
    except Exception as e:
        print(f"[ERROR] Conversion failed: {e}")
        raise
    finally:
        # Cleanup temp directory
        import shutil
        shutil.rmtree(work_dir, ignore_errors=True)

def markdown_to_docx(md_file, output_docx, logo_path=None, reference_docx=None, cache_dir=None, use_cache=True, theme_config=None, highlight_style=None, crossref_config=None, glossary_file=None):
    """Convert Markdown to DOCX via Pandoc with Mermaid pre-rendering
    
    Args:
        md_file: Path to input Markdown file
        output_docx: Path to output DOCX file
        logo_path: Optional path to logo image (not used in DOCX, but kept for API consistency)
        reference_docx: Optional path to reference DOCX template for custom styling
        cache_dir: Optional cache directory for diagrams (default: pdf-tools/pdf-diagrams/)
        use_cache: If True, use cached diagrams when available
        theme_config: Optional path to Mermaid theme config JSON file (default: pdf-tools/pdf-mermaid-theme.json)
        highlight_style: Optional code highlighting style (default: 'github')
        crossref_config: Optional path to pandoc-crossref config file
        glossary_file: Optional path to glossary YAML file for term expansion
    """
    
    md_path = Path(md_file)
    output_path = Path(output_docx)
    
    print(f"\nConverting {md_file}...")
    
    # Create work directory for temp files
    work_dir = Path(tempfile.mkdtemp(prefix='docx_'))
    
    try:
        # Step 0: Extract metadata from frontmatter
        md_content = md_path.read_text(encoding='utf-8')
        metadata, md_content_clean = extract_metadata(md_content)
        
        # If no frontmatter, use original content
        if not metadata:
            md_content_clean = md_content
        
        # Step 0.5: Expand glossary terms and acronyms
        if glossary_file:
            print("  [0.5/2] Expanding glossary terms...")
            md_content_clean = expand_glossary(md_content_clean, glossary_file)
        
        # Step 1: Pre-render diagrams to PNG (better Word compatibility)
        print("  [1/2] Pre-rendering diagrams to PNG...")
        md_with_images, image_files = render_all_diagrams(md_content_clean, work_dir, also_png=True, cache_dir=cache_dir, use_cache=use_cache, theme_config=theme_config)
        
        # Save preprocessed markdown
        tmp_md = work_dir / 'preprocessed.md'
        tmp_md.write_text(md_with_images, encoding='utf-8')
        
        # Step 2: Pandoc: Markdown → DOCX
        print(f"  [2/2] Pandoc converting to DOCX ({len(image_files)} diagrams embedded)...")
        
        # Find Pandoc executable
        pandoc_exe = r'C:\Program Files\Pandoc\pandoc.exe'
        if not Path(pandoc_exe).exists():
            import shutil
            pandoc_exe = shutil.which('pandoc') or 'pandoc'
        
        # Build Pandoc format string with all extensions
        markdown_extensions = [
            'pipe_tables',
            'backtick_code_blocks',
            'fenced_code_attributes',
            'smart',
            'tex_math_dollars',  # Math: $...$ and $$...$$
            'tex_math_double_backslash',  # Math: \[...\] and \(...\)
            'raw_html',
            'fenced_code_blocks',
            'autolink_bare_uris',
            'strikeout',
            'superscript',
            'subscript',
        ]
        markdown_format = 'markdown+' + '+'.join(markdown_extensions)
        
        pandoc_cmd = [
            pandoc_exe,
            str(tmp_md),
            '-f', markdown_format,
            '-t', 'docx',
            '--toc',
            '--toc-depth=3',
            '--resource-path', str(work_dir),
            '-o', str(output_path)
        ]
        
        # Add code highlighting style if specified
        if highlight_style:
            pandoc_cmd.extend(['--highlight-style', highlight_style])
        else:
            pandoc_cmd.extend(['--highlight-style', 'pygments'])  # Default to pygments style
        
        # Add pandoc-crossref filter if available and config provided
        if crossref_config and Path(crossref_config).exists():
            import shutil
            crossref_filter = shutil.which('pandoc-crossref') or 'pandoc-crossref'
            pandoc_cmd.extend(['--filter', crossref_filter])
            if Path(crossref_config).exists():
                pandoc_cmd.extend(['--metadata', f'crossrefYaml={crossref_config}'])
        
        # Add reference DOCX template if provided
        if reference_docx and Path(reference_docx).exists():
            pandoc_cmd.extend(['--reference-doc', str(reference_docx)])
            print(f"    Using reference template: {reference_docx}")
        
        subprocess.run(pandoc_cmd, check=True, capture_output=True, text=True)
        
        print(f"[OK] Created: {output_docx}")
        
    except subprocess.CalledProcessError as e:
        print(f"[ERROR] Command failed: {e.stderr if e.stderr else e}")
        raise
    except Exception as e:
        print(f"[ERROR] Conversion failed: {e}")
        raise
    finally:
        # Cleanup temp directory
        import shutil
        shutil.rmtree(work_dir, ignore_errors=True)

def markdown_to_html(md_file, output_html, cache_dir=None, use_cache=True, theme_config=None, highlight_style=None, crossref_config=None, glossary_file=None, css_file=None):
    """Convert Markdown to responsive HTML with navigation sidebar
    
    Args:
        md_file: Path to input Markdown file
        output_html: Path to output HTML file
        cache_dir: Optional cache directory for diagrams
        use_cache: If True, use cached diagrams when available
        theme_config: Optional path to Mermaid theme config JSON file
        highlight_style: Optional code highlighting style (default: 'github')
        crossref_config: Optional path to pandoc-crossref config file
        glossary_file: Optional path to glossary YAML file
        css_file: Optional path to custom CSS file for HTML styling
    """
    md_path = Path(md_file)
    output_path = Path(output_html)
    
    print(f"\nConverting {md_file} to HTML...")
    
    work_dir = Path(tempfile.mkdtemp(prefix='html_'))
    
    try:
        # Extract metadata
        md_content = md_path.read_text(encoding='utf-8')
        metadata, md_content_clean = extract_metadata(md_content)
        if not metadata:
            md_content_clean = md_content
        
        # Expand glossary
        if glossary_file:
            print("  [0.5/3] Expanding glossary terms...")
            md_content_clean = expand_glossary(md_content_clean, glossary_file)
        
        # Render diagrams
        print("  [1/3] Pre-rendering diagrams...")
        md_with_diagrams, diagram_files = render_all_diagrams(md_content_clean, work_dir, also_png=False, cache_dir=cache_dir, use_cache=use_cache, theme_config=theme_config)
        
        tmp_md = work_dir / 'preprocessed.md'
        tmp_md.write_text(md_with_diagrams, encoding='utf-8')
        
        # Pandoc to HTML
        print(f"  [2/3] Pandoc converting to HTML ({len(diagram_files)} diagrams)...")
        
        # Find Pandoc executable (robust detection)
        import shutil
        pandoc_exe = None
        
        # Try common Windows locations first
        windows_paths = [
            r'C:\Program Files\Pandoc\pandoc.exe',
            r'C:\Program Files (x86)\Pandoc\pandoc.exe',
            Path.home() / 'AppData' / 'Local' / 'Pandoc' / 'pandoc.exe',
        ]
        
        for path in windows_paths:
            if Path(path).exists():
                pandoc_exe = str(path)
                break
        
        # Fallback to PATH lookup
        if not pandoc_exe:
            pandoc_exe = shutil.which('pandoc')
        
        # Final fallback
        if not pandoc_exe:
            pandoc_exe = 'pandoc'
        
        markdown_extensions = [
            'pipe_tables', 'backtick_code_blocks', 'fenced_code_attributes', 'smart',
            'tex_math_dollars', 'tex_math_double_backslash', 'raw_html',
            'fenced_code_blocks', 'autolink_bare_uris', 'strikeout', 'superscript', 'subscript',
        ]
        markdown_format = 'markdown+' + '+'.join(markdown_extensions)
        
        tmp_html = work_dir / 'output.html'
        pandoc_cmd = [
            pandoc_exe,
            str(tmp_md),
            '-f', markdown_format,
            '-t', 'html5',
            '--standalone',
            '--toc',
            '--toc-depth=3',
            '--resource-path', str(work_dir),
            '--mathjax',
            '-o', str(tmp_html)
        ]
        
        if highlight_style:
            pandoc_cmd.extend(['--syntax-highlighting', highlight_style])
        else:
            pandoc_cmd.extend(['--syntax-highlighting', 'pygments'])
        
        if crossref_config and Path(crossref_config).exists():
            crossref_filter = shutil.which('pandoc-crossref') or 'pandoc-crossref'
            pandoc_cmd.extend(['--filter', crossref_filter])
            pandoc_cmd.extend(['--metadata', f'crossrefYaml={crossref_config}'])
        
        # Verify input file exists
        if not tmp_md.exists():
            raise FileNotFoundError(f"Preprocessed markdown file not found: {tmp_md}")
        
        # Run Pandoc
        result = subprocess.run(pandoc_cmd, check=False, capture_output=True, text=True, shell=False)
        if result.returncode != 0:
            error_msg = result.stderr if result.stderr else result.stdout
            raise RuntimeError(f"Pandoc failed with exit code {result.returncode}: {error_msg}\nCommand: {' '.join(pandoc_cmd)}")
        
        # Post-process HTML with navigation sidebar
        print("  [3/3] Adding navigation sidebar and styling...")
        html_content = tmp_html.read_text(encoding='utf-8')
        
        # Extract TOC and create sidebar navigation
        toc_match = re.search(r'<nav id="TOC"[^>]*>(.*?)</nav>', html_content, re.DOTALL)
        toc_html = toc_match.group(1) if toc_match else ''
        
        # Remove TOC from body (we'll put it in sidebar)
        if toc_match:
            html_content = html_content.replace(toc_match.group(0), '', 1)
        
        # Load custom CSS or use default
        if css_file and Path(css_file).exists():
            css_content = Path(css_file).read_text(encoding='utf-8')
        else:
            # Default responsive CSS with sidebar
            css_content = """
            <style>
            body { font-family: 'Segoe UI', Arial, sans-serif; margin: 0; padding: 0; }
            .container { display: flex; max-width: 1400px; margin: 0 auto; }
            .sidebar { width: 250px; background: #f5f5f5; padding: 20px; position: fixed; height: 100vh; overflow-y: auto; }
            .content { margin-left: 270px; padding: 20px; flex: 1; }
            .sidebar nav ul { list-style: none; padding-left: 0; }
            .sidebar nav li { margin: 8px 0; }
            .sidebar nav a { color: #1976d2; text-decoration: none; }
            .sidebar nav a:hover { text-decoration: underline; }
            @media (max-width: 768px) { .sidebar { display: none; } .content { margin-left: 0; } }
            </style>
            """
        
        # Insert sidebar and CSS
        html_content = html_content.replace('<head>', f'<head>\n{css_content}', 1)
        html_content = html_content.replace('<body>', f'<body>\n<div class="container"><div class="sidebar"><nav id="TOC">{toc_html}</nav></div><div class="content">', 1)
        html_content = html_content.replace('</body>', '</div></div></body>', 1)
        
        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_content, encoding='utf-8')
        
        # Copy diagram files to output directory so they're accessible
        import shutil
        for diagram_file in diagram_files:
            if diagram_file.exists():
                dest = output_path.parent / diagram_file.name
                shutil.copy2(diagram_file, dest)
        
        print(f"[OK] Created: {output_html}")
        
    except Exception as e:
        print(f"[ERROR] HTML conversion failed: {e}")
        raise
    finally:
        import shutil
        shutil.rmtree(work_dir, ignore_errors=True)

if __name__ == "__main__":
    # Legacy batch mode - use md2pdf.py wrapper for better CLI experience
    import sys
    if len(sys.argv) > 1:
        # If called with arguments, use simple mode
        md_file = sys.argv[1]
        pdf_file = sys.argv[2] if len(sys.argv) > 2 else str(Path(md_file).with_suffix('.pdf'))
        markdown_to_pdf(md_file, pdf_file)
    else:
        # Default batch for backward compatibility
        # Paths relative to project root (one level up from pdf-tools/)
        project_root = Path(__file__).parent.parent
        files = [
            (project_root / "docs/architecture-foundation.md", project_root / "docs/architecture-foundation.pdf"),
            (project_root / "docs/architecture-spec.md", project_root / "docs/architecture-spec.pdf"),
            (project_root / "docs/architecture-executive-brief.md", project_root / "docs/architecture-executive-brief.pdf"),
            (project_root / "docs/architecture-executive.md", project_root / "docs/architecture-executive.pdf")
        ]
        
        print("=" * 70)
        print("PROFESSIONAL PDF GENERATION")
        print("Pandoc + WeasyPrint + Mermaid-CLI")
        print("=" * 70)
        print("\nNote: For better CLI experience, use: python md2pdf.py <file.md>")
        print("=" * 70)
        
        for md_file, pdf_file in files:
            if Path(md_file).exists():
                markdown_to_pdf(str(md_file), str(pdf_file))
            else:
                print(f"[ERROR] Not found: {md_file}")
        
        print("\n" + "=" * 70)
        print("[COMPLETE] All PDFs generated with pre-rendered diagrams")
        print("=" * 70)

