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
    Detect if dark mode should be used based on profile name, CSS filename, or CSS content.
    
    Detection order:
    1. Profile name contains 'dark'
    2. CSS filename contains 'dark'
    3. CSS content has dark background colors on body/html
    """
    # Check profile name
    if profile_name and 'dark' in profile_name.lower():
        return True
    
    # Check CSS filename
    if css_file:
        css_str = str(css_file).lower()
        if 'dark' in css_str:
            return True
        
        # Check CSS content for dark backgrounds
        if css_file.exists():
            try:
                css_content = css_file.read_text(encoding='utf-8')
                
                # Look for dark background colors on body/html
                # Common dark theme patterns: #0f172a, #1a1a1a, #000, rgb(0-50, 0-50, 0-50)
                dark_bg_patterns = [
                    r'(?:body|html)\s*\{[^}]*background(?:-color)?\s*:\s*#(?:0[0-9a-f]{5}|1[0-9a-f]{5}|[0-2][0-9a-f]{4})',  # #0xxxxx, #1xxxxx
                    r'(?:body|html)\s*\{[^}]*background(?:-color)?\s*:\s*rgb\s*\(\s*[0-4][0-9]?\s*,',  # rgb(0-49, ...)
                    r'--color-bg-page\s*:\s*#(?:0[0-9a-f]{5}|1[0-9a-f]{5})',  # CSS variable with dark color
                ]
                
                for pattern in dark_bg_patterns:
                    if re.search(pattern, css_content, re.IGNORECASE):
                        return True
                        
            except Exception:
                pass  # Fallback to False if CSS can't be read
    
    return False

