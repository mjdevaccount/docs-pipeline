#!/usr/bin/env python3
"""
Project Documentation Layout Visual Test
=======================================
Generates the Project Documentation Architecture Proposal PDF using the
Playwright pipeline and verifies that the pipeline runs end-to-end.

This is a document-specific visual validation: it ensures that
the exact markdown document we're tuning can be rendered via the
Playwright stack using the same profile and options as the CLI,
and produces a PDF for manual inspection.
"""
import asyncio
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List

import yaml  # type: ignore

sys.path.insert(0, str(Path(__file__).parent.parent))

from convert_final import markdown_to_html  # type: ignore
from profiles import get_profile  # type: ignore
from playwright_pdf.config import PdfGenerationConfig  # type: ignore
from playwright_pdf.pipeline import generate_pdf  # type: ignore
from playwright_pdf.browser import open_page  # type: ignore
from playwright_pdf.styles import (  # type: ignore
    inject_fonts,
    inject_pagination_css,
    inject_custom_css,
)
from playwright_pdf.decorators.cover import inject_cover_page  # type: ignore
from playwright_pdf.decorators.toc import inject_toc  # type: ignore
from playwright_pdf.page_measurements import measure_page_dimensions  # type: ignore
from playwright_pdf.dom_analyzer import analyze_layout  # type: ignore
from playwright_pdf.layout_transformer import (  # type: ignore
    compute_scaling,
    LayoutPolicy,
    apply_scaling,
)
from playwright_pdf.pdf_renderer import build_header_footer  # type: ignore


@dataclass
class InvariantConfig:
    """Toggle specific invariants on/off for a document."""

    height_fit: bool = True
    group_parent_child_diagrams: bool = True


@dataclass
class LayoutDocConfig:
    """Configuration for a single document layout test."""

    name: str
    md: str
    profile: str
    title: str
    invariants: InvariantConfig
    generate_cover: bool = True
    generate_toc: bool = True


def _load_docs_config() -> List[LayoutDocConfig]:
    """
    Load document layout test configuration from YAML.

    This allows you to add new documents by editing layout_docs.yaml rather
    than writing new Python tests.
    """
    config_path = Path(__file__).parent / "layout_docs.yaml"
    if not config_path.exists():
        # Default fallback: return empty list if no config file exists
        # Users should create layout_docs.yaml with their document paths
        return []

    raw = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    docs_raw: List[Dict[str, Any]] = raw.get("documents", [])
    docs: List[LayoutDocConfig] = []

    for entry in docs_raw:
        inv_raw = entry.get("invariants", {}) or {}
        invariants = InvariantConfig(
            height_fit=bool(inv_raw.get("height_fit", True)),
            group_parent_child_diagrams=bool(
                inv_raw.get("group_parent_child_diagrams", True)
            ),
        )
        docs.append(
            LayoutDocConfig(
                name=str(entry["name"]),
                md=str(entry["md"]),
                profile=str(entry["profile"]),
                title=str(entry.get("title", entry["name"])),
                invariants=invariants,
                generate_cover=bool(entry.get("generate_cover", True)),
                generate_toc=bool(entry.get("generate_toc", True)),
            )
        )

    return docs


