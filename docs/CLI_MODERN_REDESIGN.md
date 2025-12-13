# Modern CLI Redesign (v4.0.0)

**Date:** December 13, 2025  
**Framework:** Typer + Rich (2025 standards)  
**Status:** Complete & Live  

---

## Overview

The CLI has been completely redesigned with:

✅ **Typer** - Type-safe, auto-completing command structure  
✅ **Rich** - Beautiful terminal output with colors, tables, progress bars  
✅ **Phase B Integration** - Native renderer control with clear flags  
✅ **Diagnostics** - Built-in environment checks and Phase B testing  
✅ **Modern UX** - Helpful error messages with actionable hints  

---

## Installation

### Install CLI Dependencies

```bash
pip install typer>=0.9.0 rich>=13.0.0
```

### Or from requirements

```bash
pip install -r tools/pdf/requirements-cli.txt
```

---

## Quick Start

### Basic Conversion

```bash
# Convert to PDF (Phase B enabled by default)
python -m tools.pdf.cli convert input.md output.pdf

# Convert to DOCX
python -m tools.pdf.cli convert input.md output.docx --format docx

# Convert to HTML
python -m tools.pdf.cli convert input.md output.html --format html
```

### Batch Processing

```bash
# Convert all markdown files in a directory
python -m tools.pdf.cli batch docs/**/*.md --format pdf

# Output to specific directory
python -m tools.pdf.cli batch docs/**/*.md --output-dir output/

# Disable Phase B (use mmdc fallback)
python -m tools.pdf.cli batch docs/**/*.md --no-native
```

### Diagnostics

```bash
# Check environment setup
python -m tools.pdf.cli diag env

# Test Phase B native renderer
python -m tools.pdf.cli diag phase-b
```

---

## Commands

### `convert` - Single file conversion

**Basic usage:**
```bash
python -m tools.pdf.cli convert INPUT_FILE [OUTPUT_FILE] [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format`, `-f` | pdf \| docx \| html | pdf | Output format |
| `--profile`, `-p` | string | None | Style profile (tech-whitepaper, dark-pro, enterprise-blue, minimalist) |
| `--native` / `--no-native` | flag | --native | Use Phase B native Playwright renderer (40-60% faster) |
| `--diagrams` / `--no-diagrams` | flag | --diagrams | Render Mermaid diagrams |
| `--cover` | flag | False | Generate cover page (PDF only) |
| `--toc` | flag | False | Generate table of contents |
| `--cache` / `--no-cache` | flag | --cache | Cache diagram renders |
| `--verbose`, `-v` | normal \| verbose \| debug | normal | Logging level |

**Examples:**

```bash
# Convert with cover and TOC
python -m tools.pdf.cli convert input.md output.pdf --cover --toc

# Use tech-whitepaper profile
python -m tools.pdf.cli convert input.md output.pdf --profile tech-whitepaper

# Disable Phase B (use mmdc)
python -m tools.pdf.cli convert input.md output.pdf --no-native

# Show detailed rendering info
python -m tools.pdf.cli convert input.md output.pdf --verbose

# Debug mode (full stack traces)
python -m tools.pdf.cli convert input.md output.pdf --verbose debug
```

---

### `batch` - Multiple file conversion

**Basic usage:**
```bash
python -m tools.pdf.cli batch INPUT_FILES... [OPTIONS]
```

**Options:**

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--format`, `-f` | pdf \| docx \| html | pdf | Output format |
| `--output-dir`, `-o` | path | current dir | Output directory for all files |
| `--profile`, `-p` | string | None | Style profile |
| `--native` / `--no-native` | flag | --native | Use Phase B renderer |
| `--verbose`, `-v` | normal \| verbose | normal | Logging level |

**Examples:**

```bash
# Convert all .md files in docs/ to PDF
python -m tools.pdf.cli batch docs/**/*.md --format pdf

# Output to output/ directory
python -m tools.pdf.cli batch docs/**/*.md --output-dir output/

