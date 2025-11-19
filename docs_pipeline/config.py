from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class DiagramConfig:
    workspace: Path
    formats: List[str]
    output_dir: Path
    image: Optional[str] = None


@dataclass
class DocumentConfig:
    input: Path
    output: Optional[Path] = None
    format: Optional[str] = None  # pdf | docx | html
    profile: Optional[str] = None


@dataclass
class WorkspaceConfig:
    name: str
    diagrams: Optional[DiagramConfig] = None
    documents: List[DocumentConfig] | None = None


@dataclass
class PipelineConfig:
    workspaces: List[WorkspaceConfig]


