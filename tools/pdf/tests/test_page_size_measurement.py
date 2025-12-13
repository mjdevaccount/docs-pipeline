#!/usr/bin/env python3
"""
Page Size Measurement Test
=========================
Validates that page dimensions and available height calculations are correct.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright_pdf.dom_analyzer import analyze_layout
from playwright_pdf.browser import open_page
from playwright_pdf.styles import inject_pagination_css
from playwright_pdf.decorators.cover import inject_cover_page
from playwright_pdf.decorators.toc import inject_toc
from playwright_pdf.config import CoverConfig

# Test HTML with a large diagram similar to "Failure Detection and Recovery"
TEST_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Page Size Test</title>
    <style>
        body { font-family: Arial; padding: 20px; max-width: 900px; margin: 0 auto; }
        h1 { font-size: 24pt; margin: 20px 0; }
        h2 { font-size: 20pt; margin: 15px 0; }
        p { margin: 10px 0; line-height: 1.6; }
        figure { margin: 20px 0; }
        svg { border: 1px solid #ccc; display: block; }
    </style>
</head>
<body>
    <h1 id="intro">Introduction</h1>
    <p>Some introductory content.</p>
    
    <h2 id="failure-detection">Failure Detection and Recovery</h2>
    <p>This is a large diagram that should be measured correctly.</p>
    <figure>
        <svg width="1200" height="2000" xmlns="http://www.w3.org/2000/svg">
            <rect width="1200" height="2000" fill="#f5f5f5" stroke="#333" stroke-width="2"/>
            <text x="600" y="1000" text-anchor="middle" font-size="32" fill="#333">
                Large Diagram: 1200x2000px
            </text>
            <text x="600" y="1050" text-anchor="middle" font-size="24" fill="#666">
                Similar to Failure Detection and Recovery
            </text>
            <!-- Simulate a complex flowchart -->
            <rect x="100" y="200" width="200" height="100" fill="#fff3e0" stroke="#f57c00"/>
            <rect x="400" y="200" width="200" height="100" fill="#fff3e0" stroke="#f57c00"/>
            <rect x="700" y="200" width="200" height="100" fill="#fff3e0" stroke="#f57c00"/>
            <rect x="100" y="400" width="200" height="100" fill="#e3f2fd" stroke="#1976d2"/>
            <rect x="400" y="400" width="200" height="100" fill="#e3f2fd" stroke="#1976d2"/>
            <rect x="700" y="400" width="200" height="100" fill="#e3f2fd" stroke="#1976d2"/>
            <rect x="100" y="600" width="200" height="100" fill="#e8f5e9" stroke="#388e3c"/>
            <rect x="400" y="600" width="200" height="100" fill="#e8f5e9" stroke="#388e3c"/>
            <rect x="700" y="600" width="200" height="100" fill="#e8f5e9" stroke="#388e3c"/>
            <rect x="100" y="800" width="200" height="100" fill="#fce4ec" stroke="#c2185b"/>
            <rect x="400" y="800" width="200" height="100" fill="#fce4ec" stroke="#c2185b"/>
            <rect x="700" y="800" width="200" height="100" fill="#fce4ec" stroke="#c2185b"/>
            <rect x="100" y="1000" width="200" height="100" fill="#fff9c4" stroke="#f9a825"/>
            <rect x="400" y="1000" width="200" height="100" fill="#fff9c4" stroke="#f9a825"/>
            <rect x="700" y="1000" width="200" height="100" fill="#fff9c4" stroke="#f9a825"/>
            <rect x="100" y="1200" width="200" height="100" fill="#e1bee7" stroke="#7b1fa2"/>
            <rect x="400" y="1200" width="200" height="100" fill="#e1bee7" stroke="#7b1fa2"/>
            <rect x="700" y="1200" width="200" height="100" fill="#e1bee7" stroke="#7b1fa2"/>
            <rect x="100" y="1400" width="200" height="100" fill="#b2dfdb" stroke="#00796b"/>
            <rect x="400" y="1400" width="200" height="100" fill="#b2dfdb" stroke="#00796b"/>
            <rect x="700" y="1400" width="200" height="100" fill="#b2dfdb" stroke="#00796b"/>
            <rect x="100" y="1600" width="200" height="100" fill="#ffccbc" stroke="#e64a19"/>
            <rect x="400" y="1600" width="200" height="100" fill="#ffccbc" stroke="#e64a19"/>
            <rect x="700" y="1600" width="200" height="100" fill="#ffccbc" stroke="#e64a19"/>
            <rect x="100" y="1800" width="200" height="100" fill="#c5cae9" stroke="#303f9f"/>
            <rect x="400" y="1800" width="200" height="100" fill="#c5cae9" stroke="#303f9f"/>
            <rect x="700" y="1800" width="200" height="100" fill="#c5cae9" stroke="#303f9f"/>
        </svg>
    </figure>
</body>
</html>"""


