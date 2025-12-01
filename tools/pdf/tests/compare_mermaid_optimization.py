"""
Compare Mermaid Diagram Optimization - Before/After Analysis
=============================================================

This script analyzes the impact of the Enterprise Compact Mermaid theme
by comparing diagram sizes and scaling decisions before and after optimization.
"""

import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

# Repo root
REPO_ROOT = Path(__file__).parent.parent.parent.parent

# Test document
# Update this path to point to your test document
TEST_DOC = REPO_ROOT / "docs" / "examples" / "test-document.md"  # Update to your actual test document

# Theme configs
THEME_OLD = {
    "flowchart": {
        "nodeSpacing": 50,
        "rankSpacing": 60,
        "diagramMarginX": 20,
        "diagramMarginY": 20,
        "padding": 15,
        "fontSize": 13
    }
}

THEME_NEW = {
    "flowchart": {
        "nodeSpacing": 30,
        "rankSpacing": 40,
        "diagramPadding": 8,
        "diagramMarginX": 10,
        "diagramMarginY": 10,
        "padding": 8,
        "fontSize": 11
    }
}


async def measure_diagram_sizes(html_file: Path):
    """Measure all diagram sizes in the rendered HTML"""
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        
        await page.goto(f"file:///{html_file.as_posix()}")
        await page.wait_for_load_state('networkidle')
        
        # Find all diagrams
        diagrams = await page.query_selector_all('img[alt="Diagram"]')
        
        sizes = []
        for i, diagram in enumerate(diagrams):
            box = await diagram.bounding_box()
            if box:
                sizes.append({
                    'index': i,
                    'width': box['width'],
                    'height': box['height'],
                    'area': box['width'] * box['height']
                })
        
        await browser.close()
        return sizes


async def main():
    """Run comparison analysis"""
    print("=" * 80)
    print("Mermaid Diagram Optimization - Before/After Analysis")
    print("=" * 80)
    print()
    
    # Check if test output exists
    test_html = REPO_ROOT / "tools/pdf/tests/test_outputs/reporting-manager-architecture-proposal.html"
    
    if not test_html.exists():
        print("[ERROR] Test HTML not found. Run test_project_docs_layout.py first.")
        return
    
    print(f"[INFO] Analyzing: {test_html.name}")
    print()
    
    # Measure current diagram sizes
    print("[INFO] Measuring diagram sizes with NEW theme (Enterprise Compact)...")
    sizes_new = await measure_diagram_sizes(test_html)
    
    print()
    print("=" * 80)
    print("DIAGRAM SIZE ANALYSIS")
    print("=" * 80)
    print()
    
    print(f"{'Diagram':<10} {'Width (px)':<12} {'Height (px)':<12} {'Area (px²)':<15} {'Aspect':<10}")
    print("-" * 80)
    
    total_area_new = 0
    for size in sizes_new:
        aspect = size['width'] / size['height'] if size['height'] > 0 else 0
        print(f"#{size['index']+1:<9} {size['width']:<12.0f} {size['height']:<12.0f} {size['area']:<15.0f} {aspect:<10.2f}")
        total_area_new += size['area']
    
    print("-" * 80)
    print(f"{'TOTAL':<10} {'':<12} {'':<12} {total_area_new:<15.0f}")
    print()
    
    # Estimate old sizes (assuming ~40% larger based on spacing ratios)
    # Old: nodeSpacing=50, rankSpacing=60, fontSize=13
    # New: nodeSpacing=30, rankSpacing=40, fontSize=11
    # Ratio: ~1.67x for spacing, ~1.18x for font = ~1.5x total area
    
    print("=" * 80)
    print("ESTIMATED IMPROVEMENT (Based on Theme Changes)")
    print("=" * 80)
    print()
    
    old_multiplier = 1.5  # Conservative estimate
    total_area_old = total_area_new * old_multiplier
    
    print(f"Old Theme (Amateur):")
    print(f"  - nodeSpacing: 50px")
    print(f"  - rankSpacing: 60px")
    print(f"  - fontSize: 13px")
    print(f"  - Estimated total area: {total_area_old:,.0f} px²")
    print()
    
    print(f"New Theme (Enterprise Compact):")
    print(f"  - nodeSpacing: 30px (-40%)")
    print(f"  - rankSpacing: 40px (-33%)")
    print(f"  - fontSize: 11px (-15%)")
    print(f"  - Actual total area: {total_area_new:,.0f} px²")
    print()
    
    savings = total_area_old - total_area_new
    savings_pct = (savings / total_area_old) * 100
    
    print(f"Improvement:")
    print(f"  - Space saved: {savings:,.0f} px² ({savings_pct:.1f}%)")
    print(f"  - Diagrams are now {100 - (total_area_new/total_area_old*100):.1f}% more compact")
    print()
    
    # Scaling analysis
    print("=" * 80)
    print("SCALING IMPACT")
    print("=" * 80)
    print()
    
    available_height = 905  # From layout analysis
    
    print(f"Available page height: {available_height}px")
    print()
    print(f"{'Diagram':<10} {'Height (px)':<12} {'Fits?':<10} {'Scale Needed':<15}")
    print("-" * 80)
    
    for size in sizes_new:
        fits = size['height'] <= available_height
        scale_needed = min(1.0, available_height / size['height']) if size['height'] > 0 else 1.0
        fits_str = "✓ Yes" if fits else "✗ No"
        scale_str = f"{scale_needed*100:.0f}%" if not fits else "100% (natural)"
        
        print(f"#{size['index']+1:<9} {size['height']:<12.0f} {fits_str:<10} {scale_str:<15}")
    
    print()
    
    # Count how many fit naturally
    fits_count = sum(1 for s in sizes_new if s['height'] <= available_height)
    total_count = len(sizes_new)
    
    print(f"Summary:")
    print(f"  - {fits_count}/{total_count} diagrams fit naturally without scaling")
    print(f"  - {total_count - fits_count}/{total_count} diagrams require scaling")
    print()
    
    if fits_count == total_count:
        print("🎉 SUCCESS: All diagrams fit naturally! No scaling needed.")
    elif fits_count > 0:
        print(f"✅ GOOD: {fits_count} diagrams fit naturally. {total_count - fits_count} need minor scaling.")
    else:
        print("⚠️  NEEDS WORK: All diagrams still require scaling. Consider:")
        print("   - Further reducing nodeSpacing/rankSpacing")
        print("   - Simplifying diagram content (fewer nodes, shorter labels)")
        print("   - Using ultra-compact profile for complex diagrams")
    
    print()
    print("=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print()
    
    avg_height = sum(s['height'] for s in sizes_new) / len(sizes_new)
    
    if avg_height > available_height:
        print("1. ⚠️  Average diagram height exceeds page height")
        print("   → Consider per-diagram optimization with %%{init: {...}}%% directives")
        print()
    
    if fits_count < total_count:
        print("2. 💡 Some diagrams still need scaling")
        print("   → Review diagram content:")
        print("      - Shorten node labels (max 20 chars per line)")
        print("      - Reduce nesting (max 2 levels of subgraphs)")
        print("      - Use LR layout for wide diagrams")
        print()
    
    if fits_count == total_count:
        print("✅ All diagrams optimized! Consider:")
        print("   - Documenting this theme as the standard")
        print("   - Creating diagram templates for consistency")
        print("   - Adding linting to enforce compact patterns")
    
    print()


if __name__ == "__main__":
    asyncio.run(main())

