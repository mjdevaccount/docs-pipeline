"""
DOM Analyzer - Pure Analysis
=============================
Only reads DOM and returns LayoutAnalysis model.
No mutation, no scaling decisions, no CSS injection.
"""
from typing import List, Optional, TYPE_CHECKING
from playwright.async_api import Page
from .layout_model import LayoutAnalysis, DiagramBlock

if TYPE_CHECKING:
    from .page_measurements import PageMeasurements

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    WARN = f"{Fore.YELLOW}[WARN]{Style.RESET_ALL}"
    INFO = f"{Fore.CYAN}[INFO]{Style.RESET_ALL}"
except ImportError:
    WARN = "[WARN]"
    INFO = "[INFO]"


async def analyze_layout(
    page: Page,
    page_measurements: Optional['PageMeasurements'] = None,  # type: ignore
    verbose: bool = False
) -> LayoutAnalysis:
    """
    Analyze DOM layout and return structured analysis model.
    
    This is pure analysis - no mutations, no scaling decisions.
    Returns a LayoutAnalysis dataclass that can be used for
    scaling decisions in a separate phase.
    """
    try:
        # Prepare measurements to pass to JavaScript
        if page_measurements:
            measurements_dict = {
                'pageHeight': page_measurements.page_height,
                'marginTop': page_measurements.margin_top,
                'marginBottom': page_measurements.margin_bottom,
                'headerHeight': page_measurements.header_height,
                'footerHeight': page_measurements.footer_height,
            }
        else:
            # Fallback: use A4 defaults (should not happen in production)
            measurements_dict = {
                'pageHeight': 11.69 * 96,
                'marginTop': 0.75 * 96,
                'marginBottom': 1.0 * 96,
                'headerHeight': 0,
                'footerHeight': 0,
            }
        
        raw_pairs = await page.evaluate("""
            (pageMeasurements) => {
                const problems = [];
                // Allow hero/cover sections that start with an H1
                const headings = document.querySelectorAll('h1, h2, h3');
                
                // STEP 1: Calculate True Available Space
                // Use measured values passed from Python (no hardcoding)
                const measurements = pageMeasurements || {};
                const pageHeight = measurements.pageHeight || (11.69 * 96);  // Fallback to A4 if not provided
                const marginTop = measurements.marginTop || (0.75 * 96);
                const marginBottom = measurements.marginBottom || (1 * 96);
                const headerHeight = measurements.headerHeight || 0;
                const footerHeight = measurements.footerHeight || 0;
                
                // Calculate available height from measured values
                let availableHeight = pageHeight - marginTop - marginBottom - headerHeight - footerHeight;
                
                headings.forEach((heading, idx) => {
                    // Find diagram
                    let next = heading.nextElementSibling;
                    let foundDiagram = false;
                    let diagramElement = null;
                    
                    // Look deeper for hero sections that have metadata blocks
                    for (let i = 0; i < 10 && next && !foundDiagram; i++) {
                        const svg = next.querySelector('svg');
                        const img = next.querySelector('img[src$=".svg"]');
                        
                        if (svg) {
                            diagramElement = svg;
                            foundDiagram = true;
                            break;
                        } else if (img) {
                            diagramElement = img;
                            foundDiagram = true;
                            break;
                        }
                        
                        if (next.tagName && /^H[1-6]$/.test(next.tagName)) {
                            break;
                        }
                        
                        next = next.nextElementSibling;
                    }
                    
                    if (foundDiagram && diagramElement) {
                        // CRITICAL FIX: Use viewport-based measurement instead of cumulative height
                        // This accounts for actual page position in PDF context
                        
                        const effectivePageHeight = pageHeight - marginTop - marginBottom - headerHeight - footerHeight;
                        
                        // Find the last page-break element before this heading (cover, TOC, or explicit breaks)
                        let lastPageBreak = null;
                        let elemBeforeHeading = document.body.firstElementChild;
                        
                        while (elemBeforeHeading && elemBeforeHeading !== heading) {
                            const style = window.getComputedStyle(elemBeforeHeading);
                            const hasPageBreak = (
                                (elemBeforeHeading.classList && (
                                    elemBeforeHeading.classList.contains('cover-page-wrapper') ||
                                    elemBeforeHeading.classList.contains('toc-wrapper') ||
                                    elemBeforeHeading.classList.contains('page-break')
                                )) ||
                                style.pageBreakAfter === 'always' ||
                                style.breakAfter === 'page'
                            );
                            
                            if (hasPageBreak) {
                                lastPageBreak = elemBeforeHeading;
                            }
                            
                            elemBeforeHeading = elemBeforeHeading.nextElementSibling;
                        }
                        
                        // Measure height from last page break to heading (or from body start if no page break)
                        let contentAboveHeading = 0;
                        let measureStart = lastPageBreak ? lastPageBreak.nextElementSibling : document.body.firstElementChild;
                        
                        while (measureStart && measureStart !== heading) {
                            // Skip page-break elements themselves
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
                                
                                contentAboveHeading += height + marginTop + marginBottom + paddingTop + paddingBottom;
                            }
                            
                            measureStart = measureStart.nextElementSibling;
                        }
                        
                        // Calculate available height based on content above
                        // CRITICAL: Account for natural page breaks in PDF
                        // Smarter logic: If content above spans multiple pages, heading is likely at top of new page
                        
                        let realAvailableHeight;
                        const pagesAbove = Math.floor(contentAboveHeading / effectivePageHeight);
                        const spaceUsedOnCurrentPage = contentAboveHeading % effectivePageHeight;
                        
                        // Threshold for "near top of page" - be generous (200px)
                        const nearTopThreshold = 200;
                        
                        if (pagesAbove >= 2) {
                            // Content above spans 2+ full pages - heading is almost certainly at top of new page
                            // Use full available height (small buffer for safety)
                            realAvailableHeight = effectivePageHeight - 50;
                        } else if (pagesAbove >= 1) {
                            // Content above spans 1+ full pages
                            // If remainder is small, heading is at top of new page
                            // If remainder is large, heading might be lower, but still give benefit of doubt
                            if (spaceUsedOnCurrentPage < nearTopThreshold) {
                                // Heading is near top of new page
                                realAvailableHeight = effectivePageHeight - Math.max(50, spaceUsedOnCurrentPage);
                            } else {
                                // Heading might be lower, but still on new page
                                // Use generous calculation: assume heading is at least 200px from top
                                const assumedTopOffset = Math.min(spaceUsedOnCurrentPage, nearTopThreshold);
                                realAvailableHeight = effectivePageHeight - assumedTopOffset;
                                // Ensure minimum reasonable height
                                realAvailableHeight = Math.max(500, realAvailableHeight);
                            }
                        } else if (contentAboveHeading < 100) {
                            // Very little content above - heading is near top of page
                            realAvailableHeight = effectivePageHeight - 50;
                        } else {
                            // Content above is on same page - reduce available space
                            // But be generous: assume content might naturally flow to next page
                            // Use a progressive reduction rather than linear
                            if (contentAboveHeading < effectivePageHeight * 0.5) {
                                // Less than half page used - still good space available
                                realAvailableHeight = effectivePageHeight - contentAboveHeading;
                            } else {
                                // More than half page used - assume heading might be on next page
                                // Use modulo to find position, but be generous
                                const remainder = contentAboveHeading % effectivePageHeight;
                                realAvailableHeight = Math.max(500, effectivePageHeight - Math.min(remainder, nearTopThreshold));
                            }
                        }
                        
                        // STEP 2: Sum ALL page content from heading to diagram
                        let totalContentHeight = 0;
                        const measurementBreakdown = {
                            headingHeight: 0,
                            headingMargins: 0,
                            headingPadding: 0,
                            headingBorders: 0,
                            parentHeadingHeight: 0,
                            parentHeadingMargins: 0,
                            parentHeadingBorders: 0,
                            intermediateElements: [],
                            diagramHeight: 0,
                            containerMargins: 0,
                            containerPadding: 0,
                            containerBorders: 0,
                            lineHeightAdjustment: 0,
                            contentAboveHeading: Math.max(0, contentAboveHeading),
                            realAvailableHeight: realAvailableHeight
                        };
                        
                        // Measure primary heading
                        const headingStyle = window.getComputedStyle(heading);
                        const headingOffsetHeight = heading.offsetHeight;
                        const headingMarginTop = parseFloat(headingStyle.marginTop) || 0;
                        const headingMarginBottom = parseFloat(headingStyle.marginBottom) || 0;
                        const headingPaddingTop = parseFloat(headingStyle.paddingTop) || 0;
                        const headingPaddingBottom = parseFloat(headingStyle.paddingBottom) || 0;
                        const headingBorderTop = parseFloat(headingStyle.borderTopWidth) || 0;
                        const headingBorderBottom = parseFloat(headingStyle.borderBottomWidth) || 0;
                        
                        measurementBreakdown.headingHeight = headingOffsetHeight;
                        measurementBreakdown.headingMargins = headingMarginTop + headingMarginBottom;
                        measurementBreakdown.headingPadding = headingPaddingTop + headingPaddingBottom;
                        measurementBreakdown.headingBorders = headingBorderTop + headingBorderBottom;
                        
                        totalContentHeight += headingOffsetHeight + headingMarginTop + headingMarginBottom +
                                            headingPaddingTop + headingPaddingBottom +
                                            headingBorderTop + headingBorderBottom;
                        
                        // If h3, check for h2 ABOVE and sum it
                        if (heading.tagName === 'H3') {
                            let prev = heading.previousElementSibling;
                            while (prev && !prev.tagName) {
                                prev = prev.previousElementSibling;
                            }
                            
                            if (prev && prev.tagName === 'H2') {
                                const prevStyle = window.getComputedStyle(prev);
                                const prevOffsetHeight = prev.offsetHeight;
                                const prevMarginTop = parseFloat(prevStyle.marginTop) || 0;
                                const prevMarginBottom = parseFloat(prevStyle.marginBottom) || 0;
                                const prevBorderTop = parseFloat(prevStyle.borderTopWidth) || 0;
                                const prevBorderBottom = parseFloat(prevStyle.borderBottomWidth) || 0;
                                
                                measurementBreakdown.parentHeadingHeight = prevOffsetHeight;
                                measurementBreakdown.parentHeadingMargins = prevMarginTop + prevMarginBottom;
                                measurementBreakdown.parentHeadingBorders = prevBorderTop + prevBorderBottom;
                                
                                totalContentHeight += prevOffsetHeight + prevMarginTop + prevMarginBottom +
                                                    prevBorderTop + prevBorderBottom;
                            }
                        }
                        
                        // If h2, check for h3 BELOW and sum it
                        if (heading.tagName === 'H2' && heading.nextElementSibling && 
                            heading.nextElementSibling.tagName === 'H3') {
                            const nextH3 = heading.nextElementSibling;
                            const nextStyle = window.getComputedStyle(nextH3);
                            const nextOffsetHeight = nextH3.offsetHeight;
                            const nextMarginTop = parseFloat(nextStyle.marginTop) || 0;
                            const nextMarginBottom = parseFloat(nextStyle.marginBottom) || 0;
                            const nextBorderTop = parseFloat(nextStyle.borderTopWidth) || 0;
                            const nextBorderBottom = parseFloat(nextStyle.borderBottomWidth) || 0;
                            
                            measurementBreakdown.parentHeadingHeight = nextOffsetHeight;
                            measurementBreakdown.parentHeadingMargins = nextMarginTop + nextMarginBottom;
                            measurementBreakdown.parentHeadingBorders = nextBorderTop + nextBorderBottom;
                            
                            totalContentHeight += nextOffsetHeight + nextMarginTop + nextMarginBottom +
                                                nextBorderTop + nextBorderBottom;
                        }
                        
                        // Walk ALL intermediate siblings between heading and diagram container
                        const diagramContainer = diagramElement.parentElement;
                        let current = heading.nextElementSibling;
                        
                        while (current && current !== diagramContainer && current !== diagramElement) {
                            if (current.nodeType === Node.ELEMENT_NODE && 
                                current.tagName && !/^H[1-6]$/.test(current.tagName)) {
                                const elemStyle = window.getComputedStyle(current);
                                const elemOffsetHeight = current.offsetHeight;
                                const elemMarginTop = parseFloat(elemStyle.marginTop) || 0;
                                const elemMarginBottom = parseFloat(elemStyle.marginBottom) || 0;
                                const elemPaddingTop = parseFloat(elemStyle.paddingTop) || 0;
                                const elemPaddingBottom = parseFloat(elemStyle.paddingBottom) || 0;
                                const elemBorderTop = parseFloat(elemStyle.borderTopWidth) || 0;
                                const elemBorderBottom = parseFloat(elemStyle.borderBottomWidth) || 0;
                                
                                const elemHeight = elemOffsetHeight + elemMarginTop + elemMarginBottom +
                                                  elemPaddingTop + elemPaddingBottom +
                                                  elemBorderTop + elemBorderBottom;
                                
                                measurementBreakdown.intermediateElements.push({
                                    tag: current.tagName.toLowerCase(),
                                    height: elemOffsetHeight,
                                    margins: elemMarginTop + elemMarginBottom,
                                    padding: elemPaddingTop + elemPaddingBottom,
                                    borders: elemBorderTop + elemBorderBottom,
                                    total: elemHeight
                                });
                                
                                totalContentHeight += elemHeight;
                            }
                            current = current.nextElementSibling;
                        }
                        
                        // Measure diagram element itself
                        const diagramRect = diagramElement.getBoundingClientRect();
                        const diagramHeight = diagramRect.height;
                        measurementBreakdown.diagramHeight = diagramHeight;
                        totalContentHeight += diagramHeight;
                        
                        // Measure diagram container (figure, div, etc.) - FULL box model
                        if (diagramContainer && diagramContainer !== diagramElement) {
                            const containerStyle = window.getComputedStyle(diagramContainer);
                            const containerOffsetHeight = diagramContainer.offsetHeight;
                            
                            const boxSizing = containerStyle.boxSizing || 'content-box';
                            const containerMarginTop = parseFloat(containerStyle.marginTop) || 0;
                            const containerMarginBottom = parseFloat(containerStyle.marginBottom) || 0;
                            const containerPaddingTop = parseFloat(containerStyle.paddingTop) || 0;
                            const containerPaddingBottom = parseFloat(containerStyle.paddingBottom) || 0;
                            const containerBorderTop = parseFloat(containerStyle.borderTopWidth) || 0;
                            const containerBorderBottom = parseFloat(containerStyle.borderBottomWidth) || 0;
                            
                            measurementBreakdown.containerMargins = containerMarginTop + containerMarginBottom;
                            measurementBreakdown.containerPadding = containerPaddingTop + containerPaddingBottom;
                            measurementBreakdown.containerBorders = containerBorderTop + containerBorderBottom;
                            
                            if (boxSizing === 'border-box') {
                                totalContentHeight += containerMarginTop + containerMarginBottom;
                            } else {
                                totalContentHeight += containerMarginTop + containerMarginBottom +
                                                    containerPaddingTop + containerPaddingBottom +
                                                    containerBorderTop + containerBorderBottom;
                            }
                        }
                        
                        // Account for line-height (only if it's a unitless ratio, not pixels)
                        const lineHeightValue = headingStyle.lineHeight;
                        if (lineHeightValue && !lineHeightValue.includes('px') && !lineHeightValue.includes('%')) {
                            // Unitless line-height (e.g., "1.5")
                            const headingLineHeight = parseFloat(lineHeightValue) || 1;
                            if (headingLineHeight > 1.0 && headingOffsetHeight > parseFloat(headingStyle.fontSize) * 1.5) {
                                const fontSize = parseFloat(headingStyle.fontSize) || 16;
                                const lineHeightSpace = (headingLineHeight - 1.0) * fontSize;
                                measurementBreakdown.lineHeightAdjustment += lineHeightSpace;
                                totalContentHeight += lineHeightSpace;
                            }
                        }
                        
                        // Add safety buffer
                        const safetyBuffer = 48;
                        const totalHeight = totalContentHeight + safetyBuffer;
                        
                        // Use realAvailableHeight instead of fixed availableHeight
                        // This accounts for content already on the page above the heading
                        if (totalHeight > realAvailableHeight) {
                            const headingId = heading.id || `heading-${idx}`;
                            if (!heading.id) heading.id = headingId;
                            
                            problems.push({
                                headingId: headingId,
                                headingText: heading.textContent.trim().substring(0, 50),
                                headingHeight: measurementBreakdown.headingHeight + 
                                             measurementBreakdown.headingMargins + 
                                             measurementBreakdown.headingBorders +
                                             measurementBreakdown.parentHeadingHeight +
                                             measurementBreakdown.parentHeadingMargins +
                                             measurementBreakdown.parentHeadingBorders,
                                elementsBetweenHeight: measurementBreakdown.intermediateElements.reduce((sum, el) => sum + el.total, 0),
                                diagramHeight: diagramHeight,
                                diagramTotalHeight: diagramHeight + measurementBreakdown.containerMargins +
                                                  measurementBreakdown.containerPadding +
                                                  measurementBreakdown.containerBorders,
                                measurementBreakdown: measurementBreakdown,
                                totalContentHeight: totalContentHeight,
                                totalHeight: totalHeight,
                                availableHeight: realAvailableHeight,  // Use real available height
                                overflowRatio: totalHeight / realAvailableHeight,
                                diagramType: diagramElement.tagName.toLowerCase(),
                                diagramSrc: diagramElement.src || 'inline-svg',
                                headerHeight: headerHeight,
                                footerHeight: footerHeight
                            });
                        }
                    }
                });
                
                return {
                    problems: problems,
                    pageHeight: pageHeight,
                    measurements: measurements,
                    availableHeight: availableHeight
                };
            }
        """, measurements_dict)
        
        if not raw_pairs or not raw_pairs.get('problems'):
            return LayoutAnalysis(
                page_height=raw_pairs.get('pageHeight', 1122) if raw_pairs else 1122,
                available_height=raw_pairs.get('availableHeight', 800) if raw_pairs else 800,
                diagram_blocks=[]
            )
        
        problems = raw_pairs['problems']
        sample = problems[0]
        
        analysis = LayoutAnalysis(
            page_height=raw_pairs.get('pageHeight', 1122),
            available_height=sample['availableHeight'],
        )
        
        for p in problems:
            breakdown = p.get('measurementBreakdown', {})
            analysis.diagram_blocks.append(
                DiagramBlock(
                    heading_id=p['headingId'],
                    heading_text=p['headingText'],
                    diagram_type=p['diagramType'],
                    diagram_selector=f"#{p['headingId']}",
                    heading_height=p['headingHeight'],
                    elements_between_height=p.get('elementsBetweenHeight', 0.0),
                    diagram_height=p['diagramHeight'],
                    container_margins=breakdown.get('containerMargins', 0.0),
                    container_padding=breakdown.get('containerPadding', 0.0),
                    container_borders=breakdown.get('containerBorders', 0.0),
                    total_content_height=p['totalContentHeight'],
                    available_height=p['availableHeight'],
                    overflow_ratio=p['overflowRatio'],
                    header_height=p['headerHeight'],
                    footer_height=p['footerHeight'],
                    measurement_breakdown=breakdown
                )
            )
        
        if verbose and problems:
            _log_analysis(analysis, problems)
        
        return analysis
        
    except Exception as e:
        if verbose:
            print(f"{WARN} Layout analysis failed: {e}")
            import traceback
            traceback.print_exc()
        return LayoutAnalysis(page_height=960, available_height=800, diagram_blocks=[])