async def test_page_dimensions():
    """Test that page dimensions are measured correctly"""
    print("\n" + "="*70)
    print("PAGE DIMENSION MEASUREMENT TEST")
    print("="*70)
    
    test_file = Path(__file__).parent / "page_size_test.html"
    test_file.write_text(TEST_HTML, encoding='utf-8')
    
    try:
        async with open_page(test_file, verbose=False) as (browser, page):
            await page.wait_for_load_state('networkidle')
            await inject_pagination_css(page, verbose=False)
            
            # Inject cover and TOC to match real scenario
            cover_config = CoverConfig(
                title="Page Size Test",
                author="Test Author",
                organization="Test Org",
                date="2025"
            )
            await inject_cover_page(page, cover_config, verbose=False)
            await inject_toc(page, verbose=False)
            await page.wait_for_timeout(500)
            
            # Get actual page dimensions from browser
            page_dimensions = await page.evaluate("""
                () => {
                    // A4 page dimensions at 96dpi
                    const a4Width = 8.27 * 96;  // 794px
                    const a4Height = 11.69 * 96; // 1123px
                    
                    // Margins from CSS
                    const topMargin = 0.75 * 96;   // 72px
                    const bottomMargin = 1.0 * 96;  // 96px
                    const sideMargin = 0.75 * 96;   // 72px
                    
                    // Available content area
                    const contentWidth = a4Width - (sideMargin * 2);
                    const contentHeight = a4Height - topMargin - bottomMargin;
                    
                    // Get actual computed values
                    const body = document.body;
                    const bodyRect = body.getBoundingClientRect();
                    const bodyStyle = window.getComputedStyle(body);
                    
                    return {
                        a4Width: a4Width,
                        a4Height: a4Height,
                        topMargin: topMargin,
                        bottomMargin: bottomMargin,
                        sideMargin: sideMargin,
                        contentWidth: contentWidth,
                        contentHeight: contentHeight,
                        bodyWidth: bodyRect.width,
                        bodyHeight: bodyRect.height,
                        bodyMarginTop: parseFloat(bodyStyle.marginTop) || 0,
                        bodyMarginBottom: parseFloat(bodyStyle.marginBottom) || 0,
                        windowWidth: window.innerWidth,
                        windowHeight: window.innerHeight,
                        scrollHeight: document.documentElement.scrollHeight
                    };
                }
            """)
            
            print("\n[Page Dimensions from Browser]")
            print(f"  A4 Size (96dpi): {page_dimensions['a4Width']:.0f}px × {page_dimensions['a4Height']:.0f}px")
            print(f"  Margins: Top={page_dimensions['topMargin']:.0f}px, Bottom={page_dimensions['bottomMargin']:.0f}px, Side={page_dimensions['sideMargin']:.0f}px")
            print(f"  Content Area: {page_dimensions['contentWidth']:.0f}px × {page_dimensions['contentHeight']:.0f}px")
            print(f"  Body Size: {page_dimensions['bodyWidth']:.0f}px × {page_dimensions['bodyHeight']:.0f}px")
            print(f"  Window Size: {page_dimensions['windowWidth']:.0f}px × {page_dimensions['windowHeight']:.0f}px")
            print(f"  Document Scroll Height: {page_dimensions['scrollHeight']:.0f}px")
            
            # Now run analysis
            analysis = await analyze_layout(page, verbose=True)
            
            if analysis.diagram_blocks:
                block = analysis.diagram_blocks[0]
                breakdown = block.measurement_breakdown or {}
                
                print("\n[Analysis Results]")
                print(f"  Page Height (from analysis): {analysis.page_height:.0f}px")
                print(f"  Available Height (from analysis): {analysis.available_height:.0f}px")
                print(f"  Diagram Block Available Height: {block.available_height:.0f}px")
                print(f"  Content Above Heading: {breakdown.get('contentAboveHeading', 0):.0f}px")
                print(f"  Diagram Height: {block.diagram_height:.0f}px")
                print(f"  Total Content Height: {block.total_content_height:.0f}px")
                print(f"  Overflow Ratio: {block.overflow_ratio:.2f}x")
                
                # Validate measurements
                print("\n[Validation]")
                
                # Check if page height matches expected A4 height
                expected_page_height = 1122  # 11.69in at 96dpi (A4 height)
                if abs(analysis.page_height - expected_page_height) < 10:
                    print(f"  ✓ Page height matches expected ({expected_page_height}px)")
                else:
                    print(f"  ✗ Page height mismatch: {analysis.page_height:.0f}px vs expected {expected_page_height}px")
                
                # Check if available height is reasonable
                expected_available = expected_page_height - 72 - 96 - 30 - 30  # page - margins - header - footer
                if abs(block.available_height - expected_available) < 50:
                    print(f"  ✓ Available height reasonable ({block.available_height:.0f}px)")
                else:
                    print(f"  [WARN] Available height differs from expected: {block.available_height:.0f}px vs ~{expected_available}px")
                
                # Check content above measurement
                if breakdown.get('contentAboveHeading', 0) >= 0:
                    print(f"  ✓ Content above measured: {breakdown.get('contentAboveHeading', 0):.0f}px")
                else:
                    print(f"  ✗ Content above invalid: {breakdown.get('contentAboveHeading', 0):.0f}px")
                
                return True
            else:
                print("\n[ERROR] No diagram blocks found in analysis")
                return False
                
    finally:
        if test_file.exists():
            test_file.unlink()


