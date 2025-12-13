# Mermaid Color Mapping Fix

## Problem Identified

Your Mermaid diagrams were not using theme colors because of a **pipeline ordering issue** - colors were being mapped but the step was missing from the execution flow.

### What Was Happening:

1. ✅ Design tokens defined custom Mermaid variables in `design-tokens.yml` (e.g., `--mermaid-stream-fill`)
2. ✅ CSS generator created CSS variables from those tokens  
3. ✅ CSS was injected into the Playwright page
4. ❌ **MISSING STEP**: JavaScript never ran to read CSS variables and update the Mermaid SVG diagrams
5. ✅ Diagrams rendered with placeholder colors from Mermaid-CLI

### Root Cause:

The Mermaid diagram rendering happens in **two stages**:

**Stage 1: Markdown → HTML (Pre-Playwright)**
- Mermaid-CLI renders diagrams to SVG with hardcoded colors
- Uses design-tokens to set placeholder colors  
- SVGs embedded in HTML with `<style>` tags containing `.classname { fill: #color1; stroke: #color2; }`

**Stage 2: HTML → PDF (Playwright)**
- Profile CSS injected (contains `--mermaid-config-fill`, etc. CSS variables)
- **MISSING**: No code to read CSS variables and update SVG `<style>` elements
- Diagrams render with original Mermaid-CLI placeholder colors, not theme colors

## Solution Implemented

### 1. Created `mermaid_colors.py` Decorator

New file: `tools/pdf/playwright_pdf/decorators/mermaid_colors.py`

Implements `apply_mermaid_colors()` function that:
- Reads CSS variables from the page's `:root` element
- Finds all SVG diagrams' `<style>` tags
- Parses classDef rules (`.config`, `.core`, `.stream`, etc.)
- Replaces placeholder hex colors with CSS variable values

**Key JavaScript logic:**
```javascript
const getVar = (varName) => {
    return getComputedStyle(document.documentElement)
        .getPropertyValue(varName).trim();
};

// For each class (config, core, stream, ...)
const fillColor = getVar('--mermaid-config-fill');
const strokeColor = getVar('--mermaid-config-stroke');

// Update SVG style: replace #xxx colors with CSS variables
styleContent.replace(/fill\s*:\s*#[0-9a-fA-F]{6}/gi, `fill: ${fillColor}`);
```

### 2. Updated Pipeline Order in `pipeline.py`

**Critical: Apply Mermaid colors AFTER CSS injection, BEFORE pagination CSS**

**Correct Pipeline Order:**
```python
# Phase 2: Inject CSS
1. Inject profile CSS (contains --mermaid-* variables)
2. Inject Google Fonts
3. ✨ Apply Mermaid colors (READ CSS variables, update SVGs)
4. Inject pagination CSS

# Phase 3: Layout decorators
5. Remove Pandoc TOC
6. Extract margins
7. Inject cover page
8. Inject TOC
9. Measure page dimensions
10. Analyze layout
# ... rest of pipeline
```

### 3. Import in Pipeline

```python
from .decorators.mermaid_colors import apply_mermaid_colors

# In generate_pdf():
await apply_mermaid_colors(page, verbose=config.verbose)
```

## Why This Works

### Ordering is Critical:

1. **Profile CSS injected first** → CSS variables available
   - ✅ `getComputedStyle(document.documentElement)` can read `--mermaid-config-fill`
   - ✅ CSS variables are now in the DOM's cascade

2. **Mermaid colors applied second** → JavaScript reads variables
   - ✅ SVG `<style>` tags are mutated
   - ✅ Colors change from `#164e63` → computed CSS variable value
   - ✅ Mermaid SVGs now match theme

3. **Pagination CSS injected last** → No conflicts
   - ✅ Won't interfere with Mermaid color replacement
   - ✅ Page break rules unaffected

### Color Mapping:

For each class (config, core, stream, storage, output, topic, highlight):

