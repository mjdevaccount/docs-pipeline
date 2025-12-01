#!/usr/bin/env python3
"""
Project Documentation Architecture Proposal – Scaling Verification
==================================================================

This test uses the same Playwright-based layout analysis pipeline as the
other scaling tests, but runs it against the *actual* generated HTML for:

  archive/reporting-manager-docs/ReportingManager_ArchitectureProposal_Enhanced.md

The goal is to:
  - Confirm all diagram blocks have reasonable available height.
  - Confirm scale factors are within a sane band for this real-world doc.
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright_pdf.browser import open_page  # type: ignore[import]
from playwright_pdf.styles import inject_pagination_css  # type: ignore[import]
from playwright_pdf.dom_analyzer import analyze_layout  # type: ignore[import]
from playwright_pdf.layout_transformer import compute_scaling  # type: ignore[import]
from playwright_pdf.config import CoverConfig  # type: ignore[import]
from playwright_pdf.decorators.cover import inject_cover_page  # type: ignore[import]
from playwright_pdf.decorators.toc import inject_toc  # type: ignore[import]

from convert_final import markdown_to_html, extract_metadata  # type: ignore[import]


async def run_project_docs_scaling_test() -> bool:
    # tests/ -> pdf/ -> tools/ -> repo_root
    repo_root = Path(__file__).parent.parent.parent.parent
    # Update this path to point to your actual test document
    md_file = (
        repo_root
        / "docs"
        / "examples"
        / "test-document.md"  # Update to your test document path
    )

    if not md_file.exists():
        print(f"[WARN] Test document not found: {md_file}")
        print(f"[INFO] Update the path in this test to point to your test document")
        return False

    # 1) Convert Markdown → HTML once using the same preprocessor as md2pdf
    work_dir = Path(__file__).parent / "test_outputs"
    work_dir.mkdir(parents=True, exist_ok=True)
    html_file = work_dir / "ReportingManager_ArchitectureProposal_Enhanced.html"

    print(f"[INFO] Rendering Markdown to HTML for analysis: {md_file}")
    markdown_to_html(str(md_file), str(html_file))

    # 2) Run Playwright analysis on the generated HTML
    async with open_page(html_file, verbose=False) as (browser, page):
        await page.wait_for_load_state("networkidle")
        await inject_pagination_css(page, verbose=False)

        # Use frontmatter metadata for a realistic cover page
        metadata, _ = extract_metadata(md_file.read_text(encoding="utf-8"))
        cover_config = CoverConfig(
            title=metadata.get("title", "Project Documentation Architecture Proposal"),
            author=metadata.get("author", "Unknown"),
            organization=metadata.get("organization", "Unknown"),
            date=str(metadata.get("date", "")),
        )
        await inject_cover_page(page, cover_config, verbose=False)
        await inject_toc(page, verbose=False)
        await page.wait_for_timeout(1000)

        analysis = await analyze_layout(page, verbose=True)
        decisions = compute_scaling(analysis)

        if not analysis.diagram_blocks:
            print("[FAIL] No diagram blocks detected in proposal.")
            return False

        print(f"[INFO] Found {len(analysis.diagram_blocks)} diagram blocks.")
        all_ok = True

        for i, block in enumerate(analysis.diagram_blocks, 1):
            print(f"\n  Block {i}: '{block.heading_text}'")
            print(f"    Available height: {block.available_height:.0f}px")
            print(f"    Diagram height: {block.diagram_height:.0f}px")
            print(f"    Overflow ratio: {block.overflow_ratio:.2f}x")

            # Hard guard: available height must be positive and not tiny.
            if block.available_height <= 0:
                print("    [FAIL] Available height is non-positive.")
                all_ok = False
            elif block.available_height < 300:
                print("    [WARN] Available height is quite small (<300px).")

        if not decisions:
            print("[FAIL] No scaling decisions computed for proposal.")
            return False

        print(f"\n[INFO] Found {len(decisions)} scaling decisions.")
        for i, dec in enumerate(decisions, 1):
            print(
                f"  Decision {i}: scale_factor={dec.scale_factor:.2f}x, "
                f"mode={'block' if dec.scale_entire_block else 'diagram-only'}"
            )
            # Require scale factors to be in a sane band.
            if not (0.2 <= dec.scale_factor <= 1.0):
                print(
                    f"    [FAIL] Scale factor {dec.scale_factor:.2f}x "
                    "outside expected range [0.2, 1.0]."
                )
                all_ok = False

        return all_ok


async def main() -> bool:
    print("\n" + "=" * 70)
    print("PROJECT DOCUMENTATION – ARCHITECTURE PROPOSAL SCALING TEST")
    print("=" * 70)
    ok = await run_project_docs_scaling_test()
    print("\nResult:", "OK" if ok else "FAIL")
    return ok


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)


