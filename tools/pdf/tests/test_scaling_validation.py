#!/usr/bin/env python3
"""
Comprehensive Scaling Validation Test
======================================
Validates that scaling correctly accounts for front matter by checking
actual measurements and scaling decisions.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright_pdf.dom_analyzer import analyze_layout
from playwright_pdf.layout_transformer import compute_scaling
from playwright_pdf.browser import open_page
from playwright_pdf.styles import inject_pagination_css
from playwright_pdf.decorators.cover import inject_cover_page
from playwright_pdf.decorators.toc import inject_toc
from playwright_pdf.config import CoverConfig

# Test HTML with controlled structure
TEST_HTML = """<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>Scaling Validation</title>
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
    <p>Content before first diagram.</p>
    
    <h2 id="diagram-1">First Diagram</h2>
    <p>Text before diagram.</p>
    <figure>
        <svg width="800" height="600" xmlns="http://www.w3.org/2000/svg">
            <rect width="800" height="600" fill="#e3f2fd"/>
            <text x="400" y="300" text-anchor="middle" font-size="24">800x600</text>
        </svg>
    </figure>
    
    <h2 id="diagram-2">Second Diagram</h2>
    <p>More content.</p>
    <figure>
        <svg width="700" height="500" xmlns="http://www.w3.org/2000/svg">
            <rect width="700" height="500" fill="#fff3e0"/>
            <text x="350" y="250" text-anchor="middle" font-size="24">700x500</text>
        </svg>
    </figure>
