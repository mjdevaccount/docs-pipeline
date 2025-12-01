"""
structurizr_tools
=================

SOLID-style helpers for running Structurizr CLI via Docker.

This package is intentionally small and focused. It does *not* replace the existing
`structurizr.py` CLI script; instead, it provides a programmatic API that other
tools (like a docs pipeline) can consume without having to shell out manually.
"""

from pathlib import Path
from .workspace.exporter import WorkspaceExporter
from .docker.executor import DockerExecutor


def export_workspace(
    workspace_path: Path,
    fmt: str,
    output_dir: Path,
    image: str | None = None,
    resource_dirs: list[Path] | None = None,
) -> bool:
    """
    Convenience API for exporting a single Structurizr DSL workspace.

    Args:
        workspace_path: Path to the .dsl or .json workspace file.
        fmt: Export format (e.g. 'mermaid', 'svg', 'png', 'html', 'json').
        output_dir: Directory where generated files will be written.
        image: Optional Docker image override (defaults to structurizr/cli:latest).
        resource_dirs: Optional list of resource directories to mount in Docker.
    """
    executor = DockerExecutor(image=image)
    exporter = WorkspaceExporter(executor)
    return exporter.export(workspace_path, fmt, output_dir, resource_dirs)


