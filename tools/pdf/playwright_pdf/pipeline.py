"""
Pipeline Orchestrator
======================
High-level orchestration of the PDF generation pipeline.
Wires all phases together in the correct order.
"""
from pathlib import Path
from playwright.async_api import Page, Browser

from .browser import open_page
from .dom_analyzer import analyze_layout
from .layout_transformer import compute_scaling, apply_scaling
from .styles import inject_fonts, inject_pagination_css, inject_custom_css
from .decorators.cover import inject_cover_page
from .decorators.toc import inject_toc
from .decorators.watermark import add_watermark
from .pdf_renderer import render_pdf, build_header_footer, DEFAULT_MARGINS
from .postprocess import extract_headings_from_page, add_bookmarks_to_pdf, embed_metadata
from .config import PdfGenerationConfig
from .page_measurements import measure_page_dimensions
from .utils import extract_margins_from_css, detect_dark_mode

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    INFO = f"{Fore.CYAN}[INFO]{Style.RESET_ALL}"
    ERR = f"{Fore.RED}[ERROR]{Style.RESET_ALL}"
except ImportError:
    INFO = "[INFO]"
    ERR = "[ERROR]"


async def generate_pdf(config: PdfGenerationConfig) -> bool:
    """
    Generate PDF from HTML using the modular pipeline.
    
    Phases:
    1. Load → HTML → Playwright page
    2. Analyze → read DOM → layout model
    3. Transform → layout model → scaling decisions → DOM mutations
    4. Decorate → cover, TOC, pagination CSS, watermark
    5. Render → Chromium print → PDF
    6. Post-process → metadata + bookmarks
    
    Args:
        config: PDF generation configuration
    
    Returns:
        bool: True if successful
    """
    try:
        # Phase 1: Load HTML into Playwright page
        async with open_page(config.html_file, verbose=config.verbose) as (browser, page):
            # Extract metadata from HTML meta tags (always extract, fill in missing fields)
            # This ensures frontmatter like classification, version, type are captured
            html_metadata = await page.evaluate("""
                () => {
                    const meta = {};
                    const authorEl = document.querySelector('meta[name="author"]');
                    const orgEl = document.querySelector('meta[name="organization"]');
                    const dateEl = document.querySelector('meta[name="date"]');
                    const typeEl = document.querySelector('meta[name="type"]');
                    const classificationEl = document.querySelector('meta[name="classification"]');
                    const versionEl = document.querySelector('meta[name="version"]');
                    
                    if (authorEl) meta.author = authorEl.content;
                    if (orgEl) meta.organization = orgEl.content;
                    if (dateEl) meta.date = dateEl.content;
                    if (typeEl) meta.type = typeEl.content;
                    if (classificationEl) meta.classification = classificationEl.content;
                    if (versionEl) meta.version = versionEl.content;
                    
                    return meta;
                }
            """)
            
            # Update config with HTML metadata if not already set
            if html_metadata.get('author') and not config.author:
                config.author = html_metadata['author']
            if html_metadata.get('organization') and not config.organization:
                config.organization = html_metadata['organization']
            if html_metadata.get('date') and not config.date:
                config.date = html_metadata['date']
            if html_metadata.get('type') and not config.type:
                config.type = html_metadata['type']
            if html_metadata.get('classification') and not config.classification:
                config.classification = html_metadata['classification']
            if html_metadata.get('version') and not config.version:
                config.version = html_metadata['version']
            if not config.title:
                # Use title from HTML if not set
                title_from_html = await page.evaluate("() => document.title")
                if title_from_html:
                    config.title = title_from_html
            
            # Wait for resources to fully load before analysis
            await page.wait_for_load_state('networkidle')
            await page.evaluate("document.fonts.ready")
            
            # Wait for SVG elements to render
            try:
                await page.wait_for_selector('svg, img[src$=".svg"]', timeout=5000, state='visible')
            except Exception:
                pass  # Continue if no SVGs found
            
            # Additional buffer for layout stabilization
            await page.wait_for_timeout(1000)
            
            # Phase 2: Inject fonts, CSS, and decorators FIRST
            # This ensures cover page and TOC exist before we analyze layout
            # IMPORTANT: Inject profile CSS BEFORE Google Fonts so profile font stack takes precedence
            if config.css_file:
                await inject_custom_css(page, str(config.css_file), verbose=config.verbose)
            
            # Inject Google Fonts AFTER profile CSS (fonts are additive, not overriding)
            # Only inject if fonts are explicitly requested or if no profile CSS is present
            if config.font_families or not config.css_file:
                await inject_fonts(page, font_families=config.font_families, verbose=config.verbose)
            
            # Inject pagination CSS last (needed for proper page break detection)
            await inject_pagination_css(page, verbose=config.verbose)
            
            # Debug: Show loaded CSS in verbose mode
            if config.verbose:
                loaded_styles = await page.evaluate("""
                    () => {
                        return Array.from(document.styleSheets).map(sheet => {
                            try {
                                return {
                                    href: sheet.href || 'inline',
                                    rules: sheet.cssRules ? sheet.cssRules.length : 0,
                                    disabled: sheet.disabled
                                };
                            } catch (e) {
                                // CORS-protected stylesheets can't be read
                                return {
                                    href: sheet.href || 'inline',
                                    rules: 'protected',
                                    disabled: sheet.disabled
                                };
                            }
                        });
                    }
                """)
                print(f"{INFO} CSS Loading Order ({len(loaded_styles)} stylesheets):")
                for i, style in enumerate(loaded_styles, 1):
                    status = "disabled" if style.get('disabled') else "active"
                    print(f"{INFO}   {i}. {style['href']} ({style['rules']} rules, {status})")
            
            # Remove Pandoc's TOC if we're generating our own
            if config.generate_toc:
                await page.evaluate("""
                    () => {
                        const pandocToc = document.querySelector('nav#TOC, div#TOC');
                        if (pandocToc) {
                            pandocToc.remove();
                        }
                    }
                """)
            
            # Extract margins from profile CSS file BEFORE cover/TOC injection
            # These margins are needed for full-bleed elements like cover page
            margin_config = None
            if config.css_file:
                margin_config = extract_margins_from_css(config.css_file)
                if margin_config and config.verbose:
                    print(f"{INFO} Using margins from CSS: {margin_config}")
            
            if margin_config is None:
                margin_config = DEFAULT_MARGINS.copy()
                if config.verbose:
                    print(f"{INFO} Using default margins: {margin_config}")
            
            # Generate cover page if requested (inserts at beginning)
            # Pass margin_config so cover page can use correct negative margins
            if config.generate_cover:
                await inject_cover_page(page, config.cover, verbose=config.verbose, margin_config=margin_config)
            
            # Generate TOC if requested (inserts after cover page)
            if config.generate_toc:
                await inject_toc(page, verbose=config.verbose)
            
            # Wait for cover/TOC to be fully rendered
            await page.wait_for_timeout(500)
            
            # Phase 2.5: Measure actual page dimensions BEFORE analysis
            # Build header/footer templates to measure their actual heights
            
            # Detect dark mode using shared utility
            profile_name = getattr(config, 'profile', None)
            is_dark_mode = detect_dark_mode(profile_name, config.css_file)
            
            header_html, footer_html = build_header_footer(
                title=config.title,
                organization=config.organization,
                author=config.author,
                date=config.date,
                dark_mode=is_dark_mode
            )
            
            # Measure actual page dimensions (header/footer heights, margins, etc.)
            page_measurements = await measure_page_dimensions(
                page,
                header_html,
                footer_html,
                margin_config,
                page_format=config.page_format,
                verbose=config.verbose
            )
            
            # Phase 3: Analyze layout AFTER cover/TOC injection
            # This ensures measurements account for page breaks from cover/TOC
            # Pass actual measurements to analysis (no hardcoding)
            analysis = await analyze_layout(page, page_measurements=page_measurements, verbose=config.verbose)
            
            # Phase 4: Compute scaling decisions and apply them
            decisions = compute_scaling(analysis)
            if decisions:
                await apply_scaling(page, decisions, verbose=config.verbose)
                await page.wait_for_timeout(300)  # Wait for resize to take effect
            
            # Add watermark if requested
            if config.watermark:
                await add_watermark(page, config.watermark, verbose=config.verbose)
            
            # Wait for fonts, images, and async content to load
            await page.wait_for_timeout(1000)
            
            # Post-scaling sanity pass: re-analyze after scaling is applied
            # Scaling changes diagram sizes, which can affect layout
            # Only re-scale if new problems are detected
            post_scaling_analysis = await analyze_layout(page, verbose=False)
            if post_scaling_analysis.diagram_blocks:
                # Check if any diagrams still need adjustment
                post_scaling_decisions = compute_scaling(post_scaling_analysis)
                if post_scaling_decisions:
                    # Only apply if there are NEW problems (diagrams that weren't scaled before)
                    # or if scaling made things worse
                    heading_ids = [d.heading_id for d in post_scaling_decisions]
                    already_scaled = await page.evaluate("""
                        (headingIds) => {
                            const scaled = [];
                            headingIds.forEach(headingId => {
                                const heading = document.getElementById(headingId);
                                if (!heading) {
                                    scaled.push(headingId);
                                    return;
                                }
                                let next = heading.nextElementSibling;
                                for (let i = 0; i < 10 && next; i++) {
                                    const svg = next.querySelector('svg[data-scaled]');
                                    const img = next.querySelector('img[data-scaled]');
                                    if (svg || img) {
                                        scaled.push(headingId);
                                        return;
                                    }
                                    if (/^H[1-6]$/.test(next.tagName)) break;
                                    next = next.nextElementSibling;
                                }
                            });
                            return scaled;
                        }
                    """, heading_ids)
                    
                    # Filter out already-scaled diagrams (they were handled in first pass)
                    new_decisions = [
                        d for d in post_scaling_decisions
                        if d.heading_id not in already_scaled
                    ]
                    if new_decisions:
                        if config.verbose:
                            print(f"{INFO} Post-scaling analysis found {len(new_decisions)} additional diagrams needing adjustment")
                        await apply_scaling(page, new_decisions, verbose=config.verbose)
                        await page.wait_for_timeout(300)
            
            # Phase 5: Extract headings for bookmarks BEFORE generating PDF
            headings = await extract_headings_from_page(page)
            
            # Header/footer templates already built during measurement phase - reuse them
            # margin_config also already defined
            
            # Phase 6: Render PDF with measured margins and page format
            success = await render_pdf(
                page,
                str(config.pdf_file),
                header_html,
                footer_html,
                margin_config=margin_config,
                page_format=config.page_format,
                verbose=config.verbose
            )
            
            if not success:
                return False
        
        # Phase 7: Post-process PDF (outside browser context)
        if headings:
            add_bookmarks_to_pdf(str(config.pdf_file), headings, verbose=config.verbose)
        
        if config.metadata:
            embed_metadata(
                str(config.pdf_file),
                title=config.metadata.title,
                author=config.metadata.author,
                subject=config.metadata.subject,
                keywords=config.metadata.keywords,
                verbose=config.verbose
            )
        
        return True
        
    except Exception as e:
        print(f"{ERR} PDF generation failed: {e}")
        if config.verbose:
            import traceback
            traceback.print_exc()
        return False

