from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class DiagramConfig:
    workspace: Path  # Path to .dsl or .json workspace file
    formats: List[str]
    output_dir: Path
    image: Optional[str] = None
    workspace_dir: Optional[Path] = None  # Optional: directory containing workspace + supporting files
    resources: Optional[List[Path]] = None  # Optional: additional resource directories (images, styles, etc.)


@dataclass
class DocumentConfig:
    input: Path
    output: Optional[Path] = None
    format: Optional[str] = None  # pdf | docx | html
    profile: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None  # Document-specific metadata (overrides workspace defaults)


@dataclass
class WorkspaceConfig:
    name: str
    diagrams: Optional[DiagramConfig] = None
    documents: List[DocumentConfig] | None = None
    defaults: Optional[Dict[str, Any]] = None  # Workspace-level default metadata


@dataclass
class PipelineConfig:
    workspaces: List[WorkspaceConfig]


