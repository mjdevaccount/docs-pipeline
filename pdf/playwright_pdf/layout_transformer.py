"""
Layout Transformer - Scaling Decisions & DOM Mutations
=======================================================
Pure Python scaling algorithm + DOM mutation actuator.
Separates decision-making from DOM manipulation.
"""
from dataclasses import dataclass
from typing import List, Optional
from playwright.async_api import Page
from .layout_model import DiagramBlock, LayoutAnalysis

try:
    from colorama import Fore, Style, init as colorama_init
    colorama_init(autoreset=True)
    INFO = f"{Fore.CYAN}[INFO]{Style.RESET_ALL}"
    WARN = f"{Fore.YELLOW}[WARN]{Style.RESET_ALL}"
except ImportError:
    INFO = "[INFO]"
    WARN = "[WARN]"


@dataclass
class ScalingDecision:
    """Decision about how to scale a diagram block"""
    heading_id: str
    scale_factor: float
    scale_entire_block: bool
    force_pre_break: bool
    force_post_break: bool


@dataclass
class LayoutPolicy:
    """
    Tunable layout policy for scaling and page-break behavior.

    This captures the "rules" so we can adjust behavior per document
    type or brand without rewriting the algorithm.
    """

    # Reserved vertical space below each diagram block for the next heading, etc.
    next_heading_space: float = 100.0
    # Buffer around diagrams to avoid visual crowding.
    small_buffer: float = 48.0
    large_buffer: float = 100.0

    # Threshold for deciding when to scale entire block vs diagram-only.
    intermediate_ratio: float = 0.15
    intermediate_px_cap: float = 100.0

    # Minimum scale factors.
    min_scale_block: float = 0.25
    min_scale_diagram_moderate: float = 0.40
    min_scale_diagram_large: float = 0.20
    min_scale_diagram_extreme: float = 0.12

    # Overflow severity thresholds.
    severe_overflow_ratio: float = 2.5
    large_overflow_ratio: float = 2.0

    # When deciding if we still overflow badly enough to force a page break.
    post_break_overflow_factor: float = 1.10

    # Extra headroom to subtract when recomputing conservative scale.
    safety_margin_px: float = 16.0