async def _check_layout_invariants(
    html_file: Path, profile, doc_cfg: LayoutDocConfig
) -> bool:
    """
    Open the HTML in Playwright and run automatic layout invariants for a document.

    Invariants (toggled via doc_cfg.invariants):
    - Height-fit invariant: scaled blocks must fit within their computed target height.
    - Grouping invariant: parent h2 + child h3 + diagram must be in a single
      .heading-diagram-block with the parent grouped.
    """
    print(f"[INFO] Running automated layout invariants for document: {doc_cfg.name}")

    async with open_page(html_file, verbose=False) as (_, page):
        # Ensure base resources are ready
        await page.wait_for_load_state("networkidle")
        await page.evaluate("document.fonts.ready")

        # Inject fonts and CSS
        await inject_fonts(page, verbose=False)
        if profile and profile.css:
            await inject_custom_css(page, profile.css, verbose=False)
        await inject_pagination_css(page, verbose=False)

        # Use a PdfGenerationConfig stub to share cover/TOC/header/footer behavior.
        config = PdfGenerationConfig(
            html_file=html_file,
            pdf_file=html_file.with_suffix(".dummy.pdf"),
            title=doc_cfg.title,
            generate_cover=doc_cfg.generate_cover,
            generate_toc=doc_cfg.generate_toc,
            logo_path=Path(profile.logo) if profile and profile.logo else None,
            css_file=Path(profile.css) if profile and profile.css else None,
            verbose=False,
        )

        # Cover + TOC injection (matching pipeline behavior)
        await inject_cover_page(page, config.cover, verbose=False)
        await inject_toc(page, verbose=False)
        await page.wait_for_timeout(500)

        # Measure page geometry and analyze layout
        header_html, footer_html = build_header_footer(
            title=config.title,
            organization=config.organization,
            author=config.author,
            date=config.date,
        )
        margin_config = {
            "top": "0.75in",
            "right": "0.75in",
            "bottom": "1in",
            "left": "0.75in",
        }
        page_measurements = await measure_page_dimensions(
            page,
            header_html,
            footer_html,
            margin_config,
            page_format=config.page_format,
            verbose=False,
        )

        analysis = await analyze_layout(
            page, page_measurements=page_measurements, verbose=False
        )
        policy = LayoutPolicy()
        decisions = compute_scaling(analysis, policy)

        height_violations: List[str] = []
        if doc_cfg.invariants.height_fit:
            # Height-fit invariant: for each diagram block, the computed final height
            # must not exceed the target height by more than a small tolerance.
            for block in analysis.diagram_blocks:
                breakdown = block.measurement_breakdown or {}
                final_total = breakdown.get("finalTotalHeight")
                target = breakdown.get("targetHeight")
                if final_total is None or target is None:
                    continue
                if final_total > target * 1.02:  # allow small numerical slack
                    height_violations.append(
                        f"- Heading '{block.heading_text}': finalTotalHeight={final_total:.2f} > targetHeight={target:.2f}"
                    )

        # Apply scaling so that grouping invariants can be checked in the DOM.
        if decisions:
            await apply_scaling(page, decisions, verbose=False)
            await page.wait_for_timeout(300)

        grouping_issues: List[str] = []
        if doc_cfg.invariants.group_parent_child_diagrams:
            grouping_issues = await page.evaluate(
                """
                () => {
                    const issues = [];
                    const h3s = document.querySelectorAll('h3');

                    h3s.forEach(h3 => {
                        // Find diagram associated with this h3.
                        let next = h3.nextElementSibling;
                        let foundDiagram = false;
                        for (let i = 0; i < 10 && next && !foundDiagram; i++) {
                            const svg = next.querySelector('svg');
                            const img = next.querySelector('img[src$=".svg"]');
                            if (svg || img) {
                                foundDiagram = true;
                                break;
                            }
                            if (next.tagName && /^H[1-6]$/.test(next.tagName)) {
                                break;
                            }
                            next = next.nextElementSibling;
                        }
                        if (!foundDiagram) return;

                        // Find immediate previous heading (if any).
                        let prev = h3.previousElementSibling;
                        while (prev && !(prev.tagName && /^H[1-6]$/.test(prev.tagName))) {
                            prev = prev.previousElementSibling;
                        }
                        if (!prev || prev.tagName !== 'H2') return;

                        // We now have an H2 -> H3 -> diagram pattern.
                        const block = h3.closest('.heading-diagram-block');
                        if (block) {
                            const containsParent = block.contains(prev);
                            const groupedFlag = block.getAttribute('data-parent-heading-group') === 'true';
                            if (!containsParent || !groupedFlag) {
                                issues.push(`Parent H2 not properly grouped with H3 '${h3.textContent.trim()}'`);
                            }
                        }
                    });

                    return issues;
                }
                """
            )

        if height_violations:
            print("[FAIL] Height-fit invariant violations detected:")
            for msg in height_violations:
                print("   ", msg)

        if grouping_issues:
            print("[FAIL] Heading/diagram grouping issues detected:")
            for msg in grouping_issues:
                print("   ", msg)

        return not height_violations and not grouping_issues


