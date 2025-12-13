from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional


@dataclass(frozen=True)
class DocumentProfile:
    """
    Describes a reusable document profile (brand, layout, assets).

    The goal is to make it easy to support multiple organizations and
    document families without hard-coding defaults into the conversion
    pipeline. New profiles can be added here or eventually loaded from
    config files.
    """

    name: str
    logo: Optional[str] = None
    css: Optional[str] = None
    theme_config: Optional[str] = None
    reference_docx: Optional[str] = None


def _rel_from_repo_root(*parts: str) -> str:
    """
    Build a path relative to the repository root.

    Assumes this file lives under <repo>/tools/pdf/config/profiles.py.
    Going three parents up should land at the repo root in this workspace layout.
    """
    base = Path(__file__).parent  # tools/pdf/config
    repo_root = base.parent.parent.parent  # Go up: config -> pdf -> tools -> repo_root
    return str(repo_root.joinpath(*parts))


PROFILES: Dict[str, DocumentProfile] = {
    # Tech Whitepaper - Default professional engineering documentation style
    # Clean, blue accents, generous margins, perfect for technical specs
    "tech-whitepaper": DocumentProfile(
        name="tech-whitepaper",
        logo=None,
        css=_rel_from_repo_root("tools", "pdf", "styles", "generated", "tech-whitepaper.css"),
        theme_config=_rel_from_repo_root("tools", "pdf", "pdf-mermaid-theme.json"),
        reference_docx=None,
    ),
    
    # Dark Pro - Modern dark theme for on-screen viewing
    # High contrast, dramatic presentation, neon accents
    "dark-pro": DocumentProfile(
        name="dark-pro",
        logo=None,
        css=_rel_from_repo_root("tools", "pdf", "styles", "generated", "dark-pro.css"),
        theme_config=_rel_from_repo_root("tools", "pdf", "pdf-mermaid-theme.json"),
        reference_docx=None,
    ),
    
    # Minimalist - Clean, spacious design with maximum whitespace
    # Thin typography, subtle colors, perfect for architecture docs
    "minimalist": DocumentProfile(
        name="minimalist",
        logo=None,
        css=_rel_from_repo_root("tools", "pdf", "styles", "generated", "minimalist.css"),
        theme_config=_rel_from_repo_root("tools", "pdf", "pdf-mermaid-theme.json"),
        reference_docx=None,
    ),
    
    # Enterprise Blue - Corporate-friendly, conservative styling
    # Blue and gray color scheme, structured layout, perfect for business docs
    "enterprise-blue": DocumentProfile(
        name="enterprise-blue",
        logo=None,
        css=_rel_from_repo_root("tools", "pdf", "styles", "generated", "enterprise-blue.css"),
        theme_config=_rel_from_repo_root("tools", "pdf", "pdf-mermaid-theme.json"),
        reference_docx=None,
    ),
    
    # Legacy profiles (for backward compatibility)
    "project-docs": DocumentProfile(
        name="project-docs",
        logo=None,
        css=_rel_from_repo_root("tools", "pdf", "custom.css.playwright"),
        theme_config=_rel_from_repo_root("tools", "pdf", "pdf-mermaid-theme.json"),
        reference_docx=None,
    ),
    "neutral": DocumentProfile(
        name="neutral",
        logo=None,
        css=None,
        theme_config=_rel_from_repo_root("tools", "pdf", "pdf-mermaid-theme.json"),
        reference_docx=None,
    ),
}


def get_profile(name: str) -> Optional[DocumentProfile]:
    """Return a profile by name (case-insensitive) if defined."""
    key = name.lower()
    for profile_name, profile in PROFILES.items():
        if profile_name.lower() == key:
            return profile
    return None


