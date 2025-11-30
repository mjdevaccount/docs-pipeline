# Playwright Setup for FAANG-Grade PDF Generation

## Overview

Playwright provides perfect SVG rendering including `<foreignObject>` elements, which WeasyPrint cannot handle. This is the industry-standard approach used by Microsoft, AWS, and Stripe for production documentation.

## Installation

### 1. Install Python Package

```bash
pip install playwright
```

### 2. Install Chromium Browser

```bash
playwright install chromium
```

This downloads the Chromium browser (~170MB) that Playwright uses for rendering.

### 3. Verify Installation

```bash
python pdf-tools/pdf_playwright.py --check
```

Expected output:
```
[OK] Playwright Chromium available
```

## Usage

### Command Line

```bash
# Use Playwright renderer (perfect SVG)
python pdf-tools/md2pdf.py input.md output.pdf --renderer playwright

# Use WeasyPrint renderer (fast, but limited SVG)
python pdf-tools/md2pdf.py input.md output.pdf --renderer weasyprint
```

### Default Behavior

- **Default**: WeasyPrint (fast, good for drafts)
- **Production**: Playwright (perfect rendering, FAANG-grade)

## Comparison

| Feature | WeasyPrint | Playwright |
|---------|------------|------------|
| SVG foreignObject | ❌ No | ✅ Yes |
| Rendering Quality | Medium | Excellent |
| Speed | Fast | Medium |
| CI/CD Friendly | ✅ Yes | ✅ Yes |
| Industry Standard | ⚠️ Legacy | ✅ Primary |

## Troubleshooting

### Playwright Not Found

If you see:
```
[ERROR] Playwright not installed
```

Solution:
```bash
pip install playwright
playwright install chromium
```

### Chromium Not Found

If you see:
```
[WARN] Playwright installed but Chromium not found
```

Solution:
```bash
playwright install chromium
```

### Fallback Behavior

If Playwright is not available, the system automatically falls back to WeasyPrint with a warning message.

## Performance Notes

- **Playwright**: ~2-5 seconds per document (includes browser startup)
- **WeasyPrint**: ~1-2 seconds per document (faster, but limited SVG)

For production documentation with complex diagrams, Playwright is recommended.

