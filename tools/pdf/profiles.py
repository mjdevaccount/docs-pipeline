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

    Assumes this file lives under <repo>/tools/pdf/profiles.py.
    Going two parents up should land at the repo root in this workspace layout.
    """
    base = Path(__file__).parent
    repo_root = base.parent.parent
    return str(repo_root.joinpath(*parts))


PROFILES: Dict[str, DocumentProfile] = {
    # Default profile for the Reporting Manager documentation.
    "reporting-manager": DocumentProfile(
        name="reporting-manager",
        # Logo lives in the reporting-manager proposal assets.
        logo=_rel_from_repo_root("projects", "reporting-2.0", "proposals", "reporting-manager", "assets", "logo.png"),
        # Primary Playwright stylesheet with branded colors and typography.
        css=_rel_from_repo_root("tools", "pdf", "custom.css.playwright"),
        theme_config=_rel_from_repo_root("tools", "pdf", "pdf-mermaid-theme.json"),
        reference_docx=None,
    ),
    # Minimal, unbranded profile that can be used as a neutral default.
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


