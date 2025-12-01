from __future__ import annotations

from pathlib import Path

from ..core.interfaces import IContainerExecutor, IWorkspaceExporter
from ..core.exceptions import ExportError


class WorkspaceExporter(IWorkspaceExporter):
    """
    Export Structurizr workspaces via a container executor.

    This minimal implementation only knows how to call the Structurizr CLI
    `export` command; validation and serve flows remain in the legacy script.
    """

    SUPPORTED_FORMATS = {
        "mermaid",
        "plantuml",
        "png",
        "svg",
        "html",
        "json",
        "ilograph",
        "websequencediagrams",
        "graphviz",
    }

    def __init__(self, executor: IContainerExecutor) -> None:
        self._executor = executor

    def supports_format(self, fmt: str) -> bool:
        return fmt.lower() in self.SUPPORTED_FORMATS

    def export(
        self,
        workspace_path: Path,
        fmt: str,
        output_dir: Path,
        resource_dirs: list[Path] | None = None,
    ) -> bool:
        fmt = fmt.lower()
        if not self.supports_format(fmt):
            raise ExportError(
                f"Unsupported format: {fmt} "
                f"(valid: {', '.join(sorted(self.SUPPORTED_FORMATS))})"
            )

        workspace_path = workspace_path.resolve()
        if not workspace_path.exists():
            raise ExportError(f"Workspace file not found: {workspace_path}")

        # Structurizr CLI expects the workspace file to live inside the
        # mounted workspace directory. We mount the parent directory and
        # pass only the file name to the CLI.
        workspace_dir = workspace_path.parent
        workspace_name = workspace_path.name

        output_dir = output_dir.resolve()
        output_dir.mkdir(parents=True, exist_ok=True)

        # Use a path for --output that is relative to the workspace dir so
        # the same mount works in the container.
        try:
            output_rel = output_dir.relative_to(workspace_dir)
        except ValueError:
            # Different drive or unrelated path; fall back to absolute path.
            output_rel = output_dir

        args = [
            "--workspace",
            workspace_name,
            "--format",
            fmt,
            "--output",
            str(output_rel),
        ]

        # Prepare additional volume mounts for resource directories
        additional_volumes = None
        if resource_dirs:
            additional_volumes = []
            for resource_dir in resource_dirs:
                resource_dir = resource_dir.resolve()
                if resource_dir.exists():
                    # Mount to /resources/{name} in container
                    container_path = f"/resources/{resource_dir.name}"
                    additional_volumes.append((resource_dir, container_path))

        return self._executor.execute("export", args, workspace_dir, additional_volumes)


