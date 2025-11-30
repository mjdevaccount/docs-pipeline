# Playwright PDF Generator - Modular Architecture

## Overview

This package has been refactored from a monolithic 1,666-line file into a clean, modular architecture following SOLID principles. Each module has a single, well-defined responsibility.

## Architecture

### Package Structure

```
playwright_pdf/
├── __init__.py           # Package initialization
├── config.py             # Configuration dataclasses
├── browser.py            # Browser lifecycle management
├── dom_analyzer.py       # Pure DOM analysis (no mutations)
├── layout_model.py        # Domain models (dataclasses)
├── layout_transformer.py # Scaling decisions + DOM mutations
├── styles.py             # CSS injection + fonts
├── pdf_renderer.py       # PDF generation (page.pdf wrapper)
├── postprocess.py        # Metadata + bookmarks (file operations)
├── pipeline.py           # High-level orchestration
├── cli.py                # Command-line interface
└── decorators/
    ├── cover.py          # Cover page injection
    ├── toc.py           # Table of contents
    └── watermark.py     # Watermark injection
```

## Design Principles

### Single Responsibility Principle (S)

Each module has one clear purpose:
- `browser.py`: Only handles Playwright browser lifecycle
- `dom_analyzer.py`: Only reads DOM, returns analysis model
- `layout_transformer.py`: Only computes scaling decisions and applies them
- `styles.py`: Only handles CSS and fonts
- `pdf_renderer.py`: Only calls `page.pdf()`
- `postprocess.py`: Only modifies PDF files (metadata, bookmarks)

### Open/Closed Principle (O)

New features can be added without modifying existing modules:
- Add new decorators by creating new files in `decorators/`
- Extend layout model without changing analysis logic
- Add new scaling strategies without touching DOM analysis

### Liskov Substitution Principle (L)

Interfaces are consistent:
- All decorators follow the same pattern: `async def inject_X(page, config, verbose)`
- All analysis functions return `LayoutAnalysis` model
- All transformers work with `ScalingDecision` objects

### Interface Segregation Principle (I)

Small, focused interfaces:
- `compute_scaling()` takes `LayoutAnalysis`, returns `List[ScalingDecision]`
- `apply_scaling()` takes `List[ScalingDecision]`, applies to DOM
- No God methods with 20+ parameters

### Dependency Inversion Principle (D)

High-level modules don't depend on low-level details:
- Pipeline orchestrator depends on abstractions (config objects)
- Scaling logic is pure Python, testable without Playwright
- JS is "dumb actuator" - receives decisions, applies them

## Pipeline Flow

```
1. Load → browser.py opens Playwright page
2. Analyze → dom_analyzer.py reads DOM → LayoutAnalysis model
3. Transform → layout_transformer.py computes decisions → applies scaling
4. Decorate → styles.py + decorators/ inject CSS, cover, TOC, watermark
5. Render → pdf_renderer.py calls page.pdf()
6. Post-process → postprocess.py adds metadata + bookmarks
```

## Key Benefits

### 1. Testability

- `compute_scaling()` can be unit tested with fake `LayoutAnalysis` objects
- No need for Playwright or browser to test scaling logic
- Each module can be tested in isolation

### 2. Maintainability

- Changes to scaling logic don't affect DOM analysis
- CSS changes don't require touching scaling code
- Adding new decorators doesn't modify existing ones

### 3. Debuggability

- Clear boundaries make it easy to isolate issues
- Can inspect `LayoutAnalysis` and `ScalingDecision` objects directly
- No more scrolling through 5,000 lines to find the problem

### 4. Scalability

- Easy to add new features (e.g., new decorator types)
- Can swap implementations (e.g., different scaling strategies)
- Can parallelize different phases if needed

## Usage

### Programmatic API

```python
from playwright_pdf.pipeline import generate_pdf
from playwright_pdf.config import PdfGenerationConfig
from pathlib import Path

config = PdfGenerationConfig(
    html_file=Path("input.html"),
    pdf_file=Path("output.pdf"),
    title="My Document",
    author="John Doe",
    generate_cover=True,
    generate_toc=True,
    verbose=True
)

success = await generate_pdf(config)
```

### CLI

```bash
python -m playwright_pdf.cli input.html output.pdf \
    --title "My Document" \
    --author "John Doe" \
    --generate-cover \
    --generate-toc \
    --verbose
```

### Backward Compatibility

The original `pdf_playwright.py` script still works exactly as before, but now delegates to the modular package internally.

## Migration Notes

The refactoring maintains 100% backward compatibility:
- All original function signatures preserved
- CLI arguments unchanged
- Behavior identical to original implementation

The only difference: code is now organized, testable, and maintainable.

