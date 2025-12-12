"""
CSS Generator from Design Tokens

Generates production-ready CSS files from design-tokens.yml.
Creates complete theme stylesheets with all variables, selectors, and styles.

Usage:
    generator = CSSGenerator('tools/pdf/config/design-tokens.yml')
    css = generator.generate_css('dark-pro')
    generator.generate_all('tools/pdf/styles/')
"""

from pathlib import Path
from typing import Dict, List, Optional, Any
import yaml
from dataclasses import dataclass


@dataclass
class CSSTheme:
    """Represents a theme for CSS generation."""
    name: str
    description: str
    mode: str
    colors: Dict[str, Any]
    mermaid: Dict[str, str]
    global_tokens: Dict[str, Any]


class CSSGenerator:
    """
    Generates complete CSS theme files from design tokens.
    
    Creates production-ready CSS with:
    - CSS custom properties (:root variables)
    - Complete base styles (typography, components, etc.)
    - Print-specific adjustments
    - Media query support
    """
    
    def __init__(self, tokens_file: str):
        """
        Initialize CSS generator.
        
        Args:
            tokens_file: Path to design-tokens.yml
        """
        self.tokens_file = Path(tokens_file)
        if not self.tokens_file.exists():
            raise FileNotFoundError(f"Tokens file not found: {tokens_file}")
        
        self.tokens: Optional[Dict[str, Any]] = None
        self.load_tokens()
    
    def load_tokens(self) -> None:
        """Load and parse design tokens YAML file."""
        with open(self.tokens_file) as f:
            self.tokens = yaml.safe_load(f)
    
    def _flatten_dict(self, d: Dict[str, Any], parent_key: str = '') -> Dict[str, str]:
        """Flatten nested dict to single level with dash-separated keys.
        
        Example:
            {'primary': {'base': '#60a5fa'}} -> {'primary-base': '#60a5fa'}
        """
        items: List[tuple] = []
        for k, v in d.items():
            new_key = f"{parent_key}-{k}" if parent_key else k
            
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key).items())
            else:
                items.append((new_key, str(v)))
        
        return dict(items)
    
    def _generate_root_variables(self, theme: CSSTheme) -> str:
        """Generate :root CSS variables section."""
        lines = [":root {"]
        
        # Global tokens
        global_flat = self._flatten_dict(theme.global_tokens)
        for key, value in sorted(global_flat.items()):
            css_var = f"--{key}".replace('_', '-')
            lines.append(f"    {css_var}: {value};")
        
        lines.append("")  # Blank line for readability
        
        # Theme-specific color tokens
        colors_flat = self._flatten_dict(theme.colors)
        for key, value in sorted(colors_flat.items()):
            css_var = f"--color-{key}".replace('_', '-')
            lines.append(f"    {css_var}: {value};")
        
        lines.append("")  # Blank line
        
        # Mermaid tokens (60+)
        for key, value in sorted(theme.mermaid.items()):
            css_var = f"--mermaid-{key}".replace('_', '-')
            # Handle special values (quoted strings, numbers)
            if isinstance(value, str):
                if value.startswith('"') or value.startswith("'"):
                    lines.append(f"    {css_var}: {value};")
                elif value.endswith('px') or value.endswith('ms') or value.endswith('em'):
                    lines.append(f"    {css_var}: {value};")
                else:
                    lines.append(f"    {css_var}: {value};")
            else:
                lines.append(f"    {css_var}: {value};")
        
        lines.append("}")
        return "\n".join(lines)
    
    def _generate_css_header(self, theme: CSSTheme) -> str:
        """Generate CSS file header comment."""
        return f"""
/**
 * {theme.name} Theme
 * 
 * {theme.description}
 * Mode: {theme.mode.capitalize()}
 * 
 * Auto-generated from design-tokens.yml
 * Do NOT edit manually - changes will be overwritten
 * 
 * Generated: 2025-12-12
 * Version: 1.0
 */
""".strip()
    
    def _generate_page_setup(self) -> str:
        """Generate @page rules for PDF rendering."""
        return """
/* ============================================================================
   PAGE SETUP - Margins: 2cm all sides
   ========================================================================== */

@page {
    size: A4;
    margin: 2cm 1.8cm 2cm 1.8cm;
    background-color: var(--color-background-page);
}
""".strip()
    
    def _generate_base_styles(self, theme: CSSTheme) -> str:
        """Generate base HTML/body styles."""
        mode_class = "dark" if theme.mode == "dark" else "light"
        
        return f"""
/* ============================================================================
   BASE TYPOGRAPHY & LAYOUT
   ========================================================================== */

html {{
    background: var(--color-background-page) !important;
    font-family: var(--fonts-body);
    font-size: var(--font-sizes-base);
    line-height: var(--line-height-normal);
    color: var(--color-text-primary);
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
    font-feature-settings: 'liga' 1, 'calt' 1;
}}

body {{
    background: var(--color-background-page) !important;
    color: var(--color-text-secondary);
    margin: 0;
    padding: 0;
    width: 100%;
    max-width: none;
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
}}

/* ============================================================================
   HEADINGS
   ========================================================================== */

h1, h2, h3, h4, h5, h6 {{
    font-weight: var(--font-weights-semibold);
    color: var(--color-text-primary);
    margin-top: 1.5em;
    margin-bottom: 0.5em;
    line-height: var(--line-height-tight);
    letter-spacing: var(--letter-spacing-tight);
}}

h1 {{
    font-size: var(--font-sizes-4xl);
    text-transform: uppercase;
    letter-spacing: var(--letter-spacing-wide);
    border-bottom: 2px solid var(--color-border-primary);
    padding-bottom: 0.4em;
    margin-top: 0.5em;
}}

h2 {{
    font-size: var(--font-sizes-3xl);
    border-bottom: 1px solid var(--color-border-primary);
    padding-bottom: 0.3em;
}}

h3 {{
    font-size: var(--font-sizes-2xl);
}}

h4 {{
    font-size: var(--font-sizes-xl);
}}

h5 {{
    font-size: var(--font-sizes-lg);
}}

h6 {{
    font-size: var(--font-sizes-md);
}}

/* ============================================================================
   PARAGRAPHS & LINKS
   ========================================================================== */

p {{
    margin: 0.5em 0 1em 0;
    color: var(--color-text-secondary);
    text-align: left;
    orphans: 3;
    widows: 3;
}}

a {{
    color: var(--color-primary-base);
    text-decoration: none;
    font-weight: var(--font-weights-medium);
    transition: color 250ms cubic-bezier(0.16, 1, 0.3, 1);
}}

a:hover {{
    color: var(--color-primary-light);
    text-decoration: underline;
}}

/* ============================================================================
   CODE & PREFORMATTED TEXT
   ========================================================================== */

code {{
    font-family: var(--fonts-mono);
    font-size: 0.88em;
    background: var(--color-component-code-bg);
    color: var(--color-component-code-text);
    padding: 0.2em 0.4em;
    border-radius: var(--radius-sm);
    border: 1px solid var(--color-border-primary);
    font-variant-numeric: tabular-nums;
}}

pre {{
    background: var(--color-component-pre-bg);
    border-left: 4px solid var(--color-primary-base);
    border: 1px solid var(--color-border-primary);
    border-radius: var(--radius-md);
    padding: 1.25rem;
    margin: 1.5em 0;
    overflow-x: auto;
    box-shadow: var(--shadows-lg);
    width: 100%;
    max-width: none;
}}

pre code {{
    background: transparent;
    color: var(--color-component-pre-text);
    padding: 0;
    border: none;
    font-size: 0.875rem;
    line-height: 1.6;
    font-variant-ligatures: common-ligatures contextual;
}}

/* ============================================================================
   LISTS
   ========================================================================== */

ul, ol {{
    margin: 1rem 0;
    padding-left: 1.75rem;
    width: 100%;
    max-width: none;
}}

li {{
    margin: 0.5rem 0;
    line-height: 1.6;
    color: var(--color-text-secondary);
}}

ul ul, ol ol, ul ol, ol ul {{
    margin: 0.5rem 0;
    padding-left: 1.5rem;
}}

ul {{
    list-style-type: '\u2022';
}}

li::marker {{
    color: var(--color-primary-base);
    font-weight: var(--font-weights-medium);
    margin-right: 0.75em;
}}

/* ============================================================================
   TABLES
   ========================================================================== */

table {{
    width: 100%;
    border-collapse: separate;
    border-spacing: 0;
    font-size: 0.925rem;
    border: 1px solid var(--color-border-primary);
    border-radius: var(--radius-md);
    margin: 1.5em 0;
    background: var(--color-background-surface);
    box-sizing: border-box;
}}

thead {{
    background: var(--color-background-subtle);
    font-weight: var(--font-weights-bold);
}}

th {{
    padding: 0.875rem 1rem;
    text-align: left;
    color: var(--color-text-primary);
    border-bottom: 2px solid var(--color-primary-base);
    font-size: 0.875rem;
    text-transform: uppercase;
    letter-spacing: 0.025em;
}}

td {{
    padding: 0.875rem 1rem;
    border-bottom: 1px solid var(--color-border-primary);
    color: var(--color-text-secondary);
}}

tbody tr:last-child td {{
    border-bottom: none;
}}

tbody tr:hover {{
    background: rgba(96, 165, 250, 0.05);
}}

tbody tr:nth-child(odd) {{
    background: rgba(255, 255, 255, 0.02);
}}

/* ============================================================================
   BLOCKQUOTES
   ========================================================================== */

blockquote {{
    border-left: 4px solid var(--color-component-blockquote-border);
    background: var(--color-component-blockquote-bg);
    padding: 1.25rem 1.5rem;
    margin: 1.5em 0;
    width: 100%;
    max-width: none;
    font-style: italic;
    color: var(--color-component-blockquote-text);
    border-radius: 0 0.25rem 0.25rem 0;
    box-sizing: border-box;
    line-height: 1.6;
    box-shadow: var(--shadows-md);
}}

blockquote p {{
    margin: 0.5rem 0;
}}

blockquote > :first-child {{
    margin-top: 0;
}}

blockquote > :last-child {{
    margin-bottom: 0;
}}

/* ============================================================================
   PRINT-SPECIFIC ADJUSTMENTS
   ========================================================================== */

@media print {{
    body {{
        background: var(--color-background-page);
        color: var(--color-text-secondary);
    }}
    
    a {{
        color: var(--color-primary-base);
        text-decoration: none;
    }}
    
    pre, blockquote {{
        background: var(--color-background-surface);
    }}
    
    svg {{
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
    }}
    
    svg text, svg tspan {{
        fill: var(--color-text-primary) !important;
    }}
}}
""".strip()
    
    def _generate_mermaid_styles(self) -> str:
        """Generate Mermaid diagram styling."""
        return """
/* ============================================================================
   MERMAID DIAGRAM STYLING
   ========================================================================== */

svg {
    -webkit-print-color-adjust: exact !important;
    print-color-adjust: exact !important;
    color-adjust: exact !important;
}

svg text {
    fill: var(--color-text-primary) !important;
    color: var(--color-text-primary) !important;
    font-family: var(--fonts-body) !important;
    font-size: 0.9rem !important;
    font-weight: var(--font-weights-medium) !important;
}

svg text.label,
svg text.nodeLabel,
svg text.title,
svg text.sectionTitle,
svg text.mainTitle,
svg tspan {
    fill: var(--color-text-primary) !important;
    color: var(--color-text-primary) !important;
}

.mermaid text,
.mermaid tspan,
.mermaid foreignObject text {
    fill: var(--color-text-primary) !important;
    color: var(--color-text-primary) !important;
}

.mermaid .nodeLabel,
.mermaid .label,
.mermaid .edgeLabel,
.mermaid .flowchart-label {
    fill: var(--color-text-primary) !important;
}

svg rect[class*="diagram"],
svg circle[class*="diagram"],
svg ellipse[class*="diagram"],
svg path[class*="diagram"] {
    stroke: var(--color-primary-base) !important;
    stroke-width: 2px !important;
}

svg .axis-label,
svg .legend-label,
svg .chart-label,
svg .data-label,
svg [text-anchor] {
    fill: var(--color-text-primary) !important;
}

svg text:not([fill]),
svg tspan:not([fill]) {
    fill: var(--color-text-primary) !important;
}

svg text[fill="white"],
svg text[fill="#fff"],
svg text[fill="#ffffff"],
svg text[fill="#f0f0f0"],
svg text[fill="#e0e0e0"],
svg tspan[fill="white"],
svg tspan[fill="#fff"],
svg tspan[fill="#ffffff"] {
    fill: var(--color-text-primary) !important;
}
""".strip()
    
    def generate_css(self, theme_name: str) -> str:
        """
        Generate complete CSS for a theme.
        
        Args:
            theme_name: Theme to generate ('dark-pro', 'enterprise-blue', etc.)
        
        Returns:
            Complete CSS as string
        """
        if not self.tokens:
            raise RuntimeError("Tokens not loaded")
        
        if theme_name not in self.tokens['themes']:
            raise ValueError(f"Theme not found: {theme_name}")
        
        theme_data = self.tokens['themes'][theme_name]
        
        # Create CSSTheme object
        theme = CSSTheme(
            name=theme_data['metadata']['name'],
            description=theme_data['metadata']['description'],
            mode=theme_data['metadata']['mode'],
            colors=theme_data['colors'],
            mermaid=theme_data['mermaid'],
            global_tokens=self.tokens['global']
        )
        
        # Build CSS sections
        parts = [
            self._generate_css_header(theme),
            "",
            self._generate_root_variables(theme),
            "",
            self._generate_page_setup(),
            "",
            self._generate_base_styles(theme),
            "",
            self._generate_mermaid_styles(),
        ]
        
        return "\n\n".join(parts)
    
    def generate_all(self, output_dir: str) -> Dict[str, bool]:
        """
        Generate CSS files for all themes.
        
        Args:
            output_dir: Directory to write CSS files
        
        Returns:
            Dict mapping theme names to generation success status
        """
        if not self.tokens:
            raise RuntimeError("Tokens not loaded")
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        results = {}
        
        for theme_name in self.tokens['themes'].keys():
            try:
                css = self.generate_css(theme_name)
                output_file = output_path / f"{theme_name}.css"
                output_file.write_text(css)
                results[theme_name] = True
                print(f"✅ Generated: {output_file}")
            except Exception as e:
                results[theme_name] = False
                print(f"❌ Failed {theme_name}: {e}")
        
        return results


if __name__ == "__main__":
    import sys
    
    tokens_file = "tools/pdf/config/design-tokens.yml"
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "tools/pdf/styles/generated/"
    
    print(f"\n{'='*70}")
    print(f"CSS Generation from Design Tokens")
    print(f"{'='*70}")
    print(f"Tokens file: {tokens_file}")
    print(f"Output dir: {output_dir}\n")
    
    generator = CSSGenerator(tokens_file)
    results = generator.generate_all(output_dir)
    
    print(f"\n{'='*70}")
    success_count = sum(1 for v in results.values() if v)
    print(f"Generated {success_count}/{len(results)} themes successfully")
    print(f"{'='*70}\n")
    
    sys.exit(0 if all(results.values()) else 1)
