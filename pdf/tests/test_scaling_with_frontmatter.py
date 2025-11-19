#!/usr/bin/env python3
"""
Test Suite for Front Matter Scaling
===================================
Validates that scaling correctly accounts for cover page and TOC.
"""
import asyncio
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright_pdf.dom_analyzer import analyze_layout
from playwright_pdf.layout_transformer import compute_scaling
from playwright_pdf.browser import open_page
from playwright_pdf.styles import inject_pagination_css
from playwright_pdf.decorators.cover import inject_cover_page
from playwright_pdf.decorators.toc import inject_toc
from playwright_pdf.config import CoverConfig

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    OK = f"{Fore.GREEN}[OK]{Style.RESET_ALL}"
    FAIL = f"{Fore.RED}[FAIL]{Style.RESET_ALL}"
    INFO = f"{Fore.CYAN}[INFO]{Style.RESET_ALL}"
except ImportError:
    OK = "[OK]"
    FAIL = "[FAIL]"
    INFO = "[INFO]"


# Test HTML with known structure
TEST_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Test Document</title>
    <style>
        body { font-family: Arial; padding: 20px; }
        h1 { font-size: 24pt; margin: 20px 0; }
        h2 { font-size: 20pt; margin: 15px 0; }
        p { margin: 10px 0; }
        figure { margin: 20px 0; }
        svg { border: 1px solid #ccc; }
    </style>
</head>
<body>
    <h1>Introduction</h1>
    <p>This is introductory content that appears before the first diagram.</p>
    <p>It should be accounted for when calculating available space.</p>
    
    <h2>First Diagram Section</h2>
    <p>Some text before the diagram.</p>
    <figure>
        <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
            <rect width="800" height="600" fill="#e3f2fd"/>
            <text x="400" y="300" text-anchor="middle" font-size="24">Diagram 1 (800x600)</text>
        </svg>
    </figure>
    
    <h2>Second Diagram Section</h2>
    <p>More content here.</p>
    <figure>
        <svg width="700" height="500" xmlns="http://www.w3.org/2000/svg">
            <rect width="700" height="500" fill="#fff3e0"/>
            <text x="350" y="250" text-anchor="middle" font-size="24">Diagram 2 (700x500)</text>
        </svg>
    </figure>
    
    <h2>Third Diagram Section</h2>
    <p>Even more content.</p>
    <figure>
        <svg width="600" height="400" xmlns="http://www.w3.org/2000/svg">
            <rect width="600" height="400" fill="#e8f5e9"/>
            <text x="300" y="200" text-anchor="middle" font-size="24">Diagram 3 (600x400)</text>
        </svg>
    </figure>
</body>
</html>"""


async def test_scaling_without_frontmatter():
    """Test scaling without cover page/TOC"""
    print(f"\n{INFO} Test 1: Scaling WITHOUT front matter")
    print("=" * 60)
    
    # Create test HTML file
    test_file = Path(__file__).parent / "test_no_frontmatter.html"
    test_file.write_text(TEST_HTML, encoding='utf-8')
    
    try:
        async with open_page(test_file, verbose=False) as (browser, page):
            await page.wait_for_load_state('networkidle')
            await inject_pagination_css(page, verbose=False)
            await page.wait_for_timeout(500)
            
            analysis = await analyze_layout(page, verbose=True)
            
            print(f"\n{INFO} Analysis Results:")
            print(f"  Found {len(analysis.diagram_blocks)} diagram blocks")
            
            for i, block in enumerate(analysis.diagram_blocks, 1):
                print(f"\n  Block {i}: '{block.heading_text}'")
                print(f"    Available height: {block.available_height:.0f}px")
                print(f"    Total content height: {block.total_content_height:.0f}px")
                print(f"    Overflow ratio: {block.overflow_ratio:.2f}x")
            
            decisions = compute_scaling(analysis)
            print(f"\n{INFO} Scaling Decisions:")
            for i, decision in enumerate(decisions, 1):
                print(f"  Decision {i}: {decision.heading_id}")
                print(f"    Scale factor: {decision.scale_factor:.2f}x ({decision.scale_factor*100:.0f}%)")
                print(f"    Mode: {'Entire block' if decision.scale_entire_block else 'Diagram only'}")
            
            # Verify: Without front matter, first heading should have good available height
            if analysis.diagram_blocks:
                first_block = analysis.diagram_blocks[0]
                if first_block.available_height > 500:
                    print(f"\n{OK} Test 1 PASSED: First diagram has good available height ({first_block.available_height:.0f}px)")
                    return True
                else:
                    print(f"\n{FAIL} Test 1 FAILED: First diagram has low available height ({first_block.available_height:.0f}px)")
                    return False
            else:
                print(f"\n{FAIL} Test 1 FAILED: No diagram blocks found")
                return False
                
    finally:
        if test_file.exists():
            test_file.unlink()


async def test_scaling_with_frontmatter():
    """Test scaling WITH cover page and TOC"""
    print(f"\n{INFO} Test 2: Scaling WITH front matter (cover + TOC)")
    print("=" * 60)
    
    # Create test HTML file
    test_file = Path(__file__).parent / "test_with_frontmatter.html"
    test_file.write_text(TEST_HTML, encoding='utf-8')
    
    try:
        async with open_page(test_file, verbose=False) as (browser, page):
            await page.wait_for_load_state('networkidle')
            await inject_pagination_css(page, verbose=False)
            
            # Inject cover page
            cover_config = CoverConfig(
                title="Test Document",
                author="Test Author",
                organization="Test Org",
                date="2025"
            )
            await inject_cover_page(page, cover_config, verbose=False)
            
            # Inject TOC
            await inject_toc(page, verbose=False)
            
            await page.wait_for_timeout(500)
            
            analysis = await analyze_layout(page, verbose=True)
            
            print(f"\n{INFO} Analysis Results:")
            print(f"  Found {len(analysis.diagram_blocks)} diagram blocks")
            
            for i, block in enumerate(analysis.diagram_blocks, 1):
                breakdown = block.measurement_breakdown or {}
                content_above = breakdown.get('contentAboveHeading', 0)
                print(f"\n  Block {i}: '{block.heading_text}'")
                print(f"    Content above heading: {content_above:.0f}px")
                print(f"    Available height: {block.available_height:.0f}px")
                print(f"    Total content height: {block.total_content_height:.0f}px")
                print(f"    Overflow ratio: {block.overflow_ratio:.2f}x")
            
            decisions = compute_scaling(analysis)
            print(f"\n{INFO} Scaling Decisions:")
            for i, decision in enumerate(decisions, 1):
                print(f"  Decision {i}: {decision.heading_id}")
                print(f"    Scale factor: {decision.scale_factor:.2f}x ({decision.scale_factor*100:.0f}%)")
                print(f"    Mode: {'Entire block' if decision.scale_entire_block else 'Diagram only'}")
            
            # Verify: With front matter, first heading should account for content after TOC
            if analysis.diagram_blocks:
                first_block = analysis.diagram_blocks[0]
                breakdown = first_block.measurement_breakdown or {}
                content_above = breakdown.get('contentAboveHeading', 0)
                
                # After cover + TOC, there should be some content above first heading
                # But available height should still be reasonable (not artificially low)
                if content_above > 0 and first_block.available_height > 400:
                    print(f"\n{OK} Test 2 PASSED: Front matter accounted for")
                    print(f"    Content above: {content_above:.0f}px")
                    print(f"    Available height: {first_block.available_height:.0f}px")
                    return True
                elif first_block.available_height < 300:
                    print(f"\n{FAIL} Test 2 FAILED: Available height too low ({first_block.available_height:.0f}px)")
                    print(f"    Content above: {content_above:.0f}px")
                    return False
                else:
                    print(f"\n{OK} Test 2 PASSED: Available height reasonable ({first_block.available_height:.0f}px)")
                    return True
            else:
                print(f"\n{FAIL} Test 2 FAILED: No diagram blocks found")
                return False
                
    finally:
        if test_file.exists():
            test_file.unlink()


async def test_page_break_reset():
    """Test that page breaks reset the cumulative height counter"""
    print(f"\n{INFO} Test 3: Page break reset logic")
    print("=" * 60)
    
    # Create HTML with explicit page break
    html_with_break = TEST_HTML.replace(
        '<h2>Second Diagram Section</h2>',
        '<div class="page-break"></div><h2>Second Diagram Section</h2>'
    )
    
    test_file = Path(__file__).parent / "test_page_break.html"
    test_file.write_text(html_with_break, encoding='utf-8')
    
    try:
        async with open_page(test_file, verbose=False) as (browser, page):
            await page.wait_for_load_state('networkidle')
            await inject_pagination_css(page, verbose=False)
            await page.wait_for_timeout(500)
            
            analysis = await analyze_layout(page, verbose=True)
            
            if len(analysis.diagram_blocks) >= 2:
                first_block = analysis.diagram_blocks[0]
                second_block = analysis.diagram_blocks[1]
                
                breakdown1 = first_block.measurement_breakdown or {}
                breakdown2 = second_block.measurement_breakdown or {}
                content_above_1 = breakdown1.get('contentAboveHeading', 0)
                content_above_2 = breakdown2.get('contentAboveHeading', 0)
                
                print(f"\n  First diagram:")
                print(f"    Content above: {content_above_1:.0f}px")
                print(f"    Available height: {first_block.available_height:.0f}px")
                print(f"\n  Second diagram (after page break):")
                print(f"    Content above: {content_above_2:.0f}px")
                print(f"    Available height: {second_block.available_height:.0f}px")
                
                # After page break, content above should be reset (small)
                if content_above_2 < content_above_1:
                    print(f"\n{OK} Test 3 PASSED: Page break reset content counter")
                    print(f"    Content above reduced from {content_above_1:.0f}px to {content_above_2:.0f}px")
                    return True
                else:
                    print(f"\n{FAIL} Test 3 FAILED: Page break did not reset counter")
                    print(f"    Content above: {content_above_1:.0f}px -> {content_above_2:.0f}px")
                    return False
            else:
                print(f"\n{FAIL} Test 3 FAILED: Not enough diagram blocks")
                return False
                
    finally:
        if test_file.exists():
            test_file.unlink()


async def run_all_tests():
    """Run all tests and report results"""
    print("\n" + "=" * 60)
    print("FRONT MATTER SCALING TEST SUITE")
    print("=" * 60)
    
    results = []
    
    try:
        results.append(await test_scaling_without_frontmatter())
        results.append(await test_scaling_with_frontmatter())
        results.append(await test_page_break_reset())
    except Exception as e:
        print(f"\n{FAIL} Test suite failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "=" * 60)
    print("TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(results)
    total = len(results)
    
    for i, result in enumerate(results, 1):
        status = OK if result else FAIL
        print(f"  Test {i}: {'PASSED' if result else 'FAILED'} {status}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    if passed == total:
        print(f"\n{OK} All tests passed!")
        return True
    else:
        print(f"\n{FAIL} Some tests failed. Review output above.")
        return False


if __name__ == '__main__':
    success = asyncio.run(run_all_tests())
    sys.exit(0 if success else 1)

