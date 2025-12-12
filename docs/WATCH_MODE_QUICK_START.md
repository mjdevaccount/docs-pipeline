# 🔄 Watch Mode Quick Start

**Zero Manual Rebuilds. Edit. Save. Done.**

---

## Installation (30 seconds)

### 1. Install watchdog
```bash
pip install watchdog
```

### 2. That's it! 🚀

---

## Basic Usage (1 minute)

### Simple Watch
```bash
# Watch a markdown file, auto-rebuild PDF
python -m tools.pdf.cli.watch_mode book.md book.pdf
```

**Output**:
```
============================================================
  Watch Mode Active
============================================================
[WATCH] Monitoring 1 files
[WATCH] Watching 1 directories
[WATCH] Debounce: 500ms
[WATCH] Press Ctrl+C to stop
```

**Now**: Edit `book.md` in your editor → PDF rebuilds automatically!

---

## Common Workflows

### Workflow 1: Technical Documentation
```bash
# Watch with professional styling
python -m tools.pdf.cli.watch_mode api-docs.md api.pdf \
    --profile tech-whitepaper \
    --toc \
    --cover

# Now:
# - Edit api-docs.md
# - Save
# - PDF updates instantly with TOC and cover
```

### Workflow 2: E-Book Writing
```bash
# Watch with EPUB output
python -m tools.pdf.cli.watch_mode novel.md novel.epub \
    --format epub \
    --title "My Novel" \
    --author "Jane Doe"

# Now:
# - Edit novel.md
# - Save
# - EPUB updates for e-reader
```

### Workflow 3: Report with Glossary
```bash
# Watch with glossary integration
python -m tools.pdf.cli.watch_mode report.md report.pdf \
    --glossary glossary.yaml \
    --watch-glossary glossary.yaml

# Now:
# - Edit report.md OR glossary.yaml
# - Save either
# - PDF rebuilds with updated glossary
```

### Workflow 4: Design with Assets
```bash
# Watch with CSS and images
python -m tools.pdf.cli.watch_mode doc.md doc.pdf \
    --watch-css styles/ \
    --watch-images images/ \
    --profile enterprise-blue

# Now:
# - Edit doc.md
# - Edit styles/custom.css
# - Update images/logo.png
# - Any change triggers rebuild
```

---

## Configuration (Advanced)

### Create watch.json
```json
{
  "watched_files": [
    {
      "input": "book.md",
      "output": "book.pdf",
      "format": "pdf",
      "profile": "tech-whitepaper",
      "cover": true,
      "toc": true
    },
    {
      "input": "guide.md",
      "output": "guide.epub",
      "format": "epub",
      "title": "User Guide",
      "author": "Tech Team"
    }
  ],
  "watch_deps": ["styles/", "images/"],
  "debounce_ms": 500,
  "verbose": true
}
```

### Run with config
```bash
python -m tools.pdf.cli.watch_mode --config watch.json
```

**Output**:
```
[WATCH] Monitoring 4 files
[WATCH] Watching 3 directories

# Edit book.md
[BUILD] book.md -> book.pdf
[OK] Built in 0.38s

# Edit guide.md
[BUILD] guide.md -> guide.epub
[OK] Built in 0.52s
```

---

## Pro Tips ✨

### Tip 1: Multiple Outputs
```bash
# Watch markdown, generate PDF + EPUB
# Create watch.json with both files
# Edit once, get both formats!
```

### Tip 2: Fast Preview Loop
```bash
# Split screen:
# Left: VS Code (editing)
# Right: Watch mode running
# Center: PDF viewer
# Result: Edit -> Save -> Instant PDF
```

### Tip 3: Verbose Debugging
```bash
# When something isn't rebuilding:
python -m tools.pdf.cli.watch_mode doc.md doc.pdf \
    --watch-deps . \
    --verbose

# Shows exactly which files are being monitored
# and why builds trigger
```

### Tip 4: Adjust Debounce
```bash
# Too many rebuilds?
python -m tools.pdf.cli.watch_mode doc.md doc.pdf \
    --debounce 2000  # 2 second delay

# Rebuilding too slowly?
python -m tools.pdf.cli.watch_mode doc.md doc.pdf \
    --debounce 200   # 200ms delay
```

