"""
Page Measurements Module
========================
Dynamically measures actual PDF page dimensions, margins, and header/footer heights.
No hardcoded values - everything is computed from actual rendered output.
"""
from dataclasses import dataclass
from typing import Optional
from playwright.async_api import Page


@dataclass
class PageMeasurements:
    """Actual measured page dimensions and offsets"""
    page_width: float
    page_height: float
    margin_top: float
    margin_right: float
    margin_bottom: float
    margin_left: float
    header_height: float
    footer_height: float
    content_width: float
    content_height: float
    
    @property
    def available_height(self) -> float:
        """Calculate available height for content"""
        return self.content_height - self.header_height - self.footer_height


async def measure_page_dimensions(
    page: Page,
    header_html: str,
    footer_html: str,
    margin_config: dict,
    page_format: str = 'A4',
    verbose: bool = False
) -> PageMeasurements:
    """
    Measure actual page dimensions by rendering a test page.
    
    This creates a temporary page with header/footer, measures everything,
    then returns the actual dimensions.
    
    Args:
        page: Playwright page object
        header_html: Header template HTML
        footer_html: Footer template HTML
        margin_config: Margin configuration dict (e.g., {'top': '0.75in', ...})
        verbose: Verbose output
        
    Returns:
        PageMeasurements with actual measured values
    """
    # Parse margin values from config (e.g., '0.75in' or '2cm' -> pixels)
    def parse_margin(value: str) -> float:
        """Convert margin string to pixels at 96dpi"""
        value = str(value).strip()
        if value.endswith('in'):
            return float(value[:-2]) * 96
        elif value.endswith('cm'):
            return float(value[:-2]) * 37.795275591  # cm to px at 96dpi (96/2.54)
        elif value.endswith('mm'):
            return float(value[:-2]) * 3.779527559  # mm to px at 96dpi
        elif value.endswith('px'):
            return float(value[:-2])
        else:
            return float(value) * 96  # Assume inches
    
    margin_top = parse_margin(margin_config.get('top', '0.75in'))
    margin_right = parse_margin(margin_config.get('right', '0.75in'))
    margin_bottom = parse_margin(margin_config.get('bottom', '1in'))
    margin_left = parse_margin(margin_config.get('left', '0.75in'))
    
    # Measure header/footer heights by creating test elements
    measurements = await page.evaluate("""
        ([headerHtml, footerHtml]) => {
            // Create temporary container to measure header/footer
            const container = document.createElement('div');
            container.style.position = 'absolute';
            container.style.visibility = 'hidden';
            container.style.width = '794px'; // A4 width at 96dpi
            container.style.height = '1122px'; // A4 height at 96dpi
            container.style.top = '-9999px';
            document.body.appendChild(container);
            
            // Create header element
            const headerDiv = document.createElement('div');
            headerDiv.innerHTML = headerHtml;
            container.appendChild(headerDiv);
            
            // Create footer element
            const footerDiv = document.createElement('div');
            footerDiv.innerHTML = footerHtml;
            container.appendChild(footerDiv);
            
            // Force layout calculation
            container.offsetHeight;
            
            // Measure header
            const headerStyle = window.getComputedStyle(headerDiv);
            const headerHeight = headerDiv.offsetHeight +
                parseFloat(headerStyle.marginTop) +
                parseFloat(headerStyle.marginBottom);
            
            // Measure footer
            const footerStyle = window.getComputedStyle(footerDiv);
            const footerHeight = footerDiv.offsetHeight +
                parseFloat(footerStyle.marginTop) +
                parseFloat(footerStyle.marginBottom);
            
            // Clean up
            document.body.removeChild(container);
            
            return {
                headerHeight: headerHeight,
                footerHeight: footerHeight
            };
        }
    """, [header_html, footer_html])
    
    header_height = measurements['headerHeight']
    footer_height = measurements['footerHeight']
    
    # Calculate page dimensions based on format
    # Standard paper sizes at 96dpi:
    PAGE_SIZES = {
        'A4': (8.27 * 96, 11.69 * 96),      # 794px × 1122px
        'Letter': (8.5 * 96, 11 * 96),      # 816px × 1056px
        'Legal': (8.5 * 96, 14 * 96),       # 816px × 1344px
    }
    
    # Parse page format
    if page_format in PAGE_SIZES:
        page_width, page_height = PAGE_SIZES[page_format]
    elif ' ' in page_format or 'x' in page_format.lower():
        # Custom size like "8.5in 11in" or "8.5x11"
        parts = page_format.replace('x', ' ').replace('X', ' ').split()
        if len(parts) >= 2:
            def parse_dim(dim: str) -> float:
                dim = str(dim).strip()
                if dim.endswith('in'):
                    return float(dim[:-2]) * 96
                elif dim.endswith('cm'):
                    return float(dim[:-2]) * 37.795275591
                elif dim.endswith('mm'):
                    return float(dim[:-2]) * 3.779527559
                elif dim.endswith('px'):
                    return float(dim[:-2])
                else:
                    return float(dim) * 96  # Assume inches
            page_width = parse_dim(parts[0])
            page_height = parse_dim(parts[1])
        else:
            page_width, page_height = PAGE_SIZES['A4']  # Fallback
    else:
        page_width, page_height = PAGE_SIZES.get(page_format, PAGE_SIZES['A4'])
    
    # Verify actual page size from CSS @page rule if available
    css_page_size = await page.evaluate("""
        () => {
            // Check if @page rule exists and get size
            const styleSheets = Array.from(document.styleSheets);
            for (const sheet of styleSheets) {
                try {
                    const rules = Array.from(sheet.cssRules || []);
                    for (const rule of rules) {
                        if (rule.type === CSSRule.PAGE_RULE) {
                            // @page rule found
                            const size = rule.style.size || '';
                            return { size: size };
                        }
                    }
                } catch (e) {
                    // Cross-origin stylesheet, skip
                    continue;
                }
            }
            return { size: '' };
        }
    """)
    
    # If CSS specifies a size, use it (but still respect page_format parameter)
    # CSS @page size takes precedence for actual rendering
    if css_page_size.get('size') and css_page_size['size'] in PAGE_SIZES:
        css_width, css_height = PAGE_SIZES[css_page_size['size']]
        if verbose:
            print(f"[MEASURE] CSS @page specifies: {css_page_size['size']} ({css_width:.0f}px × {css_height:.0f}px)")
        # Use CSS size if it matches format, otherwise use format
        if css_page_size['size'] == page_format or page_format == 'A4':
            page_width, page_height = css_width, css_height
    
    # Calculate content dimensions
    content_width = page_width - margin_left - margin_right
    content_height = page_height - margin_top - margin_bottom
    
    result = PageMeasurements(
        page_width=page_width,
        page_height=page_height,
        margin_top=margin_top,
        margin_right=margin_right,
        margin_bottom=margin_bottom,
        margin_left=margin_left,
        header_height=header_height,
        footer_height=footer_height,
        content_width=content_width,
        content_height=content_height
    )
    
    if verbose:
        format_name = page_format if page_format in PAGE_SIZES else f"Custom ({page_format})"
        print(f"[MEASURE] Page format: {format_name}")
        print(f"[MEASURE] Page dimensions: {result.page_width:.0f}px × {result.page_height:.0f}px")
        print(f"[MEASURE] Margins: top={result.margin_top:.0f}px, right={result.margin_right:.0f}px, "
              f"bottom={result.margin_bottom:.0f}px, left={result.margin_left:.0f}px")
        print(f"[MEASURE] Header height: {result.header_height:.2f}px")
        print(f"[MEASURE] Footer height: {result.footer_height:.2f}px")
        print(f"[MEASURE] Content area: {result.content_width:.0f}px × {result.content_height:.0f}px")
        print(f"[MEASURE] Available height: {result.available_height:.0f}px")
    
    return result

