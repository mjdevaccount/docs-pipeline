# 🎨 Mermaid Themes Analysis & Improvement Plan

**Date**: December 12, 2025, 4:53 PM CST  
**Status**: 🔍 ANALYSIS COMPLETE - IMPROVEMENTS IDENTIFIED  
**Current State**: Themes "kind of working" - needs refinement

---

## 📊 Current Implementation Status

### ✅ What's In Place

1. **80+ Mermaid CSS Variables** in `dark-pro.css`
   - Primary colors (6 variables)
   - Text styling (4 variables)
   - Borders & elements (5 variables)
   - Flowchart, sequence, state, class, ER, Gantt, pie, git (60+ variables)
   - ✅ All defined at `:root` level

2. **SVG Text Color Styling**
   - Explicit rules for SVG text elements
   - Mermaid-specific selectors (`.mermaid text`, `.mermaid tspan`)
   - Fallback rules for uncolored text
   - ✅ print-color-adjust: exact configured (4 locations)

3. **Mermaid 11 Enhancement Step** (`mermaid_enhancement_step.py`)
   - Removes old Mermaid initialization
   - Injects new Mermaid 11 script
   - Sets `theme: 'base'` to read CSS variables
   - ✅ Configured for Playwright rendering

### ⚠️ Issues & Gaps

1. **CSS Variables Not Actually Being Read by Mermaid**
   - Variables defined, but Mermaid 11 isn't reading them
   - Fallback: Using hardcoded colors in `themeVariables: {}`
   - **Root cause**: `theme: 'base'` requires Mermaid config to explicitly map CSS variables

2. **Text Contrast Issues**
   - SVG text styling works for PDFs
   - But Mermaid 11 still uses default theme colors
   - Light text on light background in some diagrams

3. **Diagram Type Inconsistencies**
   - Flowcharts: Partial color application
   - Sequence diagrams: Actor backgrounds not dark
   - State diagrams: Transition text sometimes unreadable
   - Gantt: Task text contrast issues

4. **HTML vs PDF Rendering**
   - HTML (browser): Uses Mermaid's default theme (partially working)
   - PDF (Playwright): Text colors corrected by CSS, but diagram fills still default

5. **Tool Version Compatibility**
   - Mermaid: `@11` via CDN (good version)
   - Node: `20.x` (current, good)
   - Pandoc: System version (outdated potentially)
   - Chromium: Via Playwright (good, latest)

---

## 🔧 The Problem: Why Themes Aren't Fully Working

### Current Flow
```
CSS defines variables
        ↓
Mermaid 11 initialization sees theme: 'base'
        ↓
Mermaid tries to read CSS custom properties from :root
        ↓
❌ PROBLEM: Mermaid 11 expects specific CSS variable names
        But we're using --mermaid-* naming convention
        Mermaid expects: --primary, --text-color, etc.
```

### Why It "Kind Of" Works
1. SVG text styling fixes readability in PDFs
2. Light text overrides work for most diagrams
3. But diagram fills/strokes still use Mermaid defaults

---

## ✨ Solution: Complete Theme Implementation

### Phase 1: Mermaid Configuration (CRITICAL)

**Problem**: Mermaid 11 doesn't automatically map our `--mermaid-*` variables

**Solution**: Explicitly pass `themeVariables` to Mermaid initialization

**File to Update**: `mermaid_enhancement_step.py`

```javascript
// CURRENT (broken):
mermaid.initialize({
    theme: 'base',
    themeVariables: {}  // ❌ Empty!
})

// FIXED (working):
mermaid.initialize({
    theme: 'base',
    themeVariables: {
        // Read CSS variables and pass to Mermaid
        primaryColor: getComputedStyle(document.documentElement).getPropertyValue('--mermaid-primaryColor'),
        primaryTextColor: getComputedStyle(document.documentElement).getPropertyValue('--mermaid-primaryTextColor'),
        primaryBorderColor: getComputedStyle(document.documentElement).getPropertyValue('--mermaid-primaryBorderColor'),
        // ... etc for all 80+ variables
    }
})
```

### Phase 2: CSS Variable Name Alignment

**Current**: `--mermaid-primaryColor`  
**Mermaid expects**: Map of actual theme variable names

**Solution**: Create a JavaScript mapping that reads all CSS variables at runtime:

```javascript
const getCSSVariables = () => {
    const root = getComputedStyle(document.documentElement);
    const vars = {};
    
    // Map all --mermaid-* variables to Mermaid's expected names
    vars.primaryColor = root.getPropertyValue('--mermaid-primaryColor').trim();
    vars.primaryTextColor = root.getPropertyValue('--mermaid-primaryTextColor').trim();
    // ... etc
    
    return vars;
};

mermaid.initialize({
    theme: 'base',
    themeVariables: getCSSVariables()
});
```

### Phase 3: Font Family Consistency

**Current**: Mermaid uses default serif font  
**Desired**: Use Inter (body) or JetBrains Mono (code)

**Solution**: Add font-family to Mermaid initialization:

```javascript
mermaid.initialize({
    theme: 'base',
    themeVariables: {
        fontFamily: '"Inter", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif'
    }
});
```

### Phase 4: Diagram-Specific Overrides

**Some diagrams need extra config** for full theme control:

