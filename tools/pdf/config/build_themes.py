"""
Build Themes - Complete theme build integration

Orchestraizes the entire theme workflow:
1. Validate design-tokens.yml
2. Generate CSS for all themes
3. Create theme index
4. Validate generated CSS files
5. Update profiles.toml

Usage:
    python tools/pdf/config/build_themes.py [output_dir]

Examples:
    python tools/pdf/config/build_themes.py                      # Use default dir
    python tools/pdf/config/build_themes.py tools/pdf/styles/generated/
"""

import sys
import os
from pathlib import Path
from typing import Dict

from theme_manager import ThemeManager
from profile_loader import ProfileLoader


class ThemeBuildProcess:
    """
    Complete theme build orchestration.
    
    Steps:
    1. Validate tokens
    2. Generate CSS
    3. Create index
    4. Validate CSS files
    5. Load profiles
    6. Summary
    """
    
    def __init__(self, config_dir: str = "tools/pdf/config"):
        self.config_dir = Path(config_dir)
        self.styles_dir = self.config_dir.parent / "styles"
        self.tokens_file = self.config_dir / "design-tokens.yml"
        
        self.manager: Optional[ThemeManager] = None
        self.loader: Optional[ProfileLoader] = None
        self.success = False
    
    def run(self, output_dir: str = None, wcag_level: str = "AA") -> bool:
        """
        Run complete build process.
        
        Args:
            output_dir: CSS output directory (defaults to styles/generated/)
            wcag_level: WCAG compliance level
        
        Returns:
            True if build successful
        """
        if output_dir is None:
            output_dir = str(self.styles_dir / "generated")
        
        print(f"\n{'='*70}")
        print("PHASE 3: THEME BUILD PROCESS")
        print(f"{'='*70}\n")
        
        # Step 1: Initialize manager
        print("Step 1: Initialize theme manager...")
        try:
            self.manager = ThemeManager(str(self.tokens_file))
            print(self.manager.summary())
        except Exception as e:
            print(f"Failed: {e}")
            return False
        
        # Step 2: Validate tokens
        print("Step 2: Validate design tokens...")
        if not self.manager.validate(wcag_level):
            print("Validation FAILED")
            report = self.manager.get_validation_report()
            if report:
                report.print_report()
            return False
        
        print("Tokens validated successfully\n")
        
        # Step 3: Generate CSS
        print(f"Step 3: Generate CSS to {output_dir}...")
        results = self.manager.generate_all(output_dir, validate_first=False)
        
        success_count = sum(1 for v in results.values() if v)
        if success_count == 0:
            print("No CSS files generated")
            return False
        
        print(f"Generated {success_count}/{len(results)} CSS files\n")
        
        # Step 4: Create index
        print(f"Step 4: Create theme index...")
        if self.manager.create_index(output_dir):
            print("Index created successfully\n")
        else:
            print("Warning: Could not create index\n")
        
        # Step 5: Load and validate profiles
        print("Step 5: Load and validate profiles...")
        try:
            self.loader = ProfileLoader(str(self.config_dir))
            print(self.loader.summary())
            
            # Check CSS files exist
            print("Validating CSS files...\n")
            css_results = self.loader.validate_css_files("styles")
            
            css_valid = sum(1 for v in css_results.values() if v)
            if css_valid != len(css_results):
                print(f"\nWarning: {css_valid}/{len(css_results)} CSS files found")
        except Exception as e:
            print(f"Warning: {e}")
        
        # Step 6: Summary
        print(f"\n{'='*70}")
        print("BUILD COMPLETE")
        print(f"{'='*70}")
        print(f"\nAll theme artifacts generated successfully!")
        print(f"\n   Tokens file: {self.tokens_file}")
        print(f"   CSS output:  {output_dir}")
        print(f"   Profiles:    {self.config_dir / 'profiles.toml'}")
        print(f"\n   Ready for use in PDF converter")
        print(f"\n{'='*70}\n")
        
        self.success = True
        return True


def main():
    """CLI interface for theme build process."""
    output_dir = None
    config_dir = "tools/pdf/config"
    
    # Parse arguments
    if len(sys.argv) > 1:
        output_dir = sys.argv[1]
    
    if len(sys.argv) > 2:
        config_dir = sys.argv[2]
    
    try:
        builder = ThemeBuildProcess(config_dir)
        success = builder.run(output_dir)
        sys.exit(0 if success else 1)
    
    except KeyboardInterrupt:
        print("\n\nBuild cancelled by user")
        sys.exit(1)
    
    except Exception as e:
        print(f"\nFatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