```yaml
# From design-tokens.yml:
mermaid:
  config_fill: "#164e63"      # dark-pro theme
  config_stroke: "#06b6d4"
  core_fill: "#0f172a"
  core_stroke: "#60a5fa"
  # ... 5 more classes

# CSS generator creates:
--mermaid-config-fill: #164e63;
--mermaid-config-stroke: #06b6d4;
--mermaid-core-fill: #0f172a;
--mermaid-core-stroke: #60a5fa;

# Mermaid color decorator reads these and updates SVG styles:
.config1 { fill: #164e63; stroke: #06b6d4; }
.core1 { fill: #0f172a; stroke: #60a5fa; }
```

## Testing

### 1. Verify CSS Variables are Generated

```bash
cd tools/pdf/config
python build_themes.py
# Check: tools/pdf/styles/generated/dark-pro.css
grep "--mermaid-" dark-pro.css
```

Expected output:
```css
--mermaid-config-fill: #164e63;
--mermaid-config-stroke: #06b6d4;
--mermaid-core-fill: #0f172a;
--mermaid-core-stroke: #60a5fa;
# ... 12 more variables
```

### 2. Rebuild Docker Image

```bash
docker build -t docs-pipeline:latest .
docker run --rm \  
  -v $(pwd)/docs/examples/streaming-architecture-spec.md:/app/input.md:ro \
  -v $(pwd)/output:/app/output:rw \
  docs-pipeline:latest \
  python -m tools.pdf.cli.main /app/input.md /app/output/streaming.pdf \
    --profile dark-pro --cover --toc --verbose
```

### 3. Check Generated PDF

Open the PDF and verify:
- ✅ "Stream Source" node has dark slate fill (#1e293b) not light green (#d1fae5)
- ✅ All diagram nodes use theme colors
- ✅ Colors match dark-pro theme specification
- ✅ Verbose output shows: `[INFO] Applied Mermaid classDef colors from CSS variables`

## Commits

1. **Create decorator:** `tools/pdf/playwright_pdf/decorators/mermaid_colors.py`
   - Implements `apply_mermaid_colors()` function
   - Reads CSS variables and updates SVG styles

2. **Update pipeline:** `tools/pdf/playwright_pdf/pipeline.py`
   - Import `apply_mermaid_colors`
   - Call after `inject_custom_css()`, before `inject_pagination_css()`
   - Added verbose output and WARN colorama import

## Future: Even Better Solution

**Current approach:** JavaScript mutation of inline SVG styles

**Future improvement:** Render with CSS variables directly
- Modify Mermaid-CLI theme config to use CSS variables
- Or: Pre-process SVG to use CSS custom properties
- Would be cleaner but requires coordination with diagram rendering stage

## Debugging

If colors still don't match:

1. **Check CSS variables are generated:**
   ```bash
   grep "--mermaid" tools/pdf/styles/generated/dark-pro.css
   ```

2. **Check CSS is injected:**
   - Add breakpoint in Playwright
   - Run: `getComputedStyle(document.documentElement).getPropertyValue('--mermaid-config-fill')`
   - Should return color value like `#164e63`

3. **Check decorator runs:**
   - Look for: `[INFO] Applied Mermaid classDef colors from CSS variables`
   - If missing, function didn't execute

4. **Check SVG style mutations:**
   - Inspect SVG source before/after
   - Before: `.config { fill: #d1fae5; stroke: #10b981; }`
   - After: `.config { fill: #164e63; stroke: #06b6d4; }`

## Architecture Impact

- ✅ No breaking changes
- ✅ Backward compatible
- ✅ Isolated in decorators module
- ✅ Follows existing patterns (other decorators)
- ✅ Works with all themes (uses CSS variables)

## Files Modified

- `tools/pdf/playwright_pdf/decorators/mermaid_colors.py` (NEW)
- `tools/pdf/playwright_pdf/pipeline.py` (UPDATED)
