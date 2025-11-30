# Diagram Scaling Analysis: "Architecture Overview (Phase 0)"

## 🎯 Quick Summary

**Current Status:** ✅ **Automatically scaled and optimized**

- **Original height:** 829px
- **Available space:** 792px
- **Overflow:** 5% (1.05x ratio)
- **Scale applied:** 0.95x (95% - minimal scaling)
- **Final height:** ~788px
- **Page break:** ✅ Forces break after diagram (prevents collision with next heading)

**What happens:**
1. System detects diagram is 5% too tall
2. Scales down by 5% to fit with heading
3. Adds 48pt bottom margin for spacing
4. Forces page break after (diagram still >70% of page height)
5. Next heading gets 60pt top margin to prevent collision

---

## Target Diagram

**Location:** `docs/architecture-proposal.md` (lines 197-259)  
**Heading:** `### Architecture Overview (Phase 0)` (h3, line 195)  
**Diagram Type:** Mermaid flowchart with 5 subgraphs (External Systems, Portal Layer, Reporting Manager, Execution Layer, Data Layer)

---

## How the Scaling System Works

### Step 1: Detection (`analyze_heading_diagram_pairs`)

**When:** After HTML loads, before CSS injection (to get accurate measurements)

**What it does:**
1. **Finds the heading:** Searches for `h2, h3` elements
   - Your diagram follows an `h3` heading: `### Architecture Overview (Phase 0)`
   
2. **Locates the diagram:** Searches next 5 siblings for:
   - Direct `<svg>` elements (inline SVG)
   - `<img src="*.svg">` elements (Pandoc-wrapped SVG)
   - Stops if it hits another heading (`h1-h6`)

3. **Measures dimensions:**
   ```javascript
   const pageHeight = 10 * 96;           // 960px (A4 height)
   const marginTop = 0.75 * 96;          // 72px
   const marginBottom = 1 * 96;          // 96px
   const availableHeight = 792px;        // ~8.25 inches usable space
   
   const headingHeight = heading.offsetHeight;        // ~30-40px for h3
   const diagramHeight = diagram.getBoundingClientRect().height;  // Actual SVG height
   const totalHeight = headingHeight + diagramHeight + 48;  // 48px buffer
   ```

4. **Detects overflow:**
   - If `totalHeight > availableHeight` → **Problem detected!**
   - Creates a problem pair with:
     - `headingId`: Unique ID for the heading
     - `headingText`: First 50 chars of heading text
     - `headingHeight`: Height in pixels
     - `diagramHeight`: Height in pixels
     - `totalHeight`: Combined height + buffer
     - `availableHeight`: Available page space
     - `overflowRatio`: `totalHeight / availableHeight` (e.g., 1.2x = 20% overflow)
     - `diagramType`: `'svg'` or `'img'`
     - `diagramSrc`: Source path or 'inline-svg'

**For your diagram (ACTUAL MEASUREMENTS):**
- Heading: `h3` → "Architecture Overview (Phase 0)"
- Diagram: Mermaid SVG (rendered by `mermaid-cli` before PDF generation)
- **Actual height:** 829px
- **Available height:** 792px
- **Overflow ratio:** 1.05x (5% overflow)
- **Status:** ✅ **DETECTED AND SCALED**

---

### Step 2: Scaling Calculation (`apply_adaptive_diagram_sizing`)

**When:** Immediately after detection, if problems found

**Scale Factor Formula:**
```python
available_for_diagram = availableHeight - headingHeight - 48  # 48px buffer
current_diagram_height = diagramHeight
scale_factor = available_for_diagram / current_diagram_height
```

**Constraints:**
- **Minimum scale:** 50% (0.5x) - Never scales below this (becomes unreadable)
- **Maximum scale:** 100% (1.0x) - Never scales up, only down
- **Example:** If diagram is 1000px tall and available space is 750px:
  - `scale_factor = 750 / 1000 = 0.75` (75% scale)