async def test_failure_detection_scenario():
    """Test specifically the Failure Detection and Recovery scenario"""
    print("\n" + "="*70)
    print("FAILURE DETECTION SCENARIO TEST")
    print("="*70)
    
    test_file = Path(__file__).parent / "failure_detection_test.html"
    test_file.write_text(TEST_HTML, encoding='utf-8')
    
    try:
        async with open_page(test_file, verbose=False) as (browser, page):
            await page.wait_for_load_state('networkidle')
            await inject_pagination_css(page, verbose=False)
            
            cover_config = CoverConfig(
                title="Failure Detection Test",
                author="Test Author",
                organization="Test Org",
                date="2025"
            )
            await inject_cover_page(page, cover_config, verbose=False)
            await inject_toc(page, verbose=False)
            await page.wait_for_timeout(500)
            
            # Get detailed measurements
            detailed_measurements = await page.evaluate("""
                () => {
                    const heading = document.getElementById('failure-detection');
                    if (!heading) return null;
                    
                    const headingRect = heading.getBoundingClientRect();
                    const bodyRect = document.body.getBoundingClientRect();
                    
                    // Find last page break before heading
                    let lastPageBreak = null;
                    let elem = document.body.firstElementChild;
                    while (elem && elem !== heading) {
                        const style = window.getComputedStyle(elem);
                        const hasPageBreak = (
                            (elem.classList && (
                                elem.classList.contains('cover-page-wrapper') ||
                                elem.classList.contains('toc-wrapper') ||
                                elem.classList.contains('page-break')
                            )) ||
                            style.pageBreakAfter === 'always' ||
                            style.breakAfter === 'page'
                        );
                        if (hasPageBreak) {
                            lastPageBreak = elem;
                        }
                        elem = elem.nextElementSibling;
                    }
                    
                    // Measure content above
                    let contentAbove = 0;
                    let measureStart = lastPageBreak ? lastPageBreak.nextElementSibling : document.body.firstElementChild;
                    while (measureStart && measureStart !== heading) {
                        const style = window.getComputedStyle(measureStart);
                        const isPageBreak = (
                            (measureStart.classList && (
                                measureStart.classList.contains('cover-page-wrapper') ||
                                measureStart.classList.contains('toc-wrapper') ||
                                measureStart.classList.contains('page-break')
                            )) ||
                            style.pageBreakAfter === 'always' ||
                            style.breakAfter === 'page'
                        );
                        if (!isPageBreak) {
                            const height = measureStart.offsetHeight;
                            const marginTop = parseFloat(style.marginTop) || 0;
                            const marginBottom = parseFloat(style.marginBottom) || 0;
                            const paddingTop = parseFloat(style.paddingTop) || 0;
                            const paddingBottom = parseFloat(style.paddingBottom) || 0;
                            contentAbove += height + marginTop + marginBottom + paddingTop + paddingBottom;
                        }
                        measureStart = measureStart.nextElementSibling;
                    }
                    
                    // Get diagram
                    const diagram = document.querySelector('svg');
                    const diagramRect = diagram ? diagram.getBoundingClientRect() : null;
                    
                    return {
                        headingTop: headingRect.top + window.pageYOffset,
                        bodyTop: bodyRect.top + window.pageYOffset,
                        contentAbove: contentAbove,
                        lastPageBreak: lastPageBreak ? lastPageBreak.className : null,
                        diagramHeight: diagramRect ? diagramRect.height : 0,
                        diagramWidth: diagramRect ? diagramRect.width : 0
                    };
                }
            """)
            
            if detailed_measurements:
                print("\n[Detailed Measurements]")
                print(f"  Heading position (from top): {detailed_measurements['headingTop']:.0f}px")
                print(f"  Body top position: {detailed_measurements['bodyTop']:.0f}px")
                print(f"  Content above heading: {detailed_measurements['contentAbove']:.0f}px")
                print(f"  Last page break element: {detailed_measurements['lastPageBreak'] or 'None'}")
                print(f"  Diagram size: {detailed_measurements['diagramWidth']:.0f}px × {detailed_measurements['diagramHeight']:.0f}px")
            
            # Run analysis
            analysis = await analyze_layout(page, verbose=False)
            
            if analysis.diagram_blocks:
                block = analysis.diagram_blocks[0]
                breakdown = block.measurement_breakdown or {}
                
                print("\n[Analysis vs Manual Measurement]")
                print(f"  Analysis - Content above: {breakdown.get('contentAboveHeading', 0):.0f}px")
                print(f"  Manual - Content above: {detailed_measurements['contentAbove']:.0f}px")
                
                diff = abs(breakdown.get('contentAboveHeading', 0) - detailed_measurements['contentAbove'])
                if diff < 50:
                    print(f"  ✓ Measurements match (diff: {diff:.0f}px)")
                else:
                    print(f"  ✗ Measurements differ significantly (diff: {diff:.0f}px)")
                
                print(f"\n  Analysis - Available height: {block.available_height:.0f}px")
                print(f"  Analysis - Diagram height: {block.diagram_height:.0f}px")
                print(f"  Analysis - Overflow ratio: {block.overflow_ratio:.2f}x")
                
                # Calculate what scale factor should be
                effective_page_height = 1122 - 72 - 96 - 30 - 30  # ~894px
                pages_above = detailed_measurements['contentAbove'] / effective_page_height
                space_on_page = detailed_measurements['contentAbove'] % effective_page_height
                
                print(f"\n[Expected Calculation]")
                print(f"  Effective page height: {effective_page_height:.0f}px")
                print(f"  Pages above: {pages_above:.2f}")
                print(f"  Space used on current page: {space_on_page:.0f}px")
                
                if pages_above >= 2:
                    expected_available = effective_page_height - 50
                elif pages_above >= 1:
                    if space_on_page < 200:
                        expected_available = effective_page_height - Math.max(50, space_on_page)
                    else:
                        expected_available = Math.max(500, effective_page_height - Math.min(space_on_page, 200))
                else:
                    expected_available = effective_page_height - space_on_page
                
                print(f"  Expected available height: ~{expected_available:.0f}px")
                print(f"  Actual available height: {block.available_height:.0f}px")
                
                diff_available = abs(block.available_height - expected_available)
                if diff_available < 100:
                    print(f"  ✓ Available height calculation reasonable (diff: {diff_available:.0f}px)")
                else:
                    print(f"  ✗ Available height calculation differs (diff: {diff_available:.0f}px)")
                
                return True
            else:
                print("\n[ERROR] No diagram blocks found")
                return False
                
    finally:
        if test_file.exists():
            test_file.unlink()


async def main():
    """Run all page size tests"""
    print("\n" + "="*70)
    print("PAGE SIZE MEASUREMENT TEST SUITE")
    print("="*70)
    
    results = []
    
    try:
        results.append(await test_page_dimensions())
        results.append(await test_failure_detection_scenario())
    except Exception as e:
        print(f"\n[ERROR] Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    passed = sum(results)
    total = len(results)
    
    for i, result in enumerate(results, 1):
        status = "[PASS]" if result else "[FAIL]"
        print(f"  Test {i}: {status}")
    
    print(f"\n  Total: {passed}/{total} tests passed")
    
    return passed == total


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

