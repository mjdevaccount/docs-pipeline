"""
Core Utilities
==============

Utility functions for the PDF generation pipeline.
These are shared across CLI and library usage.
"""

import os
import re
import shutil
from pathlib import Path
from typing import Optional, Dict, Any, Tuple, List


def extract_metadata(content: str) -> Tuple[Dict[str, Any], str]:
    """
    Extract YAML frontmatter metadata from Markdown content.
    
    Args:
        content: Raw Markdown content with optional YAML frontmatter
    
    Returns:
        Tuple of (metadata dict, content without frontmatter)
    """
    import yaml
    
    metadata = {}
    body = content
    
    if content.startswith('---'):
        # Find the closing ---
        end_match = re.search(r'\n---\s*\n', content[3:])
        if end_match:
            yaml_content = content[3:end_match.start() + 3]
            body = content[end_match.end() + 3:]
            
            try:
                metadata = yaml.safe_load(yaml_content) or {}
            except yaml.YAMLError:
                metadata = {}
    
    return metadata, body


def get_cache_dir() -> Path:
    """
    Get the default cache directory for diagram caching.
    
    Uses environment variable DIAGRAM_CACHE if set,
    otherwise uses a temp directory.
    
    Returns:
        Path to cache directory
    """
    env_cache = os.environ.get('DIAGRAM_CACHE')
    if env_cache:
        cache_dir = Path(env_cache)
    else:
        import tempfile
        cache_dir = Path(tempfile.gettempdir()) / 'pdf-diagram-cache'
    
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def check_dependencies() -> bool:
    """
    Check if all required dependencies are available.
    
    Returns:
        True if all required dependencies are present
    """
    errors = []
    warnings = []
    
    # Check Pandoc
    pandoc = shutil.which('pandoc')
    if not pandoc:
        # Check common Windows locations
        windows_paths = [
            r'C:\Program Files\Pandoc\pandoc.exe',
            r'C:\Program Files (x86)\Pandoc\pandoc.exe',
        ]
        for path in windows_paths:
            if Path(path).exists():
                pandoc = path
                break
    
    if not pandoc:
        errors.append("Pandoc not found. Install from https://pandoc.org/installing.html")
    else:
        print(f"[OK] Pandoc found: {pandoc}")
    
    # Check Mermaid-CLI
    mmdc = shutil.which('mmdc') or shutil.which('mmdc.cmd')
    if not mmdc:
        warnings.append("Mermaid-CLI not found. Diagrams will not render.")
        warnings.append("  Install: npm install -g @mermaid-js/mermaid-cli")
    else:
        print(f"[OK] Mermaid-CLI found: {mmdc}")
    
    # Check Python packages
    try:
        import weasyprint
        print(f"[OK] WeasyPrint {weasyprint.__version__}")
    except ImportError:
        errors.append("WeasyPrint not installed. Run: pip install weasyprint")
    
    try:
        import yaml
        print(f"[OK] PyYAML installed")
    except ImportError:
        errors.append("PyYAML not installed. Run: pip install pyyaml")
    
    try:
        from playwright.sync_api import sync_playwright
        print(f"[OK] Playwright installed")
    except ImportError:
        warnings.append("Playwright not installed. Playwright renderer unavailable.")
    
    if errors:
        print(f"\n[ERROR] Missing required dependencies:")
        for error in errors:
            print(f"  - {error}")
        return False
    
    if warnings:
        print(f"\n[WARN] Optional dependencies missing:")
        for warning in warnings:
            print(f"  - {warning}")
    
    return True


def validate_markdown(md_file: str, verbose: bool = False) -> Tuple[bool, List[str]]:
    """
    Validate Markdown file and YAML frontmatter.
    
    Args:
        md_file: Path to Markdown file
        verbose: Show verbose output
    
    Returns:
        Tuple of (is_valid, list_of_issues)
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
                
                if not metadata.get('title'):
                    warnings.append("No 'title' field in frontmatter")
                
                # Check for recommended fields
                for field in ['author', 'date', 'version']:
                    if field not in metadata:
                        warnings.append(f"Missing recommended field: '{field}'")
                        
            except Exception as e:
                errors.append(f"Invalid YAML frontmatter: {e}")
        else:
            warnings.append("No YAML frontmatter found (optional but recommended)")
        
        # Basic Markdown validation
        if not md_content.strip():
            errors.append("Markdown file is empty")
        
        # Check for mismatched code blocks
        code_blocks = md_content.count('```')
        if code_blocks % 2 != 0:
            warnings.append("Possible mismatched code block delimiters")
        
        return len(errors) == 0, errors + warnings
        
    except Exception as e:
        return False, [f"Validation error: {e}"]


def resolve_output_path(output_file: str, output_dir: Optional[str] = None) -> str:
    """
    Resolve output path, applying output_dir if specified.
    
    Args:
        output_file: Desired output filename
        output_dir: Optional output directory
    
    Returns:
        Resolved absolute path for output file
    """
    output_path = Path(output_file)
    
    if output_path.is_absolute():
        target = output_path
    elif output_dir:
        target = Path(output_dir) / output_path.name
    else:
        # Default to output/ in project root
        project_root = Path(__file__).parent.parent.parent.parent
        target = project_root / "output" / output_path.name
    
    target.parent.mkdir(parents=True, exist_ok=True)
    return str(target)

