# PDF Generation Quick Reference

**Professional Markdown → PDF conversion using Pandoc + WeasyPrint + Mermaid-CLI**

## Quick Start

```bash
# Activate virtual environment
.\venv-pdf\Scripts\activate

# Check dependencies
python convert_final.py --check

# Convert a document
python convert_final.py docs/report.md
```

## Common Commands

```bash
# Single file (auto output)
python convert_final.py docs/report.md

# Single file (custom output)
python convert_final.py docs/report.md output/report.pdf

# Batch conversion
python convert_final.py --batch docs/*.md

# Using config file
python convert_final.py --config pdf-config.json

# With custom logo
python convert_final.py --logo assets/logo.png docs/report.md
```

## Files

- **`convert_final.py`** - CLI wrapper (use this!)
- **`convert_final.py`** - Core conversion engine
- **`requirements-pdf.txt`** - Python dependencies
- **`PDF_GENERATION_SETUP.md`** - Complete setup guide
- **`pdf-config.json.example`** - Example config file

## Markdown Syntax

### YAML Frontmatter (Optional)
```markdown
---
title: Document Title
author: Your Name
organization: Company Name
date: November 2025
version: 1.0
type: Technical Specification
classification: CONFIDENTIAL
---
```

### Mermaid Diagrams
```markdown
```mermaid
graph LR
    A[Start] --> B[Process]
    B --> C[End]
```
```

## Installation

See **`PDF_GENERATION_SETUP.md`** for complete installation instructions.

**Quick install:**
1. `pip install -r requirements-pdf.txt`
2. Install Pandoc: `choco install pandoc`
3. Install Mermaid-CLI: `npm install -g @mermaid-js/mermaid-cli`
4. (Windows) Install GTK: See setup guide

## Help

```bash
python convert_final.py --help
```

For detailed documentation, see **`PDF_GENERATION_SETUP.md`**.