def _log_analysis(analysis: LayoutAnalysis, problems: List[dict]):
    """Log detailed analysis breakdown"""
    print(f"{WARN} Found {len(problems)} heading+diagram pairs needing adjustment:")
    print(f"\n{INFO} Available height calculation:")
    print(f"      Page height: {analysis.page_height:.0f}px (A4 at 96dpi)")
    print(f"      Top margin: 72px (0.75in)")
    print(f"      Bottom margin: 96px (1in)")
    if problems[0].get('headerHeight'):
        print(f"      Header height: {problems[0]['headerHeight']:.0f}px (measured)")
    else:
        print(f"      Header height: 30px (estimated)")
    if problems[0].get('footerHeight'):
        print(f"      Footer height: {problems[0]['footerHeight']:.0f}px (measured)")
    else:
        print(f"      Footer height: 30px (estimated)")
    
    # Show both theoretical and real available height
    first_breakdown = problems[0].get('measurementBreakdown', {})
    real_available = first_breakdown.get('realAvailableHeight', problems[0]['availableHeight'])
    content_above = first_breakdown.get('contentAboveHeading', 0.0)
    print(f"      Theoretical available height: {problems[0]['availableHeight']:.0f}px")
    if content_above > 0:
        print(f"      Content above heading: {content_above:.0f}px")
        print(f"      Real available height: {real_available:.0f}px")
    print()
    
    for p in problems:
        breakdown = p.get('measurementBreakdown', {})
        print(f"  - '{p['headingText']}':")
        print(f"      [HEADING] Primary heading:")
        print(f"          Height: {breakdown.get('headingHeight', 0):.0f}px")
        print(f"          Margins: {breakdown.get('headingMargins', 0):.0f}px")
        print(f"          Padding: {breakdown.get('headingPadding', 0):.0f}px")
        print(f"          Borders: {breakdown.get('headingBorders', 0):.0f}px")
        if breakdown.get('parentHeadingHeight', 0) > 0:
            print(f"      [PARENT HEADING] h2/h3:")
            print(f"          Height: {breakdown.get('parentHeadingHeight', 0):.0f}px")
            print(f"          Margins: {breakdown.get('parentHeadingMargins', 0):.0f}px")
            print(f"          Borders: {breakdown.get('parentHeadingBorders', 0):.0f}px")
        if breakdown.get('intermediateElements', []):
            print(f"      [INTERMEDIATE] Elements between heading and diagram:")
            for i, elem in enumerate(breakdown['intermediateElements'], 1):
                print(f"          [{i}] <{elem['tag']}>: {elem['total']:.0f}px " +
                      f"(height: {elem['height']:.0f}px, margins: {elem['margins']:.0f}px, " +
                      f"padding: {elem['padding']:.0f}px, borders: {elem['borders']:.0f}px)")
        else:
            print(f"      [INTERMEDIATE] No elements between heading and diagram")
        print(f"      [DIAGRAM] Raw SVG/IMG height: {p['diagramHeight']:.0f}px")
        print(f"      [CONTAINER] Diagram container:")
        print(f"          Margins: {breakdown.get('containerMargins', 0):.0f}px")
        print(f"          Padding: {breakdown.get('containerPadding', 0):.0f}px")
        print(f"          Borders: {breakdown.get('containerBorders', 0):.0f}px")
        if breakdown.get('lineHeightAdjustment', 0) > 0:
            print(f"      [LINE-HEIGHT] Multi-line adjustment: {breakdown.get('lineHeightAdjustment', 0):.0f}px")
        print(f"      [BUFFER] Safety buffer: 48px")
        print(f"      {'=' * 60}")
        print(f"      [TOTAL] Total content height: {p.get('totalContentHeight', p['totalHeight'] - 48):.0f}px")
        print(f"      [TOTAL] Total height (with buffer): {p['totalHeight']:.0f}px")
        print(f"      [AVAILABLE] Available height: {p['availableHeight']:.0f}px")
        print(f"      [OVERFLOW] Overflow: {p['totalHeight'] - p['availableHeight']:.0f}px ({p['overflowRatio']:.2f}x)")
        print()

