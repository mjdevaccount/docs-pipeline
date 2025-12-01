from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any, Dict

import yaml

from .config import PipelineConfig, WorkspaceConfig, DiagramConfig, DocumentConfig
from tools.structurizr.structurizr_tools import export_workspace


def _load_pipeline_config(path: Path) -> PipelineConfig:
    """
    Load pipeline configuration from YAML file.
    All paths in the config are resolved relative to the config file's directory.
    """
    config_dir = path.parent.resolve()
    data: Dict[str, Any]
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}

    workspaces: list[WorkspaceConfig] = []
    for name, cfg in (data.get("workspaces") or {}).items():
        diagrams_cfg = cfg.get("diagrams")
        diagrams = None
        if diagrams_cfg:
            diagrams = DiagramConfig(
                workspace=(config_dir / diagrams_cfg["dsl"]).resolve(),
                formats=list(diagrams_cfg.get("formats", ["mermaid"])),
                output_dir=(config_dir / diagrams_cfg.get("output_dir", "docs/diagrams")).resolve(),
                image=diagrams_cfg.get("image"),
            )

        docs_cfg = cfg.get("documents") or []
        documents = [
            DocumentConfig(
                input=(config_dir / d["input"]).resolve(),
                output=(config_dir / d["output"]).resolve() if d.get("output") else None,
                format=d.get("format"),
                profile=d.get("profile"),
            )
            for d in docs_cfg
        ]

        workspaces.append(
            WorkspaceConfig(
                name=name,
                diagrams=diagrams,
                documents=documents,
            )
        )

    return PipelineConfig(workspaces=workspaces)


def _run_md2pdf(
    md_file: Path,
    output: Path | None,
    fmt: str | None,
    profile: str | None,
) -> bool:
    """
    Invoke the existing md2pdf.py CLI for a single document.

    This keeps the docs pipeline thin and lets md2pdf own all
    conversion concerns (frontmatter, diagrams, CSS, etc.).
    """
    script = Path(__file__).parent.parent / "pdf" / "md2pdf.py"
    cmd = ["python", str(script), str(md_file)]
    if output is not None:
        cmd.append(str(output))
    if fmt:
        cmd.extend(["--format", fmt])
    if profile:
        cmd.extend(["--profile", profile])

    result = subprocess.run(cmd, text=True)
    return result.returncode == 0


def run_pipeline(config_path: Path) -> bool:
    """
    Run the documentation pipeline described by the given YAML config.

    Example config:

    workspaces:
      reporting-manager:
        diagrams:
          dsl: archive/reporting-manager-docs/ReportingManager_Phase0_Architecture.dsl
          formats: ["mermaid"]
          output_dir: archive/reporting-manager-docs/diagrams
        documents:
          - input: archive/reporting-manager-docs/ReportingManager_ArchitectureProposal_Enhanced.md
            output: archive/reporting-manager-docs/ReportingManager_ArchitectureProposal_Enhanced.pdf
            format: pdf
            profile: reporting-manager
    """
    cfg = _load_pipeline_config(config_path)
    all_ok = True

    for ws in cfg.workspaces:
        # 1. Diagrams
        if ws.diagrams:
            for fmt in ws.diagrams.formats:
                ok = export_workspace(
                    ws.diagrams.workspace,
                    fmt,
                    ws.diagrams.output_dir,
                    image=ws.diagrams.image,
                )
                all_ok = all_ok and ok

        # 2. Documents
        for doc in ws.documents or []:
            md_file = doc.input
            if doc.output is not None:
                output = doc.output
            else:
                suffix = ".pdf" if (doc.format or "pdf") == "pdf" else f".{doc.format}"
                output = md_file.with_suffix(suffix)

            ok = _run_md2pdf(
                md_file=md_file,
                output=output,
                fmt=doc.format,
                profile=doc.profile,
            )
            all_ok = all_ok and ok

    return all_ok