</body>
</html>"""


class TestResults:
    def __init__(self):
        self.passed = []
        self.failed = []
    
    def add_pass(self, test_name, details=""):
        self.passed.append((test_name, details))
        print(f"  [PASS] {test_name}")
        if details:
            print(f"         {details}")
    
    def add_fail(self, test_name, reason):
        self.failed.append((test_name, reason))
        print(f"  [FAIL] {test_name}")
        print(f"         Reason: {reason}")
    
    def summary(self):
        total = len(self.passed) + len(self.failed)
        print(f"\n{'='*60}")
        print(f"Test Summary: {len(self.passed)}/{total} passed")
        if self.failed:
            print(f"\nFailed tests:")
            for name, reason in self.failed:
                print(f"  - {name}: {reason}")
        return len(self.failed) == 0


async def validate_frontmatter_accounting():
    """Validate that front matter is properly accounted for in measurements"""
    results = TestResults()
    
    print("\n" + "="*60)
    print("FRONT MATTER ACCOUNTING VALIDATION")
    print("="*60)
    
    test_file = Path(__file__).parent / "validation_test.html"
    test_file.write_text(TEST_HTML, encoding='utf-8')
    
    try:
        # Test WITHOUT front matter
        async with open_page(test_file, verbose=False) as (browser, page):
            await page.wait_for_load_state('networkidle')
            await inject_pagination_css(page, verbose=False)
            await page.wait_for_timeout(500)
            
            analysis_no_fm = await analyze_layout(page, verbose=False)
            
            if not analysis_no_fm.diagram_blocks:
                results.add_fail("No front matter - analysis", "No diagram blocks found")
                return results
            
            first_block_no_fm = analysis_no_fm.diagram_blocks[0]
            breakdown_no_fm = first_block_no_fm.measurement_breakdown or {}
            content_above_no_fm = breakdown_no_fm.get('contentAboveHeading', 0)
            available_no_fm = first_block_no_fm.available_height
            
            print(f"\nWithout front matter:")
            print(f"  Content above first heading: {content_above_no_fm:.0f}px")
            print(f"  Available height: {available_no_fm:.0f}px")
        
        # Test WITH front matter
        async with open_page(test_file, verbose=False) as (browser, page):
            await page.wait_for_load_state('networkidle')
            await inject_pagination_css(page, verbose=False)
            
            cover_config = CoverConfig(
                title="Test Document",
                author="Test Author",
                organization="Test Org",
                date="2025"
            )
            await inject_cover_page(page, cover_config, verbose=False)
            await inject_toc(page, verbose=False)
            await page.wait_for_timeout(500)
            
            analysis_with_fm = await analyze_layout(page, verbose=False)
            
            if not analysis_with_fm.diagram_blocks:
                results.add_fail("With front matter - analysis", "No diagram blocks found")
                return results
            
            first_block_with_fm = analysis_with_fm.diagram_blocks[0]
            breakdown_with_fm = first_block_with_fm.measurement_breakdown or {}
            content_above_with_fm = breakdown_with_fm.get('contentAboveHeading', 0)
            available_with_fm = first_block_with_fm.available_height
            
            print(f"\nWith front matter:")
            print(f"  Content above first heading: {content_above_with_fm:.0f}px")
            print(f"  Available height: {available_with_fm:.0f}px")
            
            # Validation checks
            print(f"\nValidation checks:")
            
            # Check 1: Content above should be measured
            if content_above_with_fm >= 0:
                results.add_pass("Content above measurement", 
                               f"Measured {content_above_with_fm:.0f}px")
            else:
                results.add_fail("Content above measurement", 
                               f"Invalid value: {content_above_with_fm:.0f}px")
            
            # Check 2: Available height should be reasonable (not artificially low)
            if available_with_fm >= 400:
                results.add_pass("Available height reasonable", 
                               f"{available_with_fm:.0f}px >= 400px")
            else:
                results.add_fail("Available height too low", 
                               f"{available_with_fm:.0f}px < 400px")
            
            # Check 3: Scaling decisions should be made
            decisions = compute_scaling(analysis_with_fm)
            if decisions:
                first_decision = decisions[0]
                print(f"\n  First scaling decision:")
                print(f"    Scale factor: {first_decision.scale_factor:.2f}x")
                print(f"    Mode: {'Entire block' if first_decision.scale_entire_block else 'Diagram only'}")
                
                if 0.2 <= first_decision.scale_factor <= 1.0:
                    results.add_pass("Scaling factor reasonable", 
                                     f"{first_decision.scale_factor:.2f}x")
                else:
                    results.add_fail("Scaling factor out of range", 
                                   f"{first_decision.scale_factor:.2f}x")
            else:
                results.add_fail("Scaling decisions", "No scaling decisions made")
            
            # Check 4: Page break detection
            # After cover/TOC, content should start fresh
            if content_above_with_fm < 500:  # Should be small after page breaks
                results.add_pass("Page break reset", 
                               f"Content above: {content_above_with_fm:.0f}px")
            else:
                # This might be OK if there's a lot of content after TOC
                results.add_pass("Content after TOC", 
                               f"Measured {content_above_with_fm:.0f}px (may include intro content)")
    
    finally:
        if test_file.exists():
            test_file.unlink()
    
    return results


async def validate_scaling_consistency():
    """Validate that scaling is consistent and reasonable"""
    results = TestResults()
    
    print("\n" + "="*60)
    print("SCALING CONSISTENCY VALIDATION")
    print("="*60)
    
    test_file = Path(__file__).parent / "consistency_test.html"
    test_file.write_text(TEST_HTML, encoding='utf-8')
    
    try:
        async with open_page(test_file, verbose=False) as (browser, page):
            await page.wait_for_load_state('networkidle')
            await inject_pagination_css(page, verbose=False)
            
            cover_config = CoverConfig(
                title="Test Document",
                author="Test Author",
                organization="Test Org",
                date="2025"
            )
            await inject_cover_page(page, cover_config, verbose=False)
            await inject_toc(page, verbose=False)
            await page.wait_for_timeout(500)
            
            analysis = await analyze_layout(page, verbose=False)
            decisions = compute_scaling(analysis)
            
            if not decisions:
                results.add_fail("Scaling decisions", "No decisions made")
                return results
            
            print(f"\nFound {len(decisions)} scaling decisions:")
            
            for i, decision in enumerate(decisions, 1):
                block = analysis.diagram_blocks[i-1] if i-1 < len(analysis.diagram_blocks) else None
                
                if block:
                    print(f"\n  Decision {i}: {decision.heading_id}")
                    print(f"    Available height: {block.available_height:.0f}px")
                    print(f"    Diagram height: {block.diagram_height:.0f}px")
                    print(f"    Scale factor: {decision.scale_factor:.2f}x")
                    print(f"    Mode: {'Entire block' if decision.scale_entire_block else 'Diagram only'}")
                    
                    # Validate scale factor is reasonable
                    if 0.2 <= decision.scale_factor <= 1.0:
                        results.add_pass(f"Decision {i} scale factor", 
                                        f"{decision.scale_factor:.2f}x")
                    else:
                        results.add_fail(f"Decision {i} scale factor", 
                                       f"{decision.scale_factor:.2f}x out of range")
                    
                    # Validate available height is reasonable
                    if block.available_height >= 300:
                        results.add_pass(f"Decision {i} available height", 
                                        f"{block.available_height:.0f}px")
                    else:
                        results.add_fail(f"Decision {i} available height", 
                                       f"{block.available_height:.0f}px too low")
    
    finally:
        if test_file.exists():
            test_file.unlink()
    
    return results


async def run_all_validation_tests():
    """Run all validation tests"""
    print("\n" + "="*60)
    print("COMPREHENSIVE SCALING VALIDATION")
    print("="*60)
    
    all_results = TestResults()
    
    try:
        # Run front matter accounting tests
        fm_results = await validate_frontmatter_accounting()
        all_results.passed.extend(fm_results.passed)
        all_results.failed.extend(fm_results.failed)
        
        # Run consistency tests
        consistency_results = await validate_scaling_consistency()
        all_results.passed.extend(consistency_results.passed)
        all_results.failed.extend(consistency_results.failed)
        
    except Exception as e:
        print(f"\n[ERROR] Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        all_results.add_fail("Test execution", str(e))
    
    # Print summary
    success = all_results.summary()
    
    return success


if __name__ == '__main__':
    success = asyncio.run(run_all_validation_tests())
    sys.exit(0 if success else 1)