def compute_scaling(
    analysis: LayoutAnalysis,
    policy: Optional[LayoutPolicy] = None,
) -> List[ScalingDecision]:
    """
    Pure Python function that computes scaling decisions from layout analysis.
    
    This is unit-testable without Playwright or DOM.
    Returns a list of ScalingDecision objects that can be applied to the DOM.
    """
    decisions: List[ScalingDecision] = []
    if policy is None:
        policy = LayoutPolicy()
    
    for block in analysis.diagram_blocks:
        # Calculate total diagram height including container
        current_diagram_height = (
            block.diagram_height
            + block.container_margins
            + block.container_padding
            + block.container_borders
        )
        
        # Calculate non-diagram content height
        non_diagram_height = max(block.total_content_height - current_diagram_height, 0)
        
        # Available space with safety buffer.
        # CRITICAL: Must leave enough space to prevent overlapping with next heading.
        next_heading_space = policy.next_heading_space
        buffer = (
            policy.large_buffer
            if block.overflow_ratio > policy.large_overflow_ratio
            else policy.small_buffer
        )
        # Total reserved space: buffer + next heading.
        total_reserved = buffer + next_heading_space
        # CRITICAL: Subtract total_reserved from available to ensure we actually leave that space
        available = block.available_height - total_reserved
        
        # Intermediate elements height
        intermediate_height = block.elements_between_height
        
        # Total content height
        total = block.total_content_height
        
        # Check if this block has a parent heading (H2 above H3)
        # If so, we should consider that in the "scale entire block" decision
        breakdown = getattr(block, "measurement_breakdown", None) or {}
        parent_heading_height = (
            breakdown.get("parentHeadingHeight", 0) +
            breakdown.get("parentHeadingMargins", 0) +
            breakdown.get("parentHeadingBorders", 0)
        )
        
        # Decide: scale entire block vs just diagram.
        # If intermediate content OR parent heading is significant, scale entire block.
        intermediate_threshold = min(
            policy.intermediate_px_cap,
            block.available_height * policy.intermediate_ratio,
        )
        
        # Consider both intermediate content AND parent heading when deciding
        significant_non_diagram_content = (
            intermediate_height + parent_heading_height
        ) > intermediate_threshold
        
        should_scale_entire_block = (
            significant_non_diagram_content
            and total > available
        )
        
        if should_scale_entire_block:
            # Scale entire block proportionally
            block_scale = max((available) / total, policy.min_scale_block)
            final_total_height = total * block_scale + 48
            
            # If still too tall, reduce further
            if final_total_height > block.available_height:
                block_scale = max(
                    (block.available_height - policy.small_buffer) / total,
                    policy.min_scale_block,
                )
            
            scale_factor = block_scale
            scale_entire_block = True
        else:
            # Scale only the diagram
            available_for_diagram = available - non_diagram_height
            
            if available_for_diagram <= 0:
                # If calculation goes negative, use a more intelligent fallback
                # Try to fit diagram into available space, accounting for non-diagram content
                if current_diagram_height > 0:
                    # Scale based on what fits, but be more aggressive
                    scale_factor = max(available / current_diagram_height, 0.3)
                else:
                    scale_factor = 0.5  # Fallback
            else:
                scale_factor = available_for_diagram / current_diagram_height
            
            scale_entire_block = False
        
        # Don't scale up, only down
        if scale_factor >= 1.0:
            continue
        
        # Minimum scale limits - be more flexible for very large diagrams
        # If overflow is severe, allow more aggressive scaling.
        overflow_ratio = block.overflow_ratio

        if not scale_entire_block:
            # For diagram-only scaling, minimum depends on overflow severity.
            if overflow_ratio > policy.severe_overflow_ratio:
                # Very large overflow - allow down to extreme minimum if needed.
                if scale_factor < policy.min_scale_diagram_extreme:
                    scale_factor = policy.min_scale_diagram_extreme
            elif overflow_ratio > policy.large_overflow_ratio:
                # Large overflow - allow down to "large" minimum unless calculation is already lower.
                if scale_factor < 0.15:
                    scale_factor = policy.min_scale_diagram_large
            else:
                # Moderate overflow - standard minimum.
                scale_factor = max(scale_factor, policy.min_scale_diagram_moderate)
        else:
            # For entire block scaling, keep block minimum.
            scale_factor = max(scale_factor, policy.min_scale_block)
        
        # Calculate final dimensions
        final_diagram_height = current_diagram_height * scale_factor
        
        # Ensure the final scaled block actually fits within reserved space.
        # Recompute conservatively if needed to avoid any clipping at the bottom.
        if scale_entire_block:
            target_height = block.available_height
            final_total_height = total * scale_factor + buffer
            if final_total_height > target_height:
                # Shrink just enough to fit within the available height minus a small safety margin.
                safe_target = max(target_height - policy.safety_margin_px, 50)
                scale_factor = max(safe_target / (total + 1e-6), policy.min_scale_block)
                final_total_height = total * scale_factor + buffer
            needs_pre_break = False
        else:
            target_height = block.available_height - total_reserved
            final_total_height = non_diagram_height + final_diagram_height
            if final_total_height > target_height:
                safe_target = max(target_height - policy.safety_margin_px, 50)
                # Only scale further down if the diagram is actually taller than the safe space.
                if current_diagram_height > 0:
                    extra_scale = safe_target / (non_diagram_height + current_diagram_height + 1e-6)
                    scale_factor = min(scale_factor, extra_scale)
                    final_diagram_height = current_diagram_height * scale_factor
                    final_total_height = non_diagram_height + final_diagram_height
            needs_pre_break = final_total_height > target_height
        
        # Force post-break ONLY if scaled content still overflows badly.
        force_post_break = False
        if final_total_height > target_height * policy.post_break_overflow_factor:
            force_post_break = True

        # Record final computed values on the block for downstream diagnostics/tests.
        try:
            breakdown = getattr(block, "measurement_breakdown", None)
            if isinstance(breakdown, dict):
                breakdown["finalScaleFactor"] = scale_factor
                breakdown["finalTotalHeight"] = final_total_height
                breakdown["targetHeight"] = target_height
                breakdown["scaleEntireBlock"] = scale_entire_block
                breakdown["needsPreBreak"] = needs_pre_break
                breakdown["forcePostBreak"] = force_post_break
        except Exception:
            # Never let diagnostics break the main algorithm.
            pass

        decisions.append(
            ScalingDecision(
                heading_id=block.heading_id,
                scale_factor=scale_factor,
                scale_entire_block=scale_entire_block,
                force_pre_break=needs_pre_break,
                force_post_break=force_post_break
            )
        )
    
    return decisions


