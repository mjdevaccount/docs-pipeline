# CLI Upgrade Guide: v3.x → v4.0.0 (2025)

**TL;DR:** New CLI is better. Phase B is now built-in. Old commands still work (for now).

---

## What Changed

### Framework Upgrade

| Aspect | v3.x | v4.0.0 |
|--------|------|--------|
| **Framework** | argparse | Typer |
| **Output** | Plain text | Rich (beautiful) |
| **Command structure** | Flat | Organized subcommands |
| **Error messages** | Generic | Helpful with hints |
| **Phase B support** | Hidden | Clear flags |

### New CLI Structure

```
Old:
  python -m tools.pdf.cli.main input.md output.pdf --profile tech-whitepaper

New:
  python -m tools.pdf.cli convert input.md output.pdf --profile tech-whitepaper
```

---

## Installation

### Install New Dependencies

```bash
pip install typer>=0.9.0 rich>=13.0.0
```

### Or all at once:

```bash
pip install -r tools/pdf/requirements-cli.txt
```

---

## Command Mapping

### Single File Conversion

**v3.x:**
```bash
python -m tools.pdf.cli.main input.md output.pdf --profile tech-whitepaper
```

**v4.0.0:**
```bash
python -m tools.pdf.cli convert input.md output.pdf --profile tech-whitepaper
```

### Batch Conversion

**v3.x:**
```bash
python -m tools.pdf.cli.main --batch doc1.md doc2.md --threads 4
```

**v4.0.0:**
```bash
python -m tools.pdf.cli batch doc1.md doc2.md
```

### Glossary

**v3.x:**
```bash
python -m tools.pdf.cli.main input.md output.pdf --glossary glossary.yaml
```

**v4.0.0:**
```bash
python -m tools.pdf.cli convert input.md output.pdf --glossary glossary.yaml
```

---

## Key New Features

### 1. Phase B Control

Phase B (native Playwright renderer) is now explicit:

```bash
# Use Phase B (40-60% faster) - DEFAULT
python -m tools.pdf.cli convert input.md output.pdf --native

# Disable Phase B (use mmdc fallback)
python -m tools.pdf.cli convert input.md output.pdf --no-native
```

### 2. Built-in Diagnostics

```bash
# Check your system
python -m tools.pdf.cli diag env

# Test Phase B renderer
python -m tools.pdf.cli diag phase-b
```

### 3. Better Error Messages

**v3.x:**
```
[ERROR] File not found
```

**v4.0.0:**
```
✗ Input file not found
  Could not open: missing.md

→ Check the path: /home/user/missing.md
```

### 4. Progress Bars

Batch processing now shows progress:

```
✓ doc1.md → doc1.pdf
✓ doc2.md → doc2.pdf
✓ doc3.md → doc3.pdf
```

---

## Migration Checklist

- [ ] Install Typer + Rich: `pip install typer rich`
- [ ] Update scripts to use `python -m tools.pdf.cli convert` instead of `python -m tools.pdf.cli.main`
- [ ] Test Phase B: `python -m tools.pdf.cli diag phase-b`
- [ ] Check environment: `python -m tools.pdf.cli diag env`
- [ ] Update batch commands to use `batch` subcommand
- [ ] Review new `--native` / `--no-native` flags for Phase B control

---

## Backward Compatibility

**Old CLI (`main.py`) is deprecated but still available** for 1-2 major versions:

```bash
# Still works (for now)
python -m tools.pdf.cli.main input.md output.pdf
```

**But you should migrate to new CLI:**

```bash
# New way (recommended)
python -m tools.pdf.cli convert input.md output.pdf
```

---

## Quick Reference

### Convert Single File

```bash
python -m tools.pdf.cli convert input.md output.pdf [OPTIONS]
```

**Common options:**
- `--profile tech-whitepaper` - Style profile
- `--cover` - Add cover page
- `--toc` - Add table of contents  
- `--native` / `--no-native` - Phase B control
- `--format docx` - Output format
- `--verbose` - Show details

### Batch Convert

```bash
python -m tools.pdf.cli batch docs/**/*.md [OPTIONS]
```

**Common options:**
- `--output-dir output/` - Output directory
- `--format pdf` - Output format
- `--profile tech-whitepaper` - Style profile
- `--native` / `--no-native` - Phase B control

### Diagnostics

```bash
# Check environment
python -m tools.pdf.cli diag env

# Test Phase B
python -m tools.pdf.cli diag phase-b
```

---

## Example Migration

### Before (v3.x)

```bash
#!/bin/bash
# Old build script
python -m tools.pdf.cli.main docs/index.md output/index.pdf --profile tech-whitepaper
python -m tools.pdf.cli.main docs/guide.md output/guide.pdf --profile tech-whitepaper
python -m tools.pdf.cli.main docs/api.md output/api.pdf --profile tech-whitepaper
```

### After (v4.0.0)

```bash
#!/bin/bash
# New build script (cleaner)
python -m tools.pdf.cli batch docs/*.md --output-dir output/ --profile tech-whitepaper
```

---

## Performance

### Phase B is Now Default

**v3.x:**
- Used subprocess mmdc CLI
- ~150-200ms per diagram

**v4.0.0:**
- Uses Phase B native renderer by default
- ~60-120ms per diagram
- **40-60% faster**

### Test it:

```bash
# Time conversion (Phase B enabled by default)
time python -m tools.pdf.cli convert docs/large.md output.pdf
```

---

## Need Help?

### Show Help

```bash
# Overall help
python -m tools.pdf.cli --help

# Convert command help
python -m tools.pdf.cli convert --help

# Batch command help
python -m tools.pdf.cli batch --help

# Diagnostics help
python -m tools.pdf.cli diag --help
```

### Common Issues

**"typer not found"**
```bash
pip install typer rich
```

**"Phase B not working"**
```bash
python -m tools.pdf.cli diag phase-b
```

**"Pandoc not found"**
```bash
python -m tools.pdf.cli diag env
```

---

## Documentation

See **`CLI_MODERN_REDESIGN.md`** for full documentation.

---

## Summary

✅ **Typer + Rich** - Modern, beautiful CLI  
✅ **Phase B integrated** - 40-60% faster by default  
✅ **Better UX** - Helpful errors, progress bars, colors  
✅ **Diagnostics** - Built-in environment checks  
✅ **Backward compatible** - Old CLI still works (for now)  

**Status:** Ready for production  
**Migration effort:** Low (just update command names)  
**Benefits:** Faster, cleaner, more professional  

---

**Ready to upgrade?** Start here:

```bash
pip install typer rich
python -m tools.pdf.cli diag env
python -m tools.pdf.cli convert input.md output.pdf
```

Enjoy! 🚀
