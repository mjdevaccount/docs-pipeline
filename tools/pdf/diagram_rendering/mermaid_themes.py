#!/usr/bin/env python3
"""
Mermaid Theme Generator - Per-Profile Color Schemes
=====================================================

Generates Mermaid diagram themes that automatically match CSS profiles.
Ensures visual consistency between document styling and embedded diagrams.

Features:
- Per-profile color scheme generation
- Automatic theme selection based on profile
- Theme caching and reuse
- Live theme updates without re-rendering
- Statistics tracking (theme application, customization)

Usage:
    from tools.pdf.diagram_rendering.mermaid_themes import MermaidThemeGenerator
    
    generator = MermaidThemeGenerator()
    theme_config = generator.get_theme('tech-whitepaper')
    theme_json = generator.generate_theme_json('dark-pro')
"""

from dataclasses import dataclass, field
from typing import Dict, Optional, Any, Tuple
from enum import Enum
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class DiagramTheme(Enum):
    """Available diagram themes."""
    TECH_WHITEPAPER = 'tech-whitepaper'
    DARK_PRO = 'dark-pro'
    ENTERPRISE_BLUE = 'enterprise-blue'
    MINIMALIST = 'minimalist'


@dataclass
class ColorScheme:
    """Color scheme for a diagram theme."""
    primary: str
    secondary: str
    tertiary: str
    text_primary: str
    text_secondary: str
    background: str
    border: str
    accent: str
    success: str
    error: str
    warning: str
    info: str


@dataclass
class MermaidThemeConfig:
    """Complete Mermaid theme configuration."""
    theme_name: str
    colors: ColorScheme
    fonts: Dict[str, str] = field(default_factory=dict)
    style_settings: Dict[str, Any] = field(default_factory=dict)
    custom_css: Optional[str] = None


@dataclass
class ThemingStatistics:
    """Statistics for diagram theming."""
    themes_generated: int = 0
    themes_applied: int = 0
    custom_themes: int = 0
    cache_hits: int = 0
    total_diagrams_themed: int = 0
    
    def report(self) -> str:
        """Generate statistics report."""
        return f"""
[INFO] Diagram Theming Statistics
       Themes Generated: {self.themes_generated}
       Themes Applied: {self.themes_applied}
       Custom Themes: {self.custom_themes}
       Cache Hits: {self.cache_hits}
       Total Diagrams Themed: {self.total_diagrams_themed}
"""