**Force Page Break Logic:**
```python
final_height = current_diagram_height * scale_factor
page_threshold = 0.7 * availableHeight  # 70% of page (~554px)
force_break = final_height > page_threshold
```
- If scaled diagram is still >70% of page height → Forces page break after diagram

---

### Step 3: Apply Scaling (JavaScript in Browser)

**For SVG elements:**
```javascript
// Set explicit width/height attributes
diagram.setAttribute('width', newWidth);
diagram.setAttribute('height', newHeight);

// Preserve aspect ratio with viewBox
if (!diagram.hasAttribute('viewBox')) {
    diagram.setAttribute('viewBox', `0 0 ${currentWidth} ${currentHeight}`);
}
```

**For IMG elements (Pandoc-wrapped):**
```javascript
// Use inline styles (overrides CSS)
diagram.style.width = `${newWidth}px`;
diagram.style.height = `${newHeight}px`;
diagram.style.maxWidth = 'none';
diagram.style.maxHeight = 'none';
```

**Marking:**
```javascript
// Add data attribute for CSS targeting
diagram.setAttribute('data-scaled', scaleFactor.toFixed(2));  // e.g., "0.75"

// Force page break if very large
if (forceBreak) {
    diagram.setAttribute('data-force-break-after', 'true');
}

// Add extra spacing to container
if (diagram.parentElement) {
    diagram.parentElement.style.maxHeight = `${newHeight}px`;
    diagram.parentElement.style.marginBottom = '48pt';  // Extra spacing
}
```

---

### Step 4: CSS Protection (`inject_adaptive_pagination_css`)

**Critical CSS Rules:**

1. **Scaled diagrams get special spacing:**
   ```css
   [data-scaled] {
       page-break-before: avoid !important;
       margin-top: 16pt !important;
       margin-bottom: 48pt !important;  /* Large bottom margin */
       page-break-after: auto !important;
   }
   ```

2. **Prevent heading collision:**
   ```css
   figure + h1, figure + h2, figure + h3,
   [data-scaled] + h1, [data-scaled] + h2, [data-scaled] + h3,
   svg + h1, svg + h2, svg + h3 {
       margin-top: 60pt !important;  /* Extra large margin */
       page-break-before: auto !important;
   }
   ```

3. **Force page break for very large diagrams:**
   ```css
   [data-force-break-after] ~ h1,
   [data-force-break-after] ~ h2 {
       page-break-before: always !important;
   }
   ```

---

## Factors That Affect Scaling

### 1. **Diagram Complexity**
- **More nodes/subgraphs** → Taller diagram → More likely to scale
- Your diagram has 5 subgraphs with ~15 nodes → Likely tall

### 2. **Mermaid Theme Settings**
- **Font size:** `fontSize: '12px'` (line 198) → Smaller text = more compact
- **Node spacing:** Default Mermaid spacing → Can be adjusted
- **Subgraph padding:** Default → Can be adjusted

### 3. **Page Margins**
- **Current:** `0.75in top, 1in bottom` → ~792px available height
- **If you reduce margins:** More space → Less scaling needed

### 4. **Heading Height**
- **h3 height:** ~30-40px (depends on font size)
- **Nested headings:** If h3 is followed by another heading before diagram, both heights are counted

### 5. **Mermaid Rendering**
- **Pre-rendering:** Diagram is rendered to SVG by `mermaid-cli` before PDF generation
- **SVG dimensions:** Determined by Mermaid's layout algorithm
- **ViewBox:** Preserved during scaling to maintain aspect ratio

---

## How to Adjust Scaling for This Diagram

### Option 1: Modify Mermaid Diagram Settings

**Current (line 198):**
```markdown
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'12px'}}}%%
```

**Make it more compact:**
```markdown
%%{init: {'theme':'base', 'themeVariables': {'fontSize':'11px'}, 'flowchart': {'nodeSpacing': 40, 'rankSpacing': 50}}}%%
```
- Smaller font → More compact
- Reduced spacing → Less vertical space