---

## Metrics & Status

### Live Metrics (Verbose)
```bash
python -m tools.pdf.cli.watch_mode doc.md doc.pdf --verbose

# Shows:
# [WATCH] File changed: doc.md
# [WATCH] Triggering rebuild for: doc.md
# [BUILD] doc.md -> doc.pdf
# [TIME] 14:32:45
# [OK] Built in 0.38s
```

### Final Report (On Exit)
```bash
# When you press Ctrl+C:
============================================================
  Watch Mode Complete
============================================================
[INFO] Watch Mode Metrics
       Total Rebuilds: 12
       Successful: 11
       Failed: 1
       Success Rate: 91.7%
       Average Build Time: 0.40s
       Last Build Time: 0.42s
       Total Session Time: 25.34s
       Files Watched: 8
```

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **watchdog not installed** | `pip install watchdog` |
| **No rebuilds happening** | Check file path, use `--verbose` |
| **Too many rebuilds** | Increase `--debounce` to 1000-2000ms |
| **Slow rebuilds** | Check for large files, enable cache with `--no-cache` removed |
| **Permission denied** | Check file permissions, try different directory |

---

## Before vs After

### Before (Without Watch Mode)
```bash
# 1. Edit markdown
# 2. Save file
# 3. Open terminal
# 4. Run conversion
python -m tools.pdf.cli.main doc.md doc.pdf
# 5. Wait for build
# 6. View PDF
# 7. Edit again
# 8. Repeat steps 2-6

# Result: Manual rebuild every time, context switching, slow loop
```

### After (With Watch Mode)
```bash
# 1. Start watch ONCE
python -m tools.pdf.cli.watch_mode doc.md doc.pdf &

# 2. Edit markdown
# 3. Save (Ctrl+S)
# 4. Automatic rebuild happens
# 5. View PDF (it's updated!)
# 6. Edit again
# 7. Save
# 8. Auto-rebuild
# ... repeat 6-8 ...

# Result: Automatic rebuilds, no context switching, fast loop
```

---

## Real-World Examples

### Example 1: Writing a Book
```bash
python -m tools.pdf.cli.watch_mode my-novel.md my-novel.pdf \
    --cover \
    --toc \
    --profile tech-whitepaper

# Every time you save: PDF updates with your latest changes
# See cover, TOC, formatting all live
```

### Example 2: Building API Docs
```bash
python -m tools.pdf.cli.watch_mode api-reference.md api.pdf \
    --watch-css styles/api.css \
    --glossary terms.yaml \
    --profile enterprise-blue

# Edit any:
# - api-reference.md
# - styles/api.css
# - terms.yaml
# PDF updates automatically
```

### Example 3: Team Documentation
```bash
# watch.json
{
  "watched_files": [
    {"input": "README.md", "output": "readme.pdf"},
    {"input": "GUIDE.md", "output": "guide.pdf"},
    {"input": "API.md", "output": "api.pdf"}
  ],
  "watch_deps": ["styles/", "images/", "glossary.yaml"],
  "debounce_ms": 500
}
```

```bash
python -m tools.pdf.cli.watch_mode --config watch.json

# Team edits any doc -> all PDFs update automatically
```

---

## Performance

**Typical Build Times**:
- Small markdown (< 10KB): **0.3s**
- Medium markdown (10-50KB): **0.4s**
- Large markdown (> 50KB): **0.5-1.0s**

**Cache Benefits**:
- First build: 0.45s
- Cached rebuilds: 0.38s (15% faster)
- With complex glossary: 30-40% faster

---

## Next Steps

1. **Try it**: `python -m tools.pdf.cli.watch_mode doc.md doc.pdf`
2. **Edit**: Make changes to doc.md
3. **Save**: Ctrl+S
4. **Observe**: PDF rebuilds automatically
5. **Repeat**: Edit more, see instant updates

---

## Getting Help

```bash
# Full help
python -m tools.pdf.cli.watch_mode --help

# Verbose mode for debugging
python -m tools.pdf.cli.watch_mode doc.md doc.pdf --verbose

# Check implementation
cat tools/pdf/cli/watch_mode.py
```

---

**That's it! You now have a professional live editing workflow.** 🚀
