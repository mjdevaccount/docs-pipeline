#!/usr/bin/env python3
"""Simple Markdown to HTML converter for testing"""
import sys
from pathlib import Path

try:
    import markdown
    from markdown.extensions import fenced_code, tables, toc
except ImportError:
    print("Error: markdown library not installed. Install with: pip install markdown")
    sys.exit(1)

def convert_md_to_html(md_file, html_file):
    """Convert markdown to HTML"""
    md_content = Path(md_file).read_text(encoding='utf-8')
    
    # Extract frontmatter if present
    if md_content.startswith('---'):
        parts = md_content.split('---', 2)
        if len(parts) >= 3:
            frontmatter = parts[1]
            md_content = parts[2]
    
    # Convert markdown to HTML
    md = markdown.Markdown(extensions=['fenced_code', 'tables', 'toc', 'codehilite'])
    html_body = md.convert(md_content)
    
    # Create full HTML document
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Project Documentation Architecture Proposal</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
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
    </style>
</head>
<body>
{html_body}
</body>
</html>"""
    
    Path(html_file).write_text(html, encoding='utf-8')
    print(f"Converted {md_file} to {html_file}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python md_to_html_simple.py input.md [output.html]")
        sys.exit(1)
    
    md_file = sys.argv[1]
    html_file = sys.argv[2] if len(sys.argv) > 2 else md_file.replace('.md', '.html')
    
    convert_md_to_html(md_file, html_file)

