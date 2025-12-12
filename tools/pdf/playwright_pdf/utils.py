"""
Shared utilities for Playwright PDF generation.
Centralizes common logic to avoid duplication.
"""
from typing import Optional, Dict, Any
from pathlib import Path
import re


# Canonical list of placeholder values to filter out
PLACEHOLDER_VALUES = frozenset([
    'Organization',
    'Engineering Team', 
    'Author Name',
    '[Organization Name]',
    'Untitled Document',
    'Architecture Documentation',
    'Documentation',
])


def is_placeholder(value: Optional[str]) -> bool:
    """Check if a value is a placeholder that should be filtered out."""
    if not value:
        return True
    return value.strip() in PLACEHOLDER_VALUES


def filter_placeholder(value: Optional[str], default: str = '') -> str:
    """Return default if value is a placeholder, otherwise return the value."""
    if is_placeholder(value):
        return default
    return value


def extract_margins_from_css(css_file: Path) -> Optional[Dict[str, str]]:
    """
    Extract @page margin values from a CSS file, excluding pseudo-selectors.
    
    Rules:
    1. @page (default) - apply to all pages
    2. @page:first - apply to first page only (IGNORED - Playwright applies margins to all pages)
    3. @page:left/:right - apply to left/right pages (IGNORED)
    
    For PDF generation, we use @page (not @page:first) because Playwright
    applies margins to ALL pages, not just the first.
    
    Returns dict like {'top': '2cm', 'right': '1.8cm', 'bottom': '2cm', 'left': '1.8cm'}
    or None if not found.
    """
    if not css_file or not css_file.exists():
        return None
    
    try:
        css_content = css_file.read_text(encoding='utf-8')
        
        # Find @page rule (NOT @page:first, NOT @page:left, etc.)
        # Use negative lookahead to exclude pseudo-selectors
        # Pattern: @page followed by NOT colon, NOT slash, then opening brace
        page_match = re.search(r'@page(?!:)(?!\/)\s*\{([^}]+)\}', css_content)
        if not page_match:
            return None
        
        page_content = page_match.group(1)
        
        # Find margin property
        margin_match = re.search(r'margin\s*:\s*([^;]+);', page_content)
        if not margin_match:
            return None
        
        margin_value = margin_match.group(1).strip()
        parts = margin_value.split()
        
        # Parse CSS margin shorthand
        if len(parts) == 1:
            # All sides same
            return {'top': parts[0], 'right': parts[0], 'bottom': parts[0], 'left': parts[0]}
        elif len(parts) == 2:
            # top/bottom, left/right
            return {'top': parts[0], 'right': parts[1], 'bottom': parts[0], 'left': parts[1]}
        elif len(parts) == 3:
            # top, left/right, bottom
            return {'top': parts[0], 'right': parts[1], 'bottom': parts[2], 'left': parts[1]}
        elif len(parts) == 4:
            # top, right, bottom, left
            return {'top': parts[0], 'right': parts[1], 'bottom': parts[2], 'left': parts[3]}
        
        return None
        
    except Exception as e:
        # Log error for debugging but don't fail silently
        import sys
        print(f"[WARN] CSS margin extraction failed: {e}", file=sys.stderr)
        return None


def detect_dark_mode(profile_name: Optional[str] = None, css_file: Optional[Path] = None) -> bool:
    """
    Detect if dark mode should be used based on profile name or CSS file.
    """
    if profile_name and 'dark' in profile_name.lower():
        return True
    
    if css_file:
        css_str = str(css_file).lower()
        if 'dark' in css_str:
            return True
    
    return False

