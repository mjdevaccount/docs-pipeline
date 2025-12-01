from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any, Dict
from concurrent.futures import ThreadPoolExecutor, as_completed

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
            # Support both 'dsl' (legacy) and 'workspace' (new) keys
            workspace_file = diagrams_cfg.get("workspace") or diagrams_cfg.get("dsl")
            if not workspace_file:
                raise ValueError(f"diagrams section must specify 'workspace' or 'dsl' file path")
            
            workspace_path = (config_dir / workspace_file).resolve()
            
            # Optional workspace directory (for supporting files)
            workspace_dir = None
            if diagrams_cfg.get("workspace_dir"):
                workspace_dir = (config_dir / diagrams_cfg["workspace_dir"]).resolve()
            
            # Optional resource directories (images, styles, etc.)
            resources = None
            if diagrams_cfg.get("resources"):
                resources = [(config_dir / r).resolve() for r in diagrams_cfg["resources"]]
            
            diagrams = DiagramConfig(
                workspace=workspace_path,
                formats=list(diagrams_cfg.get("formats", ["mermaid"])),
                output_dir=(config_dir / diagrams_cfg.get("output_dir", "docs/diagrams")).resolve(),
                image=diagrams_cfg.get("image"),
                workspace_dir=workspace_dir,
                resources=resources,
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


def run_pipeline(config_path: Path, dry_run: bool = False, parallel: bool = False) -> bool:
    """
    Run the documentation pipeline described by the given YAML config.

    Args:
        config_path: Path to YAML configuration file
        dry_run: If True, show what would be generated without actually running
        parallel: If True, process documents in parallel (faster for multiple docs)

    Example config:

    workspaces:
      project-docs:
        diagrams:
          workspace: docs/architecture.dsl
          formats: ["mermaid"]
          output_dir: docs/diagrams
        documents:
          - input: docs/architecture-proposal.md
            output: docs/architecture-proposal.pdf
            format: pdf
            profile: default
    """
    cfg = _load_pipeline_config(config_path)
    all_ok = True

    print(f"\n[START] Starting pipeline: {config_path}")
    if dry_run:
        print("[DRY RUN] DRY RUN MODE - No files will be generated\n")
    if parallel:
        print("[PARALLEL] PARALLEL MODE - Documents will be processed concurrently\n")
    print(f"[INFO] Workspaces to process: {len(cfg.workspaces)}\n")

    for ws in cfg.workspaces:
        print(f"[WORKSPACE] {ws.name}")

        # 1. Diagrams
        if ws.diagrams:
            print(f"   [DIAGRAMS] Generating diagrams ({', '.join(ws.diagrams.formats)})...")
            
            # Use explicit workspace_dir if provided, otherwise use parent of workspace file
            workspace_file = ws.diagrams.workspace
            if ws.diagrams.workspace_dir:
                workspace_dir = ws.diagrams.workspace_dir
                print(f"      [INFO] Using workspace directory: {workspace_dir}")
                # Ensure workspace file is accessible from workspace_dir
                if not (workspace_dir / workspace_file.name).exists():
                    # Try to find workspace file relative to workspace_dir
                    if workspace_file.exists():
                        print(f"      [WARN] Workspace file {workspace_file.name} not in workspace_dir, using file location")
                        workspace_dir = workspace_file.parent
            else:
                workspace_dir = workspace_file.parent
            
            # Prepare resource directories for mounting
            resource_dirs = None
            if ws.diagrams.resources:
                resource_dirs = [r for r in ws.diagrams.resources if r.exists()]
                if resource_dirs:
                    print(f"      [INFO] Mounting {len(resource_dirs)} resource directory(ies)")
                else:
                    print(f"      [WARN] Resource directories specified but not found")
            
            for fmt in ws.diagrams.formats:
                if dry_run:
                    print(f"      [DRY RUN] Would export {fmt} to {ws.diagrams.output_dir}")
                    print(f"      [DRY RUN] Workspace: {workspace_file.name} from {workspace_dir}")
                    if resource_dirs:
                        print(f"      [DRY RUN] Would mount resources: {', '.join(str(r) for r in resource_dirs)}")
                    ok = True
                else:
                    # The export_workspace function uses the workspace file path
                    # The Docker executor will mount the workspace_dir and resource directories
                    ok = export_workspace(
                        workspace_file,
                        fmt,
                        ws.diagrams.output_dir,
                        image=ws.diagrams.image,
                        resource_dirs=resource_dirs,
                    )
                status = "[OK]" if ok else "[FAIL]"
                print(f"      {status} {fmt}")
                all_ok = all_ok and ok

        # 2. Documents
        if ws.documents:
            print(f"   [DOCUMENTS] Converting {len(ws.documents)} documents...")
            
            if parallel and not dry_run:
                # Parallel execution with configurable worker count
                max_workers = int(os.getenv('PIPELINE_WORKERS', os.cpu_count() or 4))
                with ThreadPoolExecutor(max_workers=max_workers) as executor:
                    futures = {}
                    for doc in ws.documents:
                        md_file = doc.input
                        if doc.output is not None:
                            output = doc.output
                        else:
                            suffix = ".pdf" if (doc.format or "pdf") == "pdf" else f".{doc.format}"
                            output = md_file.with_suffix(suffix)
                        
                        future = executor.submit(
                            _run_md2pdf,
                            md_file,
                            output,
                            doc.format,
                            doc.profile,
                        )
                        futures[future] = (doc, output)
                    
                    # Collect results as they complete
                    for i, future in enumerate(as_completed(futures), 1):
                        doc, output = futures[future]
                        ok = future.result()
                        status = "[OK]" if ok else "[FAIL]"
                        print(f"      {status} [{i}/{len(ws.documents)}] {doc.input.name}")
                        all_ok = all_ok and ok
            else:
                # Sequential execution
                for i, doc in enumerate(ws.documents, 1):
                    md_file = doc.input
                    if doc.output is not None:
                        output = doc.output
                    else:
                        suffix = ".pdf" if (doc.format or "pdf") == "pdf" else f".{doc.format}"
                        output = md_file.with_suffix(suffix)

                    if dry_run:
                        print(f"      [DRY RUN] Would convert: {md_file.name} -> {output.name}")
                        ok = True
                    else:
                        ok = _run_md2pdf(
                            md_file=md_file,
                            output=output,
                            fmt=doc.format,
                            profile=doc.profile,
                        )
                    status = "[OK]" if ok else "[FAIL]"
                    print(f"      {status} [{i}/{len(ws.documents)}] {doc.input.name}")
                    all_ok = all_ok and ok

        print()  # Blank line between workspaces

    if all_ok:
        print("[SUCCESS] Pipeline completed successfully!")
    else:
        print("[ERROR] Pipeline failed with errors")

    return all_ok


