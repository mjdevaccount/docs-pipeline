from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable


class IContainerExecutor(ABC):
    """Abstraction over a container runtime (e.g., Docker)."""

    @abstractmethod
    def is_available(self) -> bool:
        """Return True if the container runtime is available."""

    @abstractmethod
    def execute(
        self,
        command: str,
        args: Iterable[str],
        workspace_dir: Path,
    ) -> bool:
        """
        Execute a Structurizr CLI command inside a container.

        Args:
            command: CLI command (e.g. 'export', 'validate').
            args: Iterable of CLI arguments (e.g. ['--workspace', 'foo.dsl', ...]).
            workspace_dir: Directory that will be mounted into the container.
        """


class IWorkspaceExporter(ABC):
    """Abstraction for exporting a Structurizr workspace into diagrams."""

    @abstractmethod
    def supports_format(self, fmt: str) -> bool:
        """Return True if the exporter supports the given format."""

    @abstractmethod
    def export(
        self,
        workspace_path: Path,
        fmt: str,
        output_dir: Path,
    ) -> bool:
        """
        Export a workspace to a given format.

        Args:
            workspace_path: Path to workspace (.dsl or .json).
            fmt: Output format (mermaid, png, svg, html, json, ...).
            output_dir: Directory to write generated files to.
        """