# Convert to DOCX with specific profile
python -m tools.pdf.cli batch docs/**/*.md --format docx --profile enterprise-blue

# Show progress (verbose)
python -m tools.pdf.cli batch docs/**/*.md --verbose
```

---

### `diag env` - Environment diagnostics

**Usage:**
```bash
python -m tools.pdf.cli diag env [--paths]
```

**Shows:**
- Python version and platform
- Dependency status (Playwright, Pandoc, Node.js)
- Phase B availability

**Example:**
```bash
$ python -m tools.pdf.cli diag env

Environment Check

Python: 3.11.8
Platform: Linux 6.6.5-arch1-1

Dependencies

✓ Playwright (browser automation)
✓ Pandoc (markdown conversion): 3.1.8
✓ Node.js (Mermaid rendering): v20.10.0

Phase B Status

✓ MermaidNativeRenderer available
  Phase B will be used by default (40-60% faster)
```

---

### `diag phase-b` - Phase B renderer test

**Usage:**
```bash
python -m tools.pdf.cli diag phase-b
```

**Tests:**
- Phase B availability
- Renders a test diagram
- Reports timing and SVG size

**Example:**
```bash
$ python -m tools.pdf.cli diag phase-b

Phase B Renderer Test

Rendering test diagram...
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ✓ Phase B Working!                 ┃
┃ Render time: 85.3ms                ┃
┃ SVG size: 2844 bytes               ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

---

## Phase B Integration

Phase B (native Playwright renderer) is **enabled by default** and provides:

✅ **40-60% faster** diagram rendering  
✅ **Automatic fallback** to mmdc CLI if Phase B unavailable  
✅ **Transparent** - no code changes needed  

### Enable Phase B (Default)

```bash
# Explicitly enable
python -m tools.pdf.cli convert input.md output.pdf --native

# Or just use default (Phase B is on by default)
python -m tools.pdf.cli convert input.md output.pdf
```

### Disable Phase B (Use mmdc CLI)

```bash
# Force subprocess mmdc
python -m tools.pdf.cli convert input.md output.pdf --no-native
```

### Check Phase B Status

```bash
# Check if Phase B is available
python -m tools.pdf.cli diag env

# Test Phase B rendering
python -m tools.pdf.cli diag phase-b
```

---

## Error Handling

### Helpful Error Messages

The CLI provides actionable error hints:

```bash
$ python -m tools.pdf.cli convert missing.md output.pdf

✗ Input file not found
  Could not open: missing.md

→ Check the path: /home/user/missing.md
```

### Exit Codes

| Code | Meaning | Action |
|------|---------|--------|
| 0 | Success | ✅ File(s) converted |
| 1 | User/conversion error | ❌ Check file path, format, or config |
| 2 | Environment error | ❌ Install missing dependencies |

---

## Output Formats

### PDF (Default)

```bash
python -m tools.pdf.cli convert input.md output.pdf --cover --toc
```

**Features:**
- Professional formatting
- Optional cover page
- Optional table of contents
- Custom styling via profiles
- Diagram rendering

### DOCX

```bash
python -m tools.pdf.cli convert input.md output.docx --format docx
```

**Features:**
- Microsoft Word compatible
- Formatting preserved
- Images embedded

### HTML

```bash
python -m tools.pdf.cli convert input.md output.html --format html
```

**Features:**
- Web-ready output
- Responsive layout
- Syntax highlighting

---

## Style Profiles

Use `--profile` to apply predefined styles:

```bash
# Tech/whitepaper style (clean, minimal)
python -m tools.pdf.cli convert input.md output.pdf --profile tech-whitepaper

# Dark professional style
python -m tools.pdf.cli convert input.md output.pdf --profile dark-pro

# Enterprise corporate style
python -m tools.pdf.cli convert input.md output.pdf --profile enterprise-blue

# Minimalist style
python -m tools.pdf.cli convert input.md output.pdf --profile minimalist
```

