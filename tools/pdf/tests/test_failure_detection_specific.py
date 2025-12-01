#!/usr/bin/env python3
"""
Failure Detection and Recovery - Specific Test
==============================================
Tests the actual "Failure Detection and Recovery" diagram from the document
to validate scaling decisions.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from playwright_pdf.pipeline import generate_pdf
from playwright_pdf.config import PdfGenerationConfig
from playwright_pdf.dom_analyzer import analyze_layout
from playwright_pdf.layout_transformer import compute_scaling
from playwright_pdf.browser import open_page
from playwright_pdf.styles import inject_pagination_css
from playwright_pdf.decorators.cover import inject_cover_page
from playwright_pdf.decorators.toc import inject_toc
from playwright_pdf.page_measurements import measure_page_dimensions
from playwright_pdf.pdf_renderer import build_header_footer
from playwright_pdf.config import CoverConfig

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    OK = f"{Fore.GREEN}[OK]{Style.RESET_ALL}"
    FAIL = f"{Fore.RED}[FAIL]{Style.RESET_ALL}"
    INFO = f"{Fore.CYAN}[INFO]{Style.RESET_ALL}"
    WARN = f"{Fore.YELLOW}[WARN]{Style.RESET_ALL}"
except ImportError:
    OK = "[OK]"
    FAIL = "[FAIL]"
    INFO = "[INFO]"
    WARN = "[WARN]"


async def test_failure_detection_from_actual_document():
    """Test Failure Detection and Recovery diagram from actual document"""
    print("\n" + "="*70)
    print("FAILURE DETECTION AND RECOVERY - ACTUAL DOCUMENT TEST")
    print("="*70)
    
    html_file = Path(__file__).parent.parent.parent / "docs" / "ReportingManager_ArchitectureProposal_Enhanced.html"
    
    if not html_file.exists():
        print(f"{FAIL} HTML file not found: {html_file}")
        return False
    
    try:
        async with open_page(html_file, verbose=False) as (browser, page):
            await page.wait_for_load_state('networkidle')
            await inject_pagination_css(page, verbose=False)
            
            # Inject cover and TOC (same as production)
            cover_config = CoverConfig(
                title="Reporting Manager Architecture Proposal",
                author="Matt Jeffcoat",
                organization="[Organization Name]",
                date="November 2025"
            )
            await inject_cover_page(page, cover_config, verbose=False)
            await inject_toc(page, verbose=False)
            await page.wait_for_timeout(500)
            
            # Measure page dimensions (using new measurement system)
            header_html, footer_html = build_header_footer(
                title="Reporting Manager Architecture Proposal",
                organization="[Organization Name]",
                author="Matt Jeffcoat",
                date="November 2025"
            )
            margin_config = {
                'top': '0.75in',
                'right': '0.75in',
                'bottom': '1in',
                'left': '0.75in'
            }
            page_measurements = await measure_page_dimensions(
                page,
                header_html,
                footer_html,
                margin_config,
                page_format='A4',
                verbose=True
            )
            
            # Analyze layout with measured dimensions
            analysis = await analyze_layout(page, page_measurements=page_measurements, verbose=True)
            
            # Find Failure Detection and Recovery diagram
            failure_detection_block = None
            for block in analysis.diagram_blocks:
                if 'failure' in block.heading_text.lower() and 'detection' in block.heading_text.lower():
                    failure_detection_block = block
                    break
            
            if not failure_detection_block:
                print(f"\n{WARN} Failure Detection and Recovery diagram not found")
                print(f"Available diagrams:")
                for block in analysis.diagram_blocks:
                    print(f"  - {block.heading_text}")
                return False
            
            print(f"\n{'='*70}")
            print(f"FAILURE DETECTION AND RECOVERY DIAGRAM ANALYSIS")
            print(f"{'='*70}")
            
            breakdown = failure_detection_block.measurement_breakdown or {}
            
            print(f"\n[Page Measurements]")
            print(f"  Page format: A4")
            print(f"  Page dimensions: {page_measurements.page_width:.0f}px × {page_measurements.page_height:.0f}px")
            print(f"  Margins: top={page_measurements.margin_top:.0f}px, bottom={page_measurements.margin_bottom:.0f}px")
            print(f"  Header height: {page_measurements.header_height:.2f}px (MEASURED)")
            print(f"  Footer height: {page_measurements.footer_height:.2f}px (MEASURED)")
            print(f"  Available height: {page_measurements.available_height:.0f}px")
            
            print(f"\n[Content Analysis]")
            print(f"  Heading: '{failure_detection_block.heading_text}'")
            print(f"  Content above heading: {breakdown.get('contentAboveHeading', 0):.0f}px")
            print(f"  Heading height: {failure_detection_block.heading_height:.0f}px")
            print(f"  Elements between heading and diagram: {failure_detection_block.elements_between_height:.0f}px")
            print(f"  Diagram height (raw): {failure_detection_block.diagram_height:.0f}px")
            print(f"  Container margins: {breakdown.get('containerMargins', 0):.0f}px")
            print(f"  Total content height: {failure_detection_block.total_content_height:.0f}px")
            
            print(f"\n[Available Space Calculation]")
            print(f"  Page height: {page_measurements.page_height:.0f}px")
            print(f"  Minus top margin: {page_measurements.margin_top:.0f}px")
            print(f"  Minus bottom margin: {page_measurements.margin_bottom:.0f}px")
            print(f"  Minus header: {page_measurements.header_height:.2f}px")
            print(f"  Minus footer: {page_measurements.footer_height:.2f}px")
            print(f"  = Available: {page_measurements.available_height:.0f}px")
            
            # Account for content above
            content_above = breakdown.get('contentAboveHeading', 0)
            pages_above = content_above / page_measurements.available_height
            space_on_page = content_above % page_measurements.available_height
            
            print(f"\n[Position Analysis]")
            print(f"  Content above heading: {content_above:.0f}px")
            print(f"  Pages above: {pages_above:.2f}")
            print(f"  Space used on current page: {space_on_page:.0f}px")
            print(f"  Real available height: {failure_detection_block.available_height:.0f}px")
            
            print(f"\n[Overflow Analysis]")
            print(f"  Total content height: {failure_detection_block.total_content_height:.0f}px")
            print(f"  Available height: {failure_detection_block.available_height:.0f}px")
            print(f"  Overflow: {failure_detection_block.total_content_height - failure_detection_block.available_height:.0f}px")
            print(f"  Overflow ratio: {failure_detection_block.overflow_ratio:.2f}x")
            
            # Compute scaling decision
            decisions = compute_scaling(analysis)
            failure_decision = None
            for decision in decisions:
                if decision.heading_id == failure_detection_block.heading_id:
                    failure_decision = decision
                    break
            
            if failure_decision:
                print(f"\n[Scaling Decision]")
                print(f"  Scale factor: {failure_decision.scale_factor:.2f}x ({failure_decision.scale_factor*100:.0f}%)")
                print(f"  Mode: {'Entire block' if failure_decision.scale_entire_block else 'Diagram only'}")
                print(f"  Force pre-break: {failure_decision.force_pre_break}")
                print(f"  Force post-break: {failure_decision.force_post_break}")
                
                # Calculate expected scale
                diagram_height_with_container = (
                    failure_detection_block.diagram_height +
                    breakdown.get('containerMargins', 0) +
                    breakdown.get('containerPadding', 0) +
                    breakdown.get('containerBorders', 0)
                )
                non_diagram_height = failure_detection_block.total_content_height - diagram_height_with_container
                available_for_diagram = failure_detection_block.available_height - 48 - non_diagram_height
                expected_scale = available_for_diagram / diagram_height_with_container if diagram_height_with_container > 0 else 1.0
                
                print(f"\n[Expected vs Actual]")
                print(f"  Expected scale (based on available space): {expected_scale:.2f}x")
                print(f"  Actual scale: {failure_decision.scale_factor:.2f}x")
                
                diff = abs(expected_scale - failure_decision.scale_factor)
                if diff < 0.1:
                    print(f"  {OK} Scaling matches expected (diff: {diff:.2f})")
                else:
                    print(f"  {WARN} Scaling differs from expected (diff: {diff:.2f})")
                    print(f"    This may be due to minimum scale limits or overflow thresholds")
                
                # Validation
                print(f"\n[Validation]")
                if failure_detection_block.available_height >= 400:
                    print(f"  {OK} Available height reasonable ({failure_detection_block.available_height:.0f}px >= 400px)")
                else:
                    print(f"  {FAIL} Available height too low ({failure_detection_block.available_height:.0f}px < 400px)")
                
                if 0.2 <= failure_decision.scale_factor <= 1.0:
                    print(f"  {OK} Scale factor reasonable ({failure_decision.scale_factor:.2f}x)")
                else:
                    print(f"  {FAIL} Scale factor out of range ({failure_decision.scale_factor:.2f}x)")
                
                if content_above > 0:
                    print(f"  {OK} Content above measured ({content_above:.0f}px)")
                else:
                    print(f"  {WARN} Content above not measured (may be at top of page)")
                
                return True
            else:
                print(f"\n{FAIL} No scaling decision found for Failure Detection diagram")
                return False
                
    except Exception as e:
        print(f"\n{FAIL} Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run the test"""
    print("\n" + "="*70)
    print("FAILURE DETECTION AND RECOVERY - SPECIFIC TEST")
    print("="*70)
    
    success = await test_failure_detection_from_actual_document()
    
    print("\n" + "="*70)
    print("TEST RESULT")
    print("="*70)
    if success:
        print(f"{OK} Test passed - Failure Detection diagram analyzed correctly")
    else:
        print(f"{FAIL} Test failed - Review output above")
    
    return success


if __name__ == '__main__':
    success = asyncio.run(main())
    sys.exit(0 if success else 1)