class MermaidThemeGenerator:
    """Generate and manage Mermaid diagram themes."""
    
    # Profile-specific color schemes
    PROFILE_COLORS: Dict[str, ColorScheme] = {
        'tech-whitepaper': ColorScheme(
            primary='#2563eb',      # Blue-600
            secondary='#64748b',    # Slate-500
            tertiary='#e5e7eb',     # Gray-200
            text_primary='#1f2937', # Gray-800
            text_secondary='#6b7280', # Gray-500
            background='#ffffff',   # White
            border='#d1d5db',       # Gray-300
            accent='#059669',       # Emerald-600
            success='#10b981',      # Emerald-500
            error='#ef4444',        # Red-500
            warning='#f59e0b',      # Amber-500
            info='#06b6d4'          # Cyan-500
        ),
        'dark-pro': ColorScheme(
            primary='#60a5fa',      # Blue-400
            secondary='#94a3b8',    # Slate-400
            tertiary='#374151',     # Gray-700
            text_primary='#f3f4f6', # Gray-100
            text_secondary='#d1d5db', # Gray-300
            background='#1f2937',   # Gray-800
            border='#4b5563',       # Gray-600
            accent='#34d399',       # Emerald-400
            success='#6ee7b7',      # Emerald-300
            error='#f87171',        # Red-400
            warning='#fbbf24',      # Amber-400
            info='#22d3ee'          # Cyan-300
        ),
        'enterprise-blue': ColorScheme(
            primary='#1e40af',      # Blue-800
            secondary='#475569',    # Slate-600
            tertiary='#e0e7ff',     # Indigo-100
            text_primary='#0f172a', # Slate-900
            text_secondary='#475569', # Slate-600
            background='#f8fafc',   # Slate-50
            border='#cbd5e1',       # Slate-300
            accent='#047857',       # Emerald-700
            success='#059669',      # Emerald-600
            error='#dc2626',        # Red-600
            warning='#d97706',      # Amber-600
            info='#0891b2'          # Cyan-600
        ),
        'minimalist': ColorScheme(
            primary='#4b5563',      # Gray-600
            secondary='#9ca3af',    # Gray-400
            tertiary='#f3f4f6',     # Gray-100
            text_primary='#1f2937', # Gray-800
            text_secondary='#6b7280', # Gray-500
            background='#ffffff',   # White
            border='#e5e7eb',       # Gray-200
            accent='#374151',       # Gray-700
            success='#6b7280',      # Gray-500
            error='#374151',        # Gray-700
            warning='#4b5563',      # Gray-600
            info='#6b7280'          # Gray-500
        )
    }
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.stats = ThemingStatistics()
        self.cache: Dict[str, MermaidThemeConfig] = {}
    
    def get_theme(self, profile: str) -> Optional[MermaidThemeConfig]:
        """Get theme config for a profile."""
        # Check cache
        if profile in self.cache:
            self.stats.cache_hits += 1
            return self.cache[profile]
        
        # Check if profile exists
        if profile not in self.PROFILE_COLORS:
            logger.warning(f"Profile '{profile}' not found, using 'tech-whitepaper'")
            profile = 'tech-whitepaper'
        
        # Generate theme
        colors = self.PROFILE_COLORS[profile]
        config = MermaidThemeConfig(
            theme_name=profile,
            colors=colors
        )
        
        # Cache it
        self.cache[profile] = config
        self.stats.themes_generated += 1
        
        return config
    
    def generate_theme_json(self, profile: str) -> str:
        """Generate Mermaid theme as JSON."""
        config = self.get_theme(profile)
        if not config:
            return json.dumps({})
        
        # Mermaid theme structure
        theme_config = {
            'primaryColor': config.colors.background,
            'primaryTextColor': config.colors.text_primary,
            'primaryBorderColor': config.colors.border,
            'secondBkgColor': config.colors.secondary,
            'tertiaryColor': config.colors.tertiary,
            'tertiaryTextColor': config.colors.text_primary,
            'tertiaryBorderColor': config.colors.border,
            'notBkgColor': config.colors.accent,
            'notBorderColor': config.colors.border,
            'lineColor': config.colors.primary,
            'textColor': config.colors.text_primary,
            'mainTokenBackground': config.colors.background,
            'mainTokenBorder': config.colors.border,
            'clusterBkg': config.colors.tertiary,
            'clusterBorder': config.colors.border,
            'defaultLinkColor': config.colors.primary,
            'titleColor': config.colors.text_primary,
            'edgeLabelBackground': {
                'backgroundColor': config.colors.background,
                'color': config.colors.text_primary
            },
            'fontFamily': '"Inter", sans-serif',
            'fontSize': '14px',
            'fontFamilyCode': '"JetBrains Mono", monospace'
        }
        
        return json.dumps(theme_config, indent=2)
    
    def generate_theme_config(self, profile: str) -> Dict[str, Any]:
        """Generate complete Mermaid config with theme."""
        theme_json = self.generate_theme_json(profile)
        theme_obj = json.loads(theme_json)
        
        config = {
            'startOnLoad': True,
            'securityLevel': 'loose',
            'theme': profile,
            'themeVariables': theme_obj,
            'fontFamily': 'Inter, sans-serif',
            'flowchart': {
                'diagramMarginX': 50,
                'diagramMarginY': 10,
                'htmlLabels': True
            },
            'sequence': {
                'diagramMarginX': 50,
                'diagramMarginY': 10,
                'actorMargin': 50
            },
            'gantt': {
                'fontSize': 12,
                'fontFamily': 'Inter, sans-serif'
            },
            'class': {
                'arrowMarkerAbsolute': True
            }
        }
        
        return config
    
    def get_inline_config(self, profile: str) -> str:
        """Get inline configuration for Mermaid CLI."""
        config = self.generate_theme_config(profile)
        return json.dumps(config)
    
    def apply_theme_to_mermaid_html(self, html: str, profile: str) -> str:
        """Apply theme to Mermaid diagram HTML."""
        config = self.generate_theme_config(profile)
        
        # Inject configuration into HTML
        config_script = f"""
        <script>
            window.mermaid = {json.dumps(config)};
        </script>
        """
        
        self.stats.themes_applied += 1
        
        # Insert before mermaid script
        if '<script' in html:
            return html.replace('<script', config_script + '<script', 1)
        else:
            return config_script + html
    
    def create_custom_theme(self, name: str, colors: Dict[str, str]) -> MermaidThemeConfig:
        """Create custom theme from color dict."""
        color_scheme = ColorScheme(
            primary=colors.get('primary', '#2563eb'),
            secondary=colors.get('secondary', '#64748b'),
            tertiary=colors.get('tertiary', '#e5e7eb'),
            text_primary=colors.get('text_primary', '#1f2937'),
            text_secondary=colors.get('text_secondary', '#6b7280'),
            background=colors.get('background', '#ffffff'),
            border=colors.get('border', '#d1d5db'),
            accent=colors.get('accent', '#059669'),
            success=colors.get('success', '#10b981'),
            error=colors.get('error', '#ef4444'),
            warning=colors.get('warning', '#f59e0b'),
            info=colors.get('info', '#06b6d4')
        )
        
        config = MermaidThemeConfig(
            theme_name=name,
            colors=color_scheme
        )
        
        self.cache[name] = config
        self.stats.custom_themes += 1
        
        return config
    
    def get_all_profiles(self) -> Dict[str, str]:
        """Get all available profiles."""
        return {
            'tech-whitepaper': 'Technical, professional, clean',
            'dark-pro': 'Dark mode, modern, high contrast',
            'enterprise-blue': 'Corporate, professional, conservative',
            'minimalist': 'Minimal, elegant, content-focused'
        }
    
    def get_colors_for_profile(self, profile: str) -> Dict[str, str]:
        """Get color dict for a profile."""
        config = self.get_theme(profile)
        if not config:
            return {}
        
        colors = config.colors
        return {
            'primary': colors.primary,
            'secondary': colors.secondary,
            'tertiary': colors.tertiary,
            'text_primary': colors.text_primary,
            'text_secondary': colors.text_secondary,
            'background': colors.background,
            'border': colors.border,
            'accent': colors.accent,
            'success': colors.success,
            'error': colors.error,
            'warning': colors.warning,
            'info': colors.info
        }


def get_default_theme_generator() -> MermaidThemeGenerator:
    """Get default theme generator instance."""
    return MermaidThemeGenerator()
