from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Iterable, List

from ..core.interfaces import IContainerExecutor
from ..core.exceptions import DockerError


DEFAULT_CLI_IMAGE = "structurizr/cli:latest"


def _normalize_path_for_docker(path: Path) -> str:
    """
    Convert a local path to a Docker-compatible path.

    Mirrors the semantics of `normalize_path_for_docker` in the legacy
    `structurizr.py` script but kept local to this module so the new
    API does not depend on the script.
    """
    s = str(path.resolve())
    if subprocess.os.name == "nt":
        s = s.replace("\\", "/")
        if ":" in s:
            drive, rest = s.split(":", 1)
            s = f"/{drive.lower()}{rest}"
    return s


class DockerExecutor(IContainerExecutor):
    """
    Minimal Docker-based executor for Structurizr CLI.

    High-level tools should depend on this abstraction instead of
    shelling out directly to `docker` with ad-hoc commands.
    """

    def __init__(self, image: str | None = None) -> None:
        self._image = image or DEFAULT_CLI_IMAGE

    def is_available(self) -> bool:
        """Return True if `docker` is on PATH and responsive."""
        try:
            subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                check=True,
                text=True,
            )
            return True
        except (subprocess.CalledProcessError, FileNotFoundError):
            return False

    def execute(
        self,
        command: str,
        args: Iterable[str],
        workspace_dir: Path,
    ) -> bool:
        if not self.is_available():
            raise DockerError("Docker is not available on PATH or not running.")

        workspace_dir_norm = _normalize_path_for_docker(workspace_dir)

        docker_cmd: List[str] = [
            "docker",
            "run",
            "--rm",
            "-v",
            f"{workspace_dir_norm}:/workspace",
            "-w",
            "/workspace",
            self._image,
            command,
        ]
        docker_cmd.extend(list(args))

        try:
            result = subprocess.run(
                docker_cmd,
                check=True,
                capture_output=True,
                text=True,
            )
            if result.stdout:
                print(result.stdout)
            if result.stderr:
                # Structurizr sometimes writes non-error info to stderr;
                # we only surface it, not treat as failure.
                print(result.stderr)
            return result.returncode == 0
        except subprocess.CalledProcessError as exc:
            raise DockerError(
                f"Docker command failed with exit code {exc.returncode}: {exc.stderr}"
            ) from exc


