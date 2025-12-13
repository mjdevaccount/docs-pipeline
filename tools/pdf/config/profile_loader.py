"""
Profile Loader - Load theme profiles from TOML configuration

Supports both:
- profiles.toml (new, recommended)
- profiles.py (legacy, for backward compatibility)

Usage:
    loader = ProfileLoader('tools/pdf/config/')
    profile = loader.get_profile('dark-pro')
    css_path = loader.get_css_file('dark-pro')
"""

from pathlib import Path
from typing import Dict, Optional, List, Any
from dataclasses import dataclass
import sys

try:
    import tomllib  # Python 3.11+
except ImportError:
    import tomli as tomllib  # Fallback for Python 3.10


@dataclass
class ThemeProfile:
    """Theme profile configuration."""
    name: str
    description: str
    mode: str  # "light" or "dark"
    author: str
    version: str
    css_file: str
    header_height: str = "1.5cm"
    footer_height: str = "1.2cm"
    margin_top: str = "2cm"
    margin_bottom: str = "2cm"
    margin_left: str = "1.8cm"
    margin_right: str = "1.8cm"
    base_font_size: str = "14px"
    line_height: float = 1.5
    primary_color: str = "#000000"
    text_primary: str = "#000000"
    background: str = "#ffffff"
    mermaid_theme: str = "default"
    mermaid_font_family: str = "Inter, sans-serif"


