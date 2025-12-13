"""
Unified Theme Manager

Coordinates theme validation, generation, and management.
Provides single interface for all theme operations.

Usage:
    manager = ThemeManager('tools/pdf/config/design-tokens.yml')
    
    # Validate tokens
    if manager.validate():
        print("Tokens valid")
    
    # Generate CSS for all themes
    manager.generate_all('tools/pdf/styles/generated/')
    
    # Get theme info
    theme_info = manager.get_theme('dark-pro')
    print(f"Theme: {theme_info['name']}")
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple
import yaml
from dataclasses import dataclass
from datetime import datetime

from theme_validator import ThemeValidator, ValidationReport
from css_generator import CSSGenerator


@dataclass
class ThemeInfo:
    """Information about a theme."""
    name: str
    key: str
    description: str
    mode: str
    color_count: int
    mermaid_var_count: int


class ThemeManager:
    """
    Unified theme management system.
    
    Handles:
    - Theme validation
    - CSS generation
    - Theme discovery and info
    - Configuration management
    """
    
    def __init__(self, tokens_file: str):
        """
        Initialize theme manager.
        
        Args:
            tokens_file: Path to design-tokens.yml
        """
        self.tokens_file = Path(tokens_file)
        if not self.tokens_file.exists():
            raise FileNotFoundError(f"Tokens file not found: {tokens_file}")
        
        self.validator = ThemeValidator(str(self.tokens_file))
        self.generator = CSSGenerator(str(self.tokens_file))
        self.tokens = self.generator.tokens
        self.validation_report: Optional[ValidationReport] = None
    
    def validate(self, wcag_level: str = "AA") -> bool:
        """
        Validate all themes.
        
        Args:
            wcag_level: WCAG compliance level ("AA" or "AAA")
        
        Returns:
            True if all themes valid
        """
        self.validation_report = self.validator.validate(wcag_level)
        return self.validation_report.is_valid
    
    def get_validation_report(self) -> Optional[ValidationReport]:
        """Get last validation report."""
        return self.validation_report
    
    def list_themes(self) -> List[str]:
        """Get list of all available themes."""
        if not self.tokens:
            return []
        return list(self.tokens.get('themes', {}).keys())
    
    def get_theme_info(self, theme_name: str) -> Optional[ThemeInfo]:
        """
        Get information about a theme.
        
        Args:
            theme_name: Theme to get info for
        
        Returns:
            ThemeInfo or None if not found
        """
        if not self.tokens or theme_name not in self.tokens.get('themes', {}):
            return None
        
        theme_data = self.tokens['themes'][theme_name]
        metadata = theme_data['metadata']
        
        # Count colors
        color_count = self._count_colors(theme_data['colors'])
        
        # Count Mermaid variables
        mermaid_count = len(theme_data['mermaid'])
        
        return ThemeInfo(
            name=metadata['name'],
            key=theme_name,
            description=metadata['description'],
            mode=metadata['mode'],
            color_count=color_count,
            mermaid_var_count=mermaid_count,
        )
    
    def get_all_themes_info(self) -> List[ThemeInfo]:
        """Get information about all themes."""
        themes_info = []
        for theme_name in self.list_themes():
            info = self.get_theme_info(theme_name)
            if info:
                themes_info.append(info)
        return themes_info
    
    def generate_css(self, theme_name: str) -> Optional[str]:
        """
        Generate CSS for a specific theme.
        
        Args:
            theme_name: Theme to generate
        
        Returns:
            CSS as string or None if failed
        """
        try:
            return self.generator.generate_css(theme_name)
        except Exception as e:
            print(f"Error generating CSS for {theme_name}: {e}")
            return None
    
    def generate_all(
        self,
        output_dir: str,
        validate_first: bool = True,
        wcag_level: str = "AA",
    ) -> Dict[str, bool]:
        """
        Generate CSS for all themes.
        
        Args:
            output_dir: Directory to write CSS files
            validate_first: Validate tokens before generating
            wcag_level: WCAG compliance level if validating
        
        Returns:
            Dict mapping theme names to generation success
        """
        # Validate first if requested
        if validate_first:
            if not self.validate(wcag_level):
                print("\n[ERROR] Validation failed. Fix issues before generating.")
                if self.validation_report:
                    self.validation_report.print_report()
                return {name: False for name in self.list_themes()}
        
        # Generate all
        return self.generator.generate_all(output_dir)
    
    def create_index(self, output_dir: str) -> bool:
        """
        Create an index document of all themes.
        
        Args:
            output_dir: Directory to write index file
        
        Returns:
            True if successful
        """
        try:
            output_path = Path(output_dir)
            output_path.mkdir(parents=True, exist_ok=True)
            
            index_file = output_path / "THEMES_INDEX.md"
            
            lines = [
                "# Design Themes Index",
                f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
                f"\nTotal Themes: {len(self.list_themes())}",
                "\n## Available Themes\n",
            ]
            
            for theme_info in self.get_all_themes_info():
                lines.append(f"### {theme_info.name}")
                lines.append(f"- **Key**: `{theme_info.key}`")
                lines.append(f"- **Description**: {theme_info.description}")
                lines.append(f"- **Mode**: {theme_info.mode}")
                lines.append(f"- **Colors**: {theme_info.color_count}")
                lines.append(f"- **Mermaid Variables**: {theme_info.mermaid_var_count}")
                lines.append(f"- **CSS File**: `{theme_info.key}.css`")
                lines.append("")
            
            index_file.write_text("\n".join(lines))
            print(f"[OK] Created index: {index_file}")
            return True
        
        except Exception as e:
            print(f"[ERROR] Failed to create index: {e}")
            return False
    
    def _count_colors(self, colors_dict: Dict) -> int:
        """Recursively count all color values."""
        count = 0
        for v in colors_dict.values():
            if isinstance(v, dict):
                count += self._count_colors(v)
            else:
                count += 1
        return count
    
    def summary(self) -> str:
        """Get summary of all themes."""
        themes = self.get_all_themes_info()
        total_colors = sum(t.color_count for t in themes)
        total_mermaid = sum(t.mermaid_var_count for t in themes)
        
        summary_lines = [
            f"\n{'='*70}",
            f"THEME MANAGER SUMMARY",
            f"{'='*70}",
            f"\nTokens file: {self.tokens_file}",
            f"\nTotal themes: {len(themes)}",
            f"Total colors (all themes): {total_colors}",
            f"Total Mermaid variables: {total_mermaid}",
            f"\nThemes:",
        ]
        
        for theme in themes:
            summary_lines.append(
                f"  - {theme.name:20} ({theme.mode:5}) - "
                f"{theme.color_count:3} colors, {theme.mermaid_var_count:2} mermaid vars"
            )
        
        summary_lines.append(f"\n{'='*70}\n")
        return "\n".join(summary_lines)


def main():
    """CLI interface for theme manager."""
    import sys
    
    tokens_file = "tools/pdf/config/design-tokens.yml"
    output_dir = sys.argv[1] if len(sys.argv) > 1 else "tools/pdf/styles/generated/"
    
    print(f"\n{'='*70}")
    print("PHASE 2: Theme Manager - Validation + Generation")
    print(f"{'='*70}\n")
    
    try:
        # Initialize manager
        manager = ThemeManager(tokens_file)
        print(manager.summary())
        
        # Validate
        print("\n[INFO] Validating tokens...")
        if not manager.validate(wcag_level="AA"):
            print("\n[ERROR] Validation FAILED")
            report = manager.get_validation_report()
            if report:
                report.print_report()
            sys.exit(1)
        
        print("[OK] Validation PASSED\n")
        
        # Generate
        print(f"\n[INFO] Generating CSS files to: {output_dir}")
        results = manager.generate_all(output_dir, validate_first=False)
        
        # Create index
        manager.create_index(output_dir)
        
        # Summary
        success = sum(1 for v in results.values() if v)
        print(f"\n{'='*70}")
        print(f"[OK] Generated {success}/{len(results)} CSS files successfully")
        print(f"{'='*70}\n")
        
        sys.exit(0 if success == len(results) else 1)
    
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