---

## Verbose Output

Enable verbose logging to see detailed information:

```bash
# Normal verbosity (default)
python -m tools.pdf.cli convert input.md output.pdf

# Verbose mode (see Phase B metrics, timing, etc.)
python -m tools.pdf.cli convert input.md output.pdf --verbose

# Debug mode (full stack traces, all details)
python -m tools.pdf.cli convert input.md output.pdf --verbose debug
```

---

## Typical Workflows

### Convert single report

```bash
python -m tools.pdf.cli convert report.md report.pdf --cover --toc --profile tech-whitepaper
```

### Batch convert documentation

```bash
python -m tools.pdf.cli batch docs/**/*.md --output-dir output/ --profile tech-whitepaper
```

### Export to Word

```bash
python -m tools.pdf.cli convert document.md document.docx --format docx
```

### Check system is ready

```bash
python -m tools.pdf.cli diag env
python -m tools.pdf.cli diag phase-b
```

### Performance testing

```bash
# With Phase B (fast)
python -m tools.pdf.cli convert input.md output-phase-b.pdf --native --verbose

# Without Phase B (fallback)
python -m tools.pdf.cli convert input.md output-mmdc.pdf --no-native --verbose
```

---

## Docker Usage

### Run inside Docker container

```bash
# Build image
docker build -t docs-pipeline .

# Run convert command
docker run --rm -v $(pwd):/workspace docs-pipeline \
  python -m tools.pdf.cli convert /workspace/input.md /workspace/output.pdf

# Run batch conversion
docker run --rm -v $(pwd):/workspace docs-pipeline \
  python -m tools.pdf.cli batch /workspace/docs/**/*.md --output-dir /workspace/output/
```

---

## Troubleshooting

### Phase B not working

```bash
# Check if available
python -m tools.pdf.cli diag env

# Test it
python -m tools.pdf.cli diag phase-b

# Install Playwright if missing
python -m playwright install chromium
```

### Pandoc not found

```bash
# Check environment
python -m tools.pdf.cli diag env

# Install Pandoc
# macOS
brew install pandoc

# Ubuntu/Debian
sudo apt install pandoc

# Windows
choco install pandoc
```

### Memory issues with large documents

```bash
# Use smaller batches
python -m tools.pdf.cli batch docs/part1/**/*.md --output-dir output/
python -m tools.pdf.cli batch docs/part2/**/*.md --output-dir output/
```

---

## Comparison: Old vs New CLI

| Feature | Old | New |
|---------|-----|-----|
| **Framework** | argparse | Typer |
| **Output** | Plain text | Rich (colors, tables, progress) |
| **Commands** | Flat options | Organized subcommands |
| **Error handling** | Generic errors | Helpful hints with solutions |
| **Phase B** | Hidden flag | Clear `--native` / `--no-native` |
| **Diagnostics** | Manual checking | `diag env`, `diag phase-b` |
| **Type safety** | Limited | Full type hints |
| **Auto-completion** | No | Yes (Typer) |
| **Help text** | Long | Concise with examples |

---

## What's Next

✅ **Phase B integrated** - Use `--native` flag  
✅ **Modern CLI** - Typer + Rich  
✅ **Diagnostics** - Check your system  
✅ **Error hints** - Helpful guidance  

**Future enhancements:**
- Watch mode for auto-rebuild
- Configuration file support (.docs-pipeline.toml)
- Custom template system
- CI/CD integration helpers

---

## Documentation References

- **Typer Docs:** https://typer.tiangolo.com/
- **Rich Docs:** https://rich.readthedocs.io/
- **Phase B Integration:** See `PHASE_B_INTEGRATION_COMPLETE.md`
- **Pipeline Docs:** See `/docs/` directory

---

**Status:** ✅ Production Ready  
**Framework:** Typer + Rich (2025 standards)  
**Phase B:** Integrated and enabled by default  

Enjoy the new CLI! 🚀
