"""
Theme Token Validator

Validates design tokens using Pydantic for color format, accessibility, and completeness.

Usage:
    validator = ThemeValidator('tools/pdf/config/design-tokens.yml')
    report = validator.validate()
    if not report.is_valid:
        print(report.errors)
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
import yaml

from pydantic import BaseModel, Field, field_validator, ValidationInfo

try:
    from pydantic_extra_types.color import Color
except ImportError:
    # Fallback if pydantic-extra-types not installed
    Color = str  # type: ignore


# ============================================================================
# COLOR UTILITIES
# ============================================================================

def parse_hex_color(color_str: str) -> Optional[Tuple[int, int, int]]:
    """Parse hex color to RGB tuple.
    
    Args:
        color_str: Color in #RRGGBB or #RGB format
    
    Returns:
        (R, G, B) tuple or None if invalid
    """
    color_str = color_str.strip()
    
    # #RRGGBB format
    if re.match(r'^#[0-9a-fA-F]{6}$', color_str):
        r = int(color_str[1:3], 16)
        g = int(color_str[3:5], 16)
        b = int(color_str[5:7], 16)
        return (r, g, b)
    
    # #RGB format
    if re.match(r'^#[0-9a-fA-F]{3}$', color_str):
        r = int(color_str[1] * 2, 16)
        g = int(color_str[2] * 2, 16)
        b = int(color_str[3] * 2, 16)
        return (r, g, b)
    
    return None


def calculate_luminance(rgb: Tuple[int, int, int]) -> float:
    """Calculate relative luminance of RGB color.
    
    Formula from WCAG 2.0 guidelines
    https://www.w3.org/TR/WCAG20/#relativeluminancedef
    """
    r, g, b = [c / 255.0 for c in rgb]
    
    r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
    g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
    b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
    
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def calculate_contrast_ratio(color1: str, color2: str) -> Optional[float]:
    """Calculate WCAG contrast ratio between two colors.
    
    Returns:
        Contrast ratio (1-21) or None if colors invalid
    """
    rgb1 = parse_hex_color(color1)
    rgb2 = parse_hex_color(color2)
    
    if not rgb1 or not rgb2:
        return None
    
    l1 = calculate_luminance(rgb1)
    l2 = calculate_luminance(rgb2)
    
    lighter = max(l1, l2)
    darker = min(l1, l2)
    
    return (lighter + 0.05) / (darker + 0.05)


def meets_wcag_aa(contrast: float) -> bool:
    """Check if contrast ratio meets WCAG AA (4.5:1 for normal text)."""
    return contrast >= 4.5


def meets_wcag_aaa(contrast: float) -> bool:
    """Check if contrast ratio meets WCAG AAA (7:1 for normal text)."""
    return contrast >= 7.0


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class ColorField(BaseModel):
    """Represents a single color value with validation."""
    value: str = Field(..., description="Hex color (e.g., #60a5fa)")
    
    @field_validator('value')
    @classmethod
    def validate_color_format(cls, v: str) -> str:
        """Validate color is valid hex format."""
        if not parse_hex_color(v):
            raise ValueError(
                f"Invalid hex color: {v}. Must be #RRGGBB or #RGB format."
            )
        return v


class ColorPair(BaseModel):
    """Two colors (text on background) with contrast validation."""
    background: str
    foreground: str
    min_contrast_ratio: float = 4.5  # WCAG AA default
    
    @field_validator('background', 'foreground')
    @classmethod
    def validate_colors(cls, v: str) -> str:
        if not parse_hex_color(v):
            raise ValueError(f"Invalid hex color: {v}")
        return v
    
    def check_contrast(self) -> Tuple[bool, Optional[float]]:
        """Check if colors have sufficient contrast.
        
        Returns:
            (is_valid, contrast_ratio)
        """
        ratio = calculate_contrast_ratio(self.background, self.foreground)
        if ratio is None:
            return False, None
        return ratio >= self.min_contrast_ratio, ratio


class GlobalTokens(BaseModel):
    """Global design tokens used across all themes."""
    fonts: Dict[str, str] = Field(..., description="Font families")
    spacing: Dict[str, str] = Field(..., description="Spacing scale")
    radius: Dict[str, str] = Field(..., description="Border radius scale")


class ThemeColors(BaseModel):
    """Color palette for a single theme."""
    primary: Dict[str, str]         # base, light, dark, muted
    text: Dict[str, str]            # primary, secondary, muted
    background: Dict[str, str]      # page, surface, subtle
    border: Dict[str, str]          # primary, subtle
    status: Dict[str, str]          # success, warning, error, info
    component: Dict[str, str]
    syntax: Dict[str, str]
    callout: Dict[str, Dict[str, Dict[str, str]]]  # [type][part][color]
    
    @field_validator('primary', 'text', 'background', 'border', 'status',
                     'component', 'syntax')
    @classmethod
    def validate_hex_colors(cls, v: Dict[str, str]) -> Dict[str, str]:
        """Validate all color values in dict are valid hex."""
        for key, color in v.items():
            if not parse_hex_color(color):
                raise ValueError(
                    f"Invalid hex color for {key}: {color}. "
                    f"Must be #RRGGBB or #RGB format."
                )
        return v


class MermaidTokens(BaseModel):
    """Mermaid-specific diagram color tokens."""
    primary_color: str
    primary_text_color: str
    primary_border_color: str
    line_color: str
    second_bkg_color: str
    tertiary_color: str
    text_color: str
    # ... and 50+ more fields
    # Simplified for Phase 1
    
    @field_validator('primary_color', 'primary_text_color', 'primary_border_color',
                     'line_color', 'second_bkg_color', 'tertiary_color', 'text_color')
    @classmethod
    def validate_color_fields(cls, v: str) -> str:
        """Validate Mermaid color values are hex."""
        if not parse_hex_color(v):
            raise ValueError(f"Invalid Mermaid color: {v}")
        return v


class ThemeMetadata(BaseModel):
    """Metadata for a theme."""
    name: str = Field(..., min_length=1)
    description: str = Field(..., min_length=10)
    mode: str = Field(..., pattern="^(light|dark)$")
    author: str = Field(default="docs-pipeline")
    version: str = Field(default="1.0")


class Theme(BaseModel):
    """Complete theme definition."""
    metadata: ThemeMetadata
    colors: ThemeColors
    mermaid: MermaidTokens


class DesignTokens(BaseModel):
    """Root design tokens document."""
    version: str = Field(..., pattern="^\d+\.\d+$")
    title: str
    description: str
    global_: Dict[str, Any] = Field(alias='global')
    themes: Dict[str, Theme]
    
    class Config:
        populate_by_name = True


# ============================================================================
# VALIDATION REPORT
# ============================================================================

@dataclass
class ContrastIssue:
    """Represents a contrast ratio issue."""
    theme: str
    category: str
    foreground_key: str
    background_key: str
    foreground_color: str
    background_color: str
    ratio: float
    required_ratio: float
    wcag_level: str  # "AA" or "AAA"
    
    def __str__(self) -> str:
        return (
            f"[{self.theme}] {self.category}: {self.foreground_key} on "
            f"{self.background_key}\n"
            f"  Contrast: {self.ratio:.2f}:1 (requires {self.required_ratio}:1 for "
            f"WCAG {self.wcag_level})\n"
            f"  Colors: {self.foreground_color} on {self.background_color}"
        )


@dataclass
class ValidationReport:
    """Report from theme validation."""
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    contrast_issues: List[ContrastIssue]
    summary: str
    
    def print_report(self):
        """Print formatted validation report."""
        print(f"\n{'='*70}")
        print(f"THEME VALIDATION REPORT")
        print(f"{'='*70}")
        print(f"Status: {'✅ VALID' if self.is_valid else '❌ INVALID'}")
        print(f"\n{self.summary}")
        
        if self.errors:
            print(f"\n❌ ERRORS ({len(self.errors)}):")
            for err in self.errors:
                print(f"  - {err}")
        
        if self.warnings:
            print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
            for warn in self.warnings:
                print(f"  - {warn}")
        
        if self.contrast_issues:
            print(f"\n🎨 CONTRAST ISSUES ({len(self.contrast_issues)}):")
            for issue in self.contrast_issues:
                print(f"  {issue}")
        
        print(f"\n{'='*70}\n")


# ============================================================================
# MAIN VALIDATOR
# ============================================================================

class ThemeValidator:
    """Validates design tokens from YAML file."""
    
    def __init__(self, tokens_file: str):
        self.tokens_file = Path(tokens_file)
        if not self.tokens_file.exists():
            raise FileNotFoundError(f"Tokens file not found: {tokens_file}")
        
        self.tokens: Optional[DesignTokens] = None
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.contrast_issues: List[ContrastIssue] = []
    
    def load_tokens(self) -> bool:
        """Load and parse YAML tokens file.
        
        Returns:
            True if loaded successfully, False otherwise
        """
        try:
            with open(self.tokens_file) as f:
                data = yaml.safe_load(f)
            
            # Validate against Pydantic model
            self.tokens = DesignTokens(**data)
            return True
        
        except yaml.YAMLError as e:
            self.errors.append(f"YAML parse error: {e}")
            return False
        except Exception as e:
            self.errors.append(f"Validation error: {e}")
            return False
    
    def validate_contrast_ratios(self, wcag_level: str = "AA") -> None:
        """Validate contrast ratios in all themes.
        
        Args:
            wcag_level: "AA" (4.5:1) or "AAA" (7:1)
        """
        if not self.tokens:
            return
        
        required_ratio = 7.0 if wcag_level == "AAA" else 4.5
        
        for theme_name, theme in self.tokens.themes.items():
            # Check text on background
            text_colors = theme.colors.text
            bg_colors = theme.colors.background
            
            for text_key, text_color in text_colors.items():
                for bg_key, bg_color in bg_colors.items():
                    ratio = calculate_contrast_ratio(bg_color, text_color)
                    
                    if ratio and ratio < required_ratio:
                        self.contrast_issues.append(
                            ContrastIssue(
                                theme=theme_name,
                                category="Text on Background",
                                foreground_key=text_key,
                                background_key=bg_key,
                                foreground_color=text_color,
                                background_color=bg_color,
                                ratio=ratio,
                                required_ratio=required_ratio,
                                wcag_level=wcag_level,
                            )
                        )
    
    def validate(self, wcag_level: str = "AA") -> ValidationReport:
        """Run complete validation.
        
        Args:
            wcag_level: WCAG compliance level ("AA" or "AAA")
        
        Returns:
            ValidationReport with all findings
        """
        self.errors.clear()
        self.warnings.clear()
        self.contrast_issues.clear()
        
        # Load tokens
        if not self.load_tokens():
            return ValidationReport(
                is_valid=False,
                errors=self.errors,
                warnings=self.warnings,
                contrast_issues=[],
                summary="Failed to load tokens file",
            )
        
        # Validate contrast ratios
        self.validate_contrast_ratios(wcag_level)
        
        # Generate summary
        theme_count = len(self.tokens.themes) if self.tokens else 0
        summary = (
            f"Validated {theme_count} themes with {wcag_level} accessibility requirements.\n"
            f"Errors: {len(self.errors)}, Warnings: {len(self.warnings)}, "
            f"Contrast Issues: {len(self.contrast_issues)}"
        )
        
        is_valid = len(self.errors) == 0 and len(self.contrast_issues) == 0
        
        return ValidationReport(
            is_valid=is_valid,
            errors=self.errors,
            warnings=self.warnings,
            contrast_issues=self.contrast_issues,
            summary=summary,
        )


# ============================================================================
# CLI INTERFACE
# ============================================================================

if __name__ == "__main__":
    import sys
    
    tokens_file = sys.argv[1] if len(sys.argv) > 1 else "tools/pdf/config/design-tokens.yml"
    wcag_level = sys.argv[2] if len(sys.argv) > 2 else "AA"
    
    validator = ThemeValidator(tokens_file)
    report = validator.validate(wcag_level)
    report.print_report()
    
    sys.exit(0 if report.is_valid else 1)