async def apply_scaling(page: Page, decisions: List[ScalingDecision], verbose: bool = False) -> None:
    """
    Apply scaling decisions to the DOM.
    
    This JS is "dumb" - it just applies the decisions passed from Python.
    No re-computation of scaling logic here.
    """
    if not decisions:
        return
    
    try:
        # Convert decisions to JSON-serializable format
        payload = [
            {
                'heading_id': d.heading_id,
                'scale_factor': d.scale_factor,
                'scale_entire_block': d.scale_entire_block,
                'force_pre_break': d.force_pre_break,
                'force_post_break': d.force_post_break
            }
            for d in decisions
        ]
        
        await page.evaluate("""
            (decisions) => {
                decisions.forEach(cfg => {
                    const heading = document.getElementById(cfg.heading_id);
                    if (!heading) return;

                    // Find diagram (same logic as analysis)
                    let next = heading.nextElementSibling;
                    let diagram = null;
                    
                    for (let i = 0; i < 10 && next && !diagram; i++) {
                        const svg = next.querySelector('svg');
                        const img = next.querySelector('img[src$=".svg"]');
                        
                        if (svg) diagram = svg;
                        else if (img) diagram = img;
                        
                        if (/^H[1-6]$/.test(next.tagName)) break;
                        next = next.nextElementSibling;
                    }

                    if (!diagram) return;

                    const container = diagram.parentElement || diagram;

                    // Ensure heading + metadata + diagram stay as one unit
                    // If there is a higher-level heading immediately before this
                    // heading (e.g., H2 "Architectural Vision" followed by H3
                    // "Architecture Overview (Phase 0)"), pull that parent
                    // heading into the same block so the whole section moves
                    // together.
                    let parentHeading = null;
                    const prev = heading.previousElementSibling;
                    if (prev && /^H[1-6]$/.test(prev.tagName)) {
                        const currentLevel = parseInt(heading.tagName.substring(1), 10);
                        const prevLevel = parseInt(prev.tagName.substring(1), 10);
                        if (!Number.isNaN(prevLevel) && prevLevel < currentLevel) {
                            parentHeading = prev;
                        }
                    }

                    let block = heading.closest('.heading-diagram-block');
                    if (!block) {
                        block = document.createElement('div');
                        block.className = 'heading-diagram-block';
                        block.style.display = 'block';
                        block.style.width = '100%';
                        // Keep heading + diagram on the same page when it fits
                        block.style.setProperty('break-inside', 'avoid-page', 'important');
                        block.style.setProperty('page-break-inside', 'avoid', 'important');
                        block.style.setProperty('break-after', 'auto', 'important');
                        block.style.setProperty('page-break-after', 'auto', 'important');
                        if (parentHeading) {
                            // Mark that this block contains a parent+child heading group
                            // (page break decision will be made based on cfg.force_pre_break below)
                            block.setAttribute('data-parent-heading-group', 'true');
                        }
                        // Insert the block where the current heading was,
                        // then move the parent heading (if any) and this
                        // heading inside it. This ensures both headings and
                        // the diagram are treated as a single unit.
                        heading.before(block);
                        if (parentHeading && parentHeading.parentElement) {
                            block.appendChild(parentHeading);
                        }
                        block.appendChild(heading);
                    } else {
                        // If block already exists, re-assert non-splitting behaviour
                        block.style.setProperty('break-inside', 'avoid-page', 'important');
                        block.style.setProperty('page-break-inside', 'avoid', 'important');
                        block.style.setProperty('break-after', 'auto', 'important');
                        block.style.setProperty('page-break-after', 'auto', 'important');
                    }

                    const targetContainer = container || diagram;

                    // Move any metadata/paragraphs sitting between the heading and diagram
                    let cursor = block.nextElementSibling;
                    while (cursor && cursor !== targetContainer) {
                        const nextSibling = cursor.nextElementSibling;
                        block.appendChild(cursor);
                        cursor = nextSibling;
                    }

                    // Pull the diagram container into the wrapper
                    if (targetContainer && targetContainer.parentElement !== block) {
                        block.appendChild(targetContainer);
                    }

                    // Keep common captions with the block
                    const afterContainer = targetContainer ? targetContainer.nextElementSibling : null;
                    if (afterContainer && (afterContainer.tagName === 'FIGCAPTION' || afterContainer.classList.contains('diagram-caption'))) {
                        block.appendChild(afterContainer);
                    }

                    // Keep heading + diagram together (but allow content after)
                    // REMOVED: block.style.breakInside = 'avoid-page';
                    // REMOVED: block.style.pageBreakInside = 'avoid';
                    heading.style.breakAfter = 'avoid';
                    heading.style.pageBreakAfter = 'avoid';

                    if (cfg.force_pre_break) {
                        block.style.pageBreakBefore = 'always';
                        block.style.breakBefore = 'page';
                        block.setAttribute('data-force-break-before', 'true');
                    }

                    // Prevent splits between heading/container/diagram
                    container.style.breakInside = 'avoid-page';
                    container.style.pageBreakInside = 'avoid';
                    container.style.pageBreakAfter = cfg.force_post_break ? 'always' : 'auto';

                    // Get current dimensions
                    const rect = diagram.getBoundingClientRect();
                    const currentWidth = rect.width;
                    const currentHeight = rect.height;
                    
                    // Calculate new dimensions
                    const newWidth = currentWidth * cfg.scale_factor;
                    const newHeight = currentHeight * cfg.scale_factor;
                    
                    if (diagram.tagName.toLowerCase() === 'svg') {
                        // SVG: Set width/height attributes
                        diagram.setAttribute('width', newWidth);
                        diagram.setAttribute('height', newHeight);
                        
                        // Preserve aspect ratio with viewBox
                        if (!diagram.hasAttribute('viewBox')) {
                            diagram.setAttribute('viewBox', `0 0 ${currentWidth} ${currentHeight}`);
                        }
                    } else if (diagram.tagName.toLowerCase() === 'img') {
                        // IMG: Use inline style (overrides CSS)
                        diagram.style.width = `${newWidth}px`;
                        diagram.style.height = `${newHeight}px`;
                        diagram.style.maxWidth = 'none';
                        diagram.style.maxHeight = 'none';
                    }
                    
                    // Mark as scaled (for CSS targeting)
                    diagram.setAttribute('data-scaled', cfg.scale_factor.toFixed(2));
                    
                    // Update container with proper spacing
                    // CRITICAL: Use explicit height + padding to create actual space
                    // Chromium PDF respects explicit heights better than margins alone
                    const bottomSpacing = cfg.scale_factor < 0.35 ? 200 : 80;
                    
                    if (container && container !== diagram) {
                        // Set explicit max height to prevent overflow
                        container.style.maxHeight = `${newHeight}px`;
                        container.style.height = 'auto';
                        container.style.display = 'block';
                        container.style.overflow = 'visible';
                        
                        // CRITICAL: Use padding-bottom instead of margin for guaranteed space
                        // Chromium PDF respects padding better in print context
                        container.style.paddingBottom = `${bottomSpacing}px`;
                        container.style.marginBottom = '0';
                        
                        // Ensure no page break after container
                        container.style.setProperty('page-break-after', 'auto', 'important');
                        container.style.setProperty('break-after', 'auto', 'important');
                    }
                    
                    // Also set on diagram itself
                    diagram.style.marginBottom = '0';
                    diagram.style.paddingBottom = `${bottomSpacing}px`;
                    diagram.style.setProperty('page-break-after', 'auto', 'important');
                    diagram.style.setProperty('break-after', 'auto', 'important');
                    
                    // CRITICAL: Add a spacer div after the diagram to guarantee space
                    // This creates actual DOM space that Chromium must respect
                    const spacer = document.createElement('div');
                    spacer.style.height = `${bottomSpacing}px`;
                    spacer.style.minHeight = `${bottomSpacing}px`;
                    spacer.style.width = '100%';
                    spacer.style.display = 'block';
                    spacer.style.pageBreakInside = 'avoid';
                    spacer.style.breakInside = 'avoid';
                    spacer.setAttribute('data-diagram-spacer', 'true');
                    
                    // Insert spacer after the block (or container if no block)
                    const insertAfter = block || container;
                    if (insertAfter && insertAfter.parentElement) {
                        insertAfter.parentElement.insertBefore(spacer, insertAfter.nextSibling);
                    }
                    
                    // CRITICAL: Ensure the block itself doesn't force a break after
                    if (block) {
                        block.style.setProperty('page-break-after', 'auto', 'important');
                        block.style.setProperty('break-after', 'auto', 'important');
                    }
                    
                    // CRITICAL: Find the next h2 heading after this diagram and force it to NOT break
                    // This is the key fix - explicitly override any CSS that might force a break
                    let nextElement = block ? block.nextElementSibling : (container ? container.nextElementSibling : null);
                    let foundNextH2 = false;
                    let searchCount = 0;
                    
                    while (nextElement && searchCount < 20 && !foundNextH2) {
                        if (nextElement.tagName === 'H2') {
                            // Found the next h2 - explicitly allow it on same page
                            nextElement.style.setProperty('page-break-before', 'auto', 'important');
                            nextElement.style.setProperty('break-before', 'auto', 'important');
                            nextElement.style.setProperty('page-break-after', 'auto', 'important');
                            nextElement.style.setProperty('break-after', 'auto', 'important');
                            foundNextH2 = true;
                            break;
                        }
                        nextElement = nextElement.nextElementSibling;
                        searchCount++;
                    }
                    
                    // Force page break after if diagram is very tall
                    if (cfg.force_post_break) {
                        diagram.setAttribute('data-force-break-after', 'true');
                    }
                });
            }
        """, payload)
        
        if verbose:
            for d in decisions:
                print(f"{INFO} Scaling {d.heading_id}:")
                print(f"      [Scale] Scale factor: {d.scale_factor:.2f}x ({d.scale_factor*100:.0f}%)")
                print(f"      [Mode] {'Entire block' if d.scale_entire_block else 'Diagram only'}")
                if d.force_pre_break:
                    print(f"      [Break] Will start block on new page")
                if d.force_post_break:
                    print(f"      [Break] Will force page break after diagram")
                print()
                
    except Exception as e:
        if verbose:
            print(f"{WARN} Scaling application failed: {e}")

