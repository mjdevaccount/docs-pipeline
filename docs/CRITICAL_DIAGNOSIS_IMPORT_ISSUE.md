# CRITICAL DIAGNOSIS: Diagram Rendering Failure (Bomb Icon Issue)

## The Problem

**Symptoms:**
- Diagrams show 💣 icon instead of rendering
- Native renderer fails silently
- Falls back to subprocess rendering (mmdc)
- mmdc also fails (likely separate Dockerfile issue)

**Root Cause Identified:**
Incorrect import path in `tools/pdf/pipeline/steps/diagram_step.py`

---

## The Code Chain

### Current State (BROKEN)

**File**: `tools/pdf/pipeline/steps/diagram_step.py` line 36-39
```python
try:
    from diagram_rendering import MermaidNativeRenderer, DiagramCache, DiagramFormat
except ImportError:
    self.log("MermaidNativeRenderer not available", context)
    return markdown_content, 0
```

### The Issue

**Where diagram_step.py is:**
```
tools/pdf/
└── pipeline/
    └── steps/
        └── diagram_step.py  ← HERE
```

**Where diagram_rendering is:**
```
tools/pdf/
└── diagram_rendering/  ← HERE
    ├── __init__.py
    ├── mermaid_native_renderer.py
    └── ...
```

### Why It Fails

The import `from diagram_rendering import ...` looks for `diagram_rendering` as a **top-level module**.

But the actual location is **sibling directory**, requiring a **relative import**.

**Relative path from diagram_step.py to diagram_rendering:**
```
diagram_step.py → tools/pdf/pipeline/steps/
goal:  tools/pdf/diagram_rendering/

Up 2 levels (steps → pipeline → pdf)
Then into diagram_rendering

Relative: ../../diagram_rendering
Import:  from ...diagram_rendering import
```

---

## The Fix (Choose One)

### Option 1: Correct Relative Import (RECOMMENDED)

**Change this** (line 36-39):
```python
try:
    from diagram_rendering import MermaidNativeRenderer, DiagramCache, DiagramFormat
except ImportError:
    self.log("MermaidNativeRenderer not available", context)
    return markdown_content, 0
```

**To this:**
```python
try:
    from ...diagram_rendering import MermaidNativeRenderer, DiagramCache, DiagramFormat
except ImportError:
    self.log("MermaidNativeRenderer not available", context)
    return markdown_content, 0
```

**Why:**
- Clean relative import
- Works anywhere in the project
- Pythonic standard
- No side effects

---

### Option 2: Fix sys.path (Alternative)

At the top of `diagram_step.py` (after existing imports):

**Find this:**
```python
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ..base import PipelineStep, PipelineContext, PipelineError
```

**Also add:**
```python
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ..base import PipelineStep, PipelineContext, PipelineError

# Fix for diagram_rendering import
sys.path.insert(0, str(Path(__file__).parent.parent))  # ADD THIS LINE
```

Then imports work as-is:
```python
from diagram_rendering import MermaidNativeRenderer, DiagramCache, DiagramFormat
```

**Note:** This is less clean than Option 1.

---

## Secondary Issue: mmdc Fallback Failure

Even when Phase B import fails, subprocess fallback (`mmdc`) also fails. This suggests:

### Likely Cause 1: mmdc Not in Docker PATH

**File**: `Dockerfile`

Check that mermaid-cli is installed and accessible:
```dockerfile
# Should exist
RUN npm install -g mermaid-cli@11.12.0
```

Verify mmdc is on PATH:
```dockerfile
RUN which mmdc && mmdc --version
```

### Likely Cause 2: Diagram Code Has Syntax Error

If both Phase B AND mmdc fail, the diagram code itself may have issues.

**Check:**
```bash
# Test mmdc directly
echo "graph LR A --> B" > test.mmd
mmdc -i test.mmd -o test.svg
```

### Likely Cause 3: Missing System Dependencies

**For Puppeteer (used by mmdc internally):**
```dockerfile
RUN apt-get update && apt-get install -y \
    libgbm-dev \
    libxss1 \
    libnss3 \
    libx11-xcb1 \
    && rm -rf /var/lib/apt/lists/*
```

---

## The Complete Fix (Step-by-Step)

### Step 1: Fix diagram_step.py Import

**File:** `tools/pdf/pipeline/steps/diagram_step.py`  
**Line:** 36-39  
**Change:**
```python
# FROM
try:
    from diagram_rendering import MermaidNativeRenderer, DiagramCache, DiagramFormat
except ImportError:
    self.log("MermaidNativeRenderer not available", context)
    return markdown_content, 0

# TO
try:
    from ...diagram_rendering import MermaidNativeRenderer, DiagramCache, DiagramFormat
except ImportError:
    self.log("MermaidNativeRenderer not available", context)
    return markdown_content, 0
```

### Step 2: Verify mmdc in Docker

**File:** `Dockerfile`  
**Add after npm install:**
```dockerfile
RUN which mmdc && mmdc --version
```

### Step 3: Test Locally

```bash
# 1. Make the import fix
git diff tools/pdf/pipeline/steps/diagram_step.py

# 2. Build Docker
docker build -t docs-pipeline:fix .

# 3. Test with a diagram
docker run --rm docs-pipeline:fix \
  python -m tools.pdf.cli diag env

# 4. Test diagram rendering
echo "graph LR A --> B --> C" > test.mmd
docker run --rm -v $(pwd):/workspace docs-pipeline:fix \
  mmdc -i /workspace/test.mmd -o /workspace/test.svg
```

---

## Root Cause Analysis

### How This Happened

1. **Phase A + B changes added** `diagram_rendering` module
2. **diagram_step.py created** to use Phase B native renderer
3. **Import path NOT updated** - assumed top-level import would work
4. **Fallback to mmdc** triggered (because import fails)
5. **mmdc also fails** (separate Docker/environment issue)
6. **Result**: Bomb icon (complete diagram failure)

### Why Both Failed

When your Phase B changes were integrated:
- The import hook was missing the relative path fix
- Even though fallback to mmdc was built-in, mmdc wasn't working either
- So ALL diagram rendering failed

---

## Impact

**After Fix:**
- Phase B native renderer will work (import fixed)
- Fallback to mmdc will work (if Dockerfile is correct)
- Diagrams will render properly
- No more bomb icons

**Expected Performance:**
- Phase B renders: 60-120ms per diagram (40-60% faster)
- Fallback renders: 150-250ms per diagram (current subprocess speed)
- Both working = zero failures

---

## Quick Summary

| Item | Status | Action |
|------|--------|--------|
| **Import Path** | ❌ BROKEN | Change `from diagram_rendering` → `from ...diagram_rendering` |
| **mmdc Fallback** | ⚠️ UNTESTED | Verify in Docker: `which mmdc && mmdc --version` |
| **Diagram Code** | ⚠️ UNKNOWN | Test mmdc directly with sample diagram |
| **System Deps** | ⚠️ MAYBE | May need Puppeteer dependencies in Dockerfile |

---

## Files to Check

1. **`tools/pdf/pipeline/steps/diagram_step.py`** - Fix line 36-39
2. **`Dockerfile`** - Verify mmdc installation and dependencies
3. **Test with actual diagram** - Confirm syntax is valid

---

## Status

✅ **Root Cause Identified**  
✅ **Fix Documented**  
⏳ **Awaiting Implementation**  

**Next Action**: Apply Step 1 above to fix the import.