### Option 2: Adjust Scale Factor Constraints

**In `pdf_playwright.py` line 174:**
```python
# Current: Don't scale below 50%
scale_factor = max(scale_factor, 0.5)

# Allow smaller scale (e.g., 40% minimum):
scale_factor = max(scale_factor, 0.4)
```

### Option 3: Adjust Available Height Calculation

**In `pdf_playwright.py` line 165:**
```python
# Current: 48px buffer
available_for_diagram = pair['availableHeight'] - pair['headingHeight'] - 48

# Reduce buffer (more aggressive scaling):
available_for_diagram = pair['availableHeight'] - pair['headingHeight'] - 32
```

### Option 4: Adjust Force Break Threshold

**In `pdf_playwright.py` line 178:**
```python
# Current: 70% of page height
page_threshold = 0.7 * pair['availableHeight']

# More aggressive (force break at 60%):
page_threshold = 0.6 * pair['availableHeight']
```

### Option 5: Manual CSS Override

**Add to `custom.css.playwright`:**
```css
/* Target this specific diagram by heading ID */
#heading-architecture-overview-phase-0 + figure svg,
#heading-architecture-overview-phase-0 + figure img[src$=".svg"] {
    max-height: 600px !important;  /* Force max height */
    transform: scale(0.85);         /* Manual scale */
    transform-origin: top center;
}
```

---

## Debugging: See What's Happening

**Enable verbose mode:**
```bash
python pdf-tools/md2pdf.py \
  docs/architecture-proposal.md \
  output.pdf \
  --renderer playwright \
  --verbose
```

**Actual output (from verbose run):**
```
[WARN] Found 2 heading+diagram pairs needing adjustment:
  - 'Architecture Overview (Phase 0)': 829px (available: 792px, ratio: 1.05x, type: img)
  - 'Failure Detection and Recovery': 838px (available: 792px, ratio: 1.06x, type: img)
[INFO] Scaling img under 'Architecture Overview (Phase 0)' by 0.95x
[INFO] Large diagram under 'Architecture Overview (Phase 0)' will force page break after
```

**Analysis:**
- **Scale factor:** 0.95x (95% scale) - Very minimal scaling needed
- **Final height:** ~788px (829px × 0.95)
- **Force break:** ✅ Yes (788px > 554px threshold = 70% of 792px)
- **Result:** Diagram fits with heading, but forces page break after to prevent collision

**Check in browser DevTools (if debugging HTML):**
```javascript
// Find the diagram
const heading = document.querySelector('h3:contains("Architecture Overview")');
const diagram = heading.nextElementSibling.querySelector('svg');

// Check scaling
console.log('Scale factor:', diagram.getAttribute('data-scaled'));
console.log('Force break:', diagram.hasAttribute('data-force-break-after'));
console.log('Dimensions:', diagram.getBoundingClientRect());
```

---

## Summary: Moving Parts

1. **Detection:** `analyze_heading_diagram_pairs()` finds h3 + diagram, measures heights
2. **Calculation:** `apply_adaptive_diagram_sizing()` computes scale factor (50-100%)
3. **Application:** JavaScript sets SVG `width`/`height` attributes or IMG inline styles
4. **Marking:** Adds `data-scaled` attribute with scale factor
5. **Protection:** CSS rules prevent collision with next heading
6. **Force Break:** If still >70% of page, forces page break after diagram

**Key Files:**
- `pdf-tools/pdf_playwright.py`: Lines 55-257 (detection + scaling logic)
- `pdf-tools/custom.css.playwright`: Lines 375-394 (CSS rules for scaled diagrams)
- `pdf-tools/pdf_playwright.py`: Lines 453-520 (adaptive pagination CSS)

**To modify:** Adjust scale factor constraints, buffer sizes, or Mermaid theme settings.

