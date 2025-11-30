#!/usr/bin/env python3
"""Markdown to HTML converter with Mermaid diagram rendering and frontmatter preservation"""
import sys
import re
import subprocess
import hashlib
import tempfile
import yaml
from pathlib import Path

try:
    import markdown
    from markdown.extensions import fenced_code, tables, toc
except ImportError:
    print("Error: markdown library not installed. Install with: pip install markdown pyyaml")
    sys.exit(1)

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

def get_cache_dir():
    """Get cache directory for diagrams"""
    cache_dir = Path(__file__).parent / 'output' / 'pdf-diagrams'
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir

def render_mermaid_diagram(mermaid_code, cache_dir, work_dir):
    """Render a Mermaid diagram to SVG"""
    # Create hash for caching
    code_hash = hashlib.md5(mermaid_code.encode()).hexdigest()[:8]
    svg_file = cache_dir / f"{code_hash}.svg"
    
    # Check cache first
    if svg_file.exists():
        return svg_file
    
    # Create temporary mermaid file
    mmd_file = work_dir / f"{code_hash}.mmd"
    mmd_file.write_text(mermaid_code, encoding='utf-8')
    
    # Find mmdc executable
    mmdc_exe = r'C:\Users\mattj\AppData\Roaming\npm\mmdc.cmd'
    if not Path(mmdc_exe).exists():
        mmdc_exe = 'mmdc'  # Try PATH
    
    try:
        # Render SVG
        svg_cmd = [
            mmdc_exe,
            '-i', str(mmd_file),
            '-o', str(svg_file),
            '-t', 'neutral',
            '-b', 'transparent'
        ]
        
        result = subprocess.run(
            svg_cmd,
            capture_output=True,
            text=True,
            timeout=30,
            shell=True
        )
        
        if result.returncode == 0 and svg_file.exists():
            return svg_file
        else:
            print(f"Warning: Mermaid rendering failed: {result.stderr}")
            return None
    except Exception as e:
        print(f"Warning: Mermaid rendering error: {e}")
        return None

def convert_md_to_html(md_file, html_file, verbose=False):
    """Convert markdown to HTML with Mermaid diagram rendering"""
    md_content = Path(md_file).read_text(encoding='utf-8')
    
    # Extract frontmatter
    metadata, md_content_clean = extract_metadata(md_content)
    
    # Create work directory
    work_dir = Path(tempfile.mkdtemp(prefix='md2html_'))
    cache_dir = get_cache_dir()
    
    try:
        # Render Mermaid diagrams
        svg_files = []
        def mermaid_to_svg(match):
            mermaid_code = match.group(1).strip()
            svg_file = render_mermaid_diagram(mermaid_code, cache_dir, work_dir)
            
            if svg_file and svg_file.exists():
                svg_files.append(svg_file)
                # Use absolute file:// URL for local HTML files
                abs_path = svg_file.absolute()
                file_url = f"file:///{str(abs_path).replace(chr(92), '/')}"
                return f'<figure><img src="{file_url}" alt="Diagram" style="max-width: 100%; height: auto;" /></figure>'
            else:
                return f'<pre><code class="language-mermaid">[Diagram rendering failed]\n{mermaid_code}</code></pre>'
        
        # Replace Mermaid blocks with SVG images
        md_with_diagrams = re.sub(
            r'```mermaid\n(.+?)```',
            mermaid_to_svg,
            md_content_clean,
            flags=re.DOTALL
        )
        
        # Convert markdown to HTML
        md = markdown.Markdown(extensions=['fenced_code', 'tables', 'toc', 'codehilite'])
        html_body = md.convert(md_with_diagrams)
        
        # Build HTML with ALL metadata in head
        title = metadata.get('title', 'Document')
        author = metadata.get('author', '')
        organization = metadata.get('organization', '')
        date = metadata.get('date', '')
        doc_type = metadata.get('type', '')
        classification = metadata.get('classification', '')
        version = metadata.get('version', '')
        
        # Build meta tags for all frontmatter fields
        meta_tags = []
        if author:
            meta_tags.append(f'    <meta name="author" content="{author}">')
        if organization:
            meta_tags.append(f'    <meta name="organization" content="{organization}">')
        if date:
            meta_tags.append(f'    <meta name="date" content="{date}">')
        if doc_type:
            meta_tags.append(f'    <meta name="type" content="{doc_type}">')
        if classification:
            meta_tags.append(f'    <meta name="classification" content="{classification}">')
        if version:
            meta_tags.append(f'    <meta name="version" content="{version}">')
        
        meta_tags_str = '\n'.join(meta_tags)
        
        html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
{meta_tags_str}
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            max-width: 900px;
            margin: 0 auto;
            padding: 20px;
        }}
        h1, h2, h3, h4, h5, h6 {{
            margin-top: 1.5em;
            margin-bottom: 0.5em;
        }}
        code {{
            background: #f4f4f4;
            padding: 2px 4px;
            border-radius: 3px;
        }}
        pre {{
            background: #f4f4f4;
            padding: 10px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 1em 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }}
        th {{
            background-color: #f2f2f2;
        }}
        figure {{
            margin: 1em 0;
            text-align: center;
        }}
        figure img {{
            max-width: 100%;
            height: auto;
        }}
    </style>
</head>
<body>
{html_body}
</body>
</html>"""
        
        Path(html_file).write_text(html, encoding='utf-8')
        if verbose:
            print(f"Converted {md_file} to {html_file}")
            print(f"  Rendered {len(svg_files)} Mermaid diagrams")
            print(f"  Metadata: title={title}, author={author}, date={date}")
        
    finally:
        # Cleanup work directory
        import shutil
        try:
            shutil.rmtree(work_dir)
        except:
            pass

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python md_to_html_with_diagrams.py input.md [output.html]")
        sys.exit(1)
    
    md_file = sys.argv[1]
    html_file = sys.argv[2] if len(sys.argv) > 2 else md_file.replace('.md', '.html')
    verbose = '--verbose' in sys.argv or '-v' in sys.argv
    
    convert_md_to_html(md_file, html_file, verbose=verbose)