class ProfileLoader:
    """
    Load theme profiles from configuration.
    
    Supports:
    - profiles.toml (new, recommended)
    - profiles.py (legacy, for backward compatibility)
    """
    
    def __init__(self, config_dir: str):
        """
        Initialize profile loader.
        
        Args:
            config_dir: Directory containing profiles.toml or profiles.py
        """
        self.config_dir = Path(config_dir)
        self.profiles: Dict[str, ThemeProfile] = {}
        self.toml_file = self.config_dir / "profiles.toml"
        self.py_file = self.config_dir / "profiles.py"
        
        # Try loading from TOML first, fall back to Python
        if self.toml_file.exists():
            self._load_toml()
        elif self.py_file.exists():
            self._load_python()
        else:
            raise FileNotFoundError(
                f"No profile configuration found in {config_dir}. "
                f"Create profiles.toml or profiles.py"
            )
    
    def _load_toml(self) -> None:
        """Load profiles from profiles.toml."""
        try:
            with open(self.toml_file, 'rb') as f:
                data = tomllib.load(f)
            
            if 'theme' not in data:
                raise ValueError("No [theme.*] sections found in profiles.toml")
            
            for theme_key, theme_data in data['theme'].items():
                profile = ThemeProfile(
                    name=theme_data.get('name', theme_key),
                    description=theme_data.get('description', ''),
                    mode=theme_data.get('mode', 'light'),
                    author=theme_data.get('author', 'unknown'),
                    version=theme_data.get('version', '1.0'),
                    css_file=theme_data.get('css_file', f'{theme_key}.css'),
                    header_height=theme_data.get('header_height', '1.5cm'),
                    footer_height=theme_data.get('footer_height', '1.2cm'),
                    margin_top=theme_data.get('margin_top', '2cm'),
                    margin_bottom=theme_data.get('margin_bottom', '2cm'),
                    margin_left=theme_data.get('margin_left', '1.8cm'),
                    margin_right=theme_data.get('margin_right', '1.8cm'),
                    base_font_size=theme_data.get('base_font_size', '14px'),
                    line_height=theme_data.get('line_height', 1.5),
                    primary_color=theme_data.get('primary_color', '#000000'),
                    text_primary=theme_data.get('text_primary', '#000000'),
                    background=theme_data.get('background', '#ffffff'),
                    mermaid_theme=theme_data.get('mermaid_theme', 'default'),
                    mermaid_font_family=theme_data.get('mermaid_font_family', 'Inter, sans-serif'),
                )
                self.profiles[theme_key] = profile
            
            print(f"[OK] Loaded {len(self.profiles)} profiles from profiles.toml")
        
        except Exception as e:
            print(f"[ERROR] Error loading profiles.toml: {e}")
            raise
    
    def _load_python(self) -> None:
        """Load profiles from profiles.py (legacy)."""
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("profiles", self.py_file)
            profiles_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(profiles_module)
            
            if not hasattr(profiles_module, 'PROFILES'):
                raise ValueError("No PROFILES dict found in profiles.py")
            
            profiles_dict = profiles_module.PROFILES
            
            for theme_key, profile_data in profiles_dict.items():
                profile = ThemeProfile(
                    name=profile_data.get('name', theme_key),
                    description=profile_data.get('description', ''),
                    mode=profile_data.get('mode', 'light'),
                    author=profile_data.get('author', 'unknown'),
                    version=profile_data.get('version', '1.0'),
                    css_file=profile_data.get('css_file', f'{theme_key}.css'),
                    **{k: v for k, v in profile_data.items() 
                       if k not in ['name', 'description', 'mode', 'author', 'version', 'css_file']}
                )
                self.profiles[theme_key] = profile
            
            print(f"[OK] Loaded {len(self.profiles)} profiles from profiles.py (legacy)")
        
        except Exception as e:
            print(f"[ERROR] Error loading profiles.py: {e}")
            raise
    
    def list_themes(self) -> List[str]:
        """Get list of all available themes."""
        return list(self.profiles.keys())
    
    def get_profile(self, theme_name: str) -> Optional[ThemeProfile]:
        """
        Get profile for a theme.
        
        Args:
            theme_name: Theme name (e.g., 'dark-pro')
        
        Returns:
            ThemeProfile or None if not found
        """
        return self.profiles.get(theme_name)
    
    def get_css_file(self, theme_name: str, styles_dir: str = "styles") -> Optional[str]:
        """
        Get full path to CSS file for a theme.
        
        Args:
            theme_name: Theme name
            styles_dir: Base styles directory (relative to config_dir parent)
        
        Returns:
            Full path to CSS file or None if not found
        """
        profile = self.get_profile(theme_name)
        if not profile:
            return None
        
        # Build path: config_dir/../styles/generated/dark-pro.css
        css_path = self.config_dir.parent / styles_dir / profile.css_file
        return str(css_path)
    
    def validate_css_files(self, styles_dir: str = "styles") -> Dict[str, bool]:
        """
        Validate that CSS files exist for all themes.
        
        Args:
            styles_dir: Base styles directory
        
        Returns:
            Dict mapping theme names to existence status
        """
        results = {}
        for theme_name in self.list_themes():
            css_path = self.get_css_file(theme_name, styles_dir)
            if css_path:
                exists = Path(css_path).exists()
                results[theme_name] = exists
                status = "[OK]" if exists else "[ERROR]"
                print(f"{status} {theme_name}: {css_path}")
            else:
                results[theme_name] = False
                print(f"[ERROR] {theme_name}: Profile not found")
        
        return results
    
    def summary(self) -> str:
        """Get summary of all profiles."""
        lines = [
            f"\n{'='*70}",
            f"PROFILE LOADER SUMMARY",
            f"{'='*70}",
            f"\nConfig directory: {self.config_dir}",
            f"Configuration file: {'profiles.toml' if self.toml_file.exists() else 'profiles.py (legacy)'}",
            f"\nTotal themes: {len(self.profiles)}",
            f"\nThemes:",
        ]
        
        for theme_name, profile in self.profiles.items():
            lines.append(
                f"  - {theme_name:20} | {profile.name:25} | {profile.mode:5} | {profile.css_file}"
            )
        
        lines.append(f"\n{'='*70}\n")
        return "\n".join(lines)


def main():
    """CLI interface for profile loader."""
    config_dir = "tools/pdf/config"
    styles_dir = "styles"
    
    print(f"\n{'='*70}")
    print("PROFILE LOADER - Load and validate theme profiles")
    print(f"{'='*70}\n")
    
    try:
        loader = ProfileLoader(config_dir)
        print(loader.summary())
        
        # Validate CSS files
        print("Validating CSS files...\n")
        results = loader.validate_css_files(styles_dir)
        
        valid_count = sum(1 for v in results.values() if v)
        total = len(results)
        
        print(f"\n{'='*70}")
        print(f"[OK] {valid_count}/{total} CSS files found")
        print(f"{'='*70}\n")
        
        sys.exit(0 if valid_count == total else 1)
    
    except Exception as e:
        print(f"\n[ERROR] Error: {e}\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