```javascript
mermaid.initialize({
    // ... theme config
    
    // Flowchart
    flowchart: {
        htmlLabels: true,           // Use HTML for labels (respects CSS)
        nodeSpacing: 50,            // Space for readability
        rankSpacing: 50
    },
    
    // Sequence Diagram
    sequence: {
        useMaxWidth: true,
        actorMargin: 50,            // Actor spacing
        mirrorActors: true          // Dual-side actors
    },
    
    // Gantt
    gantt: {
        useMaxWidth: true,
        fontSize: 12,               // Readable task text
        numberSectionStyles: 2      // Color sections
    }
});
```

---

## 📋 Implementation Tasks

### Task 1: Update Mermaid Enhancement Step ⭐ CRITICAL

**File**: `tools/pdf/pipeline/steps/mermaid_enhancement_step.py`

**Changes**:
1. Replace empty `themeVariables: {}` with dynamic CSS variable reading
2. Add font-family configuration
3. Add diagram-specific settings
4. Include fallback colors for PDF rendering

**Complexity**: Medium (JavaScript generation in Python)

### Task 2: Add Mermaid Configuration Guide

**File**: `docs/MERMAID_CONFIGURATION_GUIDE.md`

**Content**:
- How Mermaid 11 reads CSS variables
- All 80+ variables and their purposes
- Per-diagram type configuration
- Testing procedures

### Task 3: Create Test Diagrams

**Location**: `docs/examples/mermaid/`

**Diagrams**:
- `flowchart-complete.md` - All flowchart elements
- `sequence-complete.md` - Sequence diagram with actors
- `state-complete.md` - State transitions
- `gantt-complete.md` - Gantt chart with tasks
- `class-complete.md` - Class diagram

**Purpose**: Visual regression testing

### Task 4: Update dark-pro.css

**Minor improvements**:
1. Add comments clarifying which variables are "critical"
2. Add fallback color values for unsupported themes
3. Verify all color values meet WCAG contrast requirements

### Task 5: Update Requirements & Versions

**Files to update**:
- `requirements-pdf.txt` - Pin Playwright version
- `Dockerfile` - Update system dependency versions
- `README.md` - Document Mermaid 11 theming

---

## 🐛 Known Issues & Workarounds

### Issue 1: HTML Rendering (Browser Preview)
**Problem**: Mermaid rendered in browser doesn't fully respect CSS variables  
**Workaround**: Use PDF output for final results  
**Fix**: Ensure Mermaid version ≥11.1.0

### Issue 2: Light Backgrounds
**Problem**: When using light theme, diagram fills become invisible  
**Workaround**: Current dark-pro profile only - add light themes later  
**Fix**: Create separate `light-pro.css` with opposite colors

### Issue 3: Playwright Rendering
**Problem**: Chromium may not render CSS custom properties before Mermaid initializes  
**Workaround**: Delay Mermaid initialization via `mermaid.contentLoaded()`  
**Fix**: Ensure CSS is loaded before Mermaid script executes

---

## 📈 Version Improvements

### Current Versions
```
Pandoc:     System (debian: 2.x, macOS: 3.x)
Node.js:    20.x LTS ✅ Good
Mermaid:    @11 (latest, ESM module) ✅ Good
Chromium:   Via Playwright (latest) ✅ Good
Playwright: >=1.40.0 ✅ Current
```

### Recommended Updates
```
Pandoc:     Pinned to >=3.1.0 (better SVG, better HTML output)
Node.js:    Keep 20.x LTS (stable)
Mermaid:    Pin to @11.2.0+ (better CSS variable support)
Chromium:   Auto-updated by Playwright ✅
Playwright: Pin to >=1.45.0 (better rendering)
```

---

## 🎯 Priority Order

### 🔴 CRITICAL (Do First)
1. **Update mermaid_enhancement_step.py** - Enable CSS variable reading
2. **Test with sample diagrams** - Verify themes work
3. **Document findings** - Update guides

### 🟡 HIGH (Do Next)
4. **Update Dockerfile Pandoc version** - Better SVG handling
5. **Create test suite** - Automated visual regression
6. **Update README** - Document Mermaid 11 theming

### 🟢 MEDIUM (Do Later)
7. **Add light theme** - Create `light-pro.css` for daytime use
8. **Optimize rendering** - Playwright settings for speed
9. **Add custom themes** - Branding options

---

## ✅ Success Criteria

✅ **Mermaid diagrams render with dark-pro colors**
✅ **All text readable (light on dark)**
✅ **Flowchart borders match primary color**
✅ **Sequence actor backgrounds use dark theme**
✅ **Gantt tasks show proper contrast**
✅ **PDF exports preserve all colors**
✅ **HTML preview matches PDF output**
✅ **No visual artifacts or color bleeding**

---

## 📚 Reference

- **Mermaid 11 Theming**: https://mermaid.js.org/theming/themes.html
- **CSS Custom Properties**: https://developer.mozilla.org/en-US/docs/Web/CSS/--*
- **Mermaid config**: https://mermaid.js.org/config/setup/mermaidConfig.html
- **Playwright rendering**: https://playwright.dev/docs/api/class-page#page-screenshot

---

## 🚀 Next Steps

1. Review this analysis
2. Prioritize which phase to implement first
3. Create branch: `feat/mermaid-themes-complete`
4. Assign Phase 1 (Mermaid enhancement) as first task
5. Test with sample diagrams
6. Document working solution

**Estimated effort**: 4-6 hours for complete implementation
