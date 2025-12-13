# 🚀 Quick Deploy: Diagram Path Fix

## What's Fixed

❌ **Before**: Diagrams showed as raw Mermaid code  
✅ **After**: Diagrams render properly as SVG images

## Deploy Now (5 minutes)

### Step 1: Pull Latest Code
```bash
git pull origin main
```

Changes:
- `tools/pdf/pipeline/steps/image_path_correction.py` (NEW)
- `tools/pdf/pipeline/steps/__init__.py` (UPDATED)
- `tools/pdf/pipeline/__init__.py` (UPDATED)
- `DEEP_FIX_DIAGRAM_PATH_ISSUE.md` (NEW - full details)

### Step 2: Rebuild Docker
```bash
docker build -t docs-pipeline:fixed .
```

### Step 3: Test
```bash
docker run --rm \
  -v ${PWD}/uploads:/app/uploads:ro \
  -v ${PWD}/output:/app/output:rw \
  docs-pipeline:fixed \
  python -m tools.pdf.cli convert \
  /app/uploads/streaming-architecture-spec.md \
  /app/output/streaming-test.pdf \
  --profile dark-pro --cover --toc
```

### Step 4: Verify
Open `output/streaming-test.pdf` - diagrams should render!

## What Changed (Technical)

### New Pipeline Order
```
DiagramRenderingStep (renders SVG)
  ↓
PandocConversionStep (converts to HTML)
  ↓
▶️ ImagePathCorrectionStep (FIX: corrects image paths) [NEW]
  ↓
Rest of pipeline...
```

### How It Works
After Pandoc generates HTML, the new step:
1. Finds all SVG files in work directory
2. Scans HTML for `<img src="...">` tags
3. Fixes broken paths to point to correct SVG files
4. Writes corrected HTML back

## Troubleshooting

### Diagrams still not showing?

**Enable verbose mode:**
```bash
... --verbose
```

Look for output:
```
[ImagePathCorrectionStep] Correcting paths for N SVG files
  Fixed: diagram.svg → diagram_001.svg
[ImagePathCorrectionStep] ✓ Corrected N image path(s)
```

### Check generated files:
```bash
# See if SVG files exist
ls -la /tmp/doc_*/diagram_*.svg

# Check HTML for img tags
cat /tmp/doc_*/output.html | grep -i '<img'
```

## Rollback (if needed)

If any issues, just remove the step:

**File**: `tools/pdf/pipeline/__init__.py`

```python
# Remove this line from create_pdf_pipeline():
ImagePathCorrectionStep(),  # <-- DELETE THIS
```

Then rebuild:
```bash
docker build -t docs-pipeline:rollback .
```

## Questions?

See full documentation: `DEEP_FIX_DIAGRAM_PATH_ISSUE.md`

---

**Ready to deploy?** Run the test command above! 🚀