async def _run_single_doc_test(doc_cfg: LayoutDocConfig) -> bool:
    """Run layout invariants + PDF generation for a single document config."""
    # parents: [tests, pdf, tools, <repo_root>, C:/]
    repo_root = Path(__file__).resolve().parents[3]
    md_file = repo_root / doc_cfg.md

    if not md_file.exists():
        print(f"[FAIL] Markdown file not found for '{doc_cfg.name}': {md_file}")
        return False

    test_dir = Path(__file__).parent / "test_outputs"
    test_dir.mkdir(parents=True, exist_ok=True)

    # Use a stable naming pattern but keep document-specific names in config.
    safe_name = doc_cfg.name.replace(" ", "_")
    html_file = test_dir / f"{safe_name}.html"
    pdf_file = test_dir / f"{safe_name}.playwright.pdf"

    # Resolve profile for theme config and CSS.
    profile = get_profile(doc_cfg.profile)
    theme_config = profile.theme_config if profile and profile.theme_config else None

    # Step 1: Convert Markdown → HTML (with diagrams pre-rendered).
    markdown_to_html(
        str(md_file),
        str(html_file),
        cache_dir=str(test_dir / "diagram_cache"),
        use_cache=True,
        theme_config=theme_config,
        highlight_style="pygments",
        crossref_config=None,
        glossary_file=None,
        css_file=None,
    )

    # Extract metadata from markdown frontmatter
    import sys
    sys.path.insert(0, str(repo_root))
    from tools.pdf.convert_final import extract_metadata
    md_content = md_file.read_text(encoding='utf-8')
    metadata, _ = extract_metadata(md_content)
    
    # Step 2a: Run automated invariants against the HTML layout.
    invariants_ok = await _check_layout_invariants(html_file, profile, doc_cfg)

    # Step 2b: Run the Playwright pipeline to generate a PDF.
    config = PdfGenerationConfig(
        html_file=html_file,
        pdf_file=pdf_file,
        title=metadata.get('title', doc_cfg.title),
        author=metadata.get('author'),
        organization=metadata.get('organization'),
        date=metadata.get('date'),
        type=metadata.get('type'),
        classification=metadata.get('classification'),
        version=metadata.get('version'),
        generate_cover=doc_cfg.generate_cover,
        generate_toc=doc_cfg.generate_toc,
        logo_path=Path(profile.logo) if profile and profile.logo else None,
        css_file=Path(profile.css) if profile and profile.css else None,
        verbose=True,
    )

    success = await generate_pdf(config)

    if invariants_ok and success and pdf_file.exists():
        size_kb = pdf_file.stat().st_size / 1024
        print(f"[OK] PDF generated for '{doc_cfg.name}': {pdf_file} ({size_kb:.1f} KB)")
        return True

    if not invariants_ok:
        print(f"[FAIL] Layout invariants failed for document '{doc_cfg.name}'")
    else:
        print(f"[FAIL] Failed to generate PDF via Playwright pipeline for '{doc_cfg.name}'")
    return False


async def run_project_docs_visual_test() -> bool:
    """
    Backwards-compatible entrypoint used by run_all_tests.py.

    Internally, this now runs all layout-doc tests defined in layout_docs.yaml,
    so adding new documents becomes a config-only change.
    """
    docs = _load_docs_config()
    if not docs:
        print("[WARN] No documents configured for layout testing")
        return True

    results = []
    for doc in docs:
        print(f"\n=== Running layout test for document: {doc.name} ===")
        results.append(await _run_single_doc_test(doc))

    passed = sum(1 for r in results if r)
    total = len(results)
    print(f"\n[INFO] Layout doc tests: {passed}/{total} passed")
    return passed == total


if __name__ == "__main__":
    result = asyncio.run(run_project_docs_visual_test())
    sys.exit(0 if result else 1)


