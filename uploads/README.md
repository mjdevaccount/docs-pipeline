# Generated PDF Examples

Real documentation from this repository, converted to PDF using the docs-pipeline tools.

## Examples

All examples are actual documentation from this project, demonstrating:

- ✅ **Real-world content** (not fake examples)
- ✅ **Complex formatting** (code blocks, headings, lists)
- ✅ **Multiple document types** (architecture docs, READMEs, analysis)

### 1. SOLID Implementation Analysis

**Source:** `docs/development/pdf-solid-implementation.md`  

**Output:** `solid-implementation.pdf`

Deep-dive into SOLID principles in the PDF generation engine.

**Generate:**

```bash
docs-pdf ../../development/pdf-solid-implementation.md --output solid-implementation.pdf
```

### 2. Structurizr Code Review

**Source:** `docs/development/structurizr-solid-evaluation.md`  

**Output:** `structurizr-evaluation.pdf`

SOLID evaluation of the Structurizr integration tool.

**Generate:**

```bash
docs-pdf ../../development/structurizr-solid-evaluation.md --output structurizr-evaluation.pdf
```

## Quick Start

Generate all examples at once:

**From repo root:**

```bash
cd docs/examples/generated

# Generate PDFs
docs-pdf ../../development/pdf-solid-implementation.md --output solid-implementation.pdf
docs-pdf ../../development/structurizr-solid-evaluation.md --output structurizr-evaluation.pdf
```

## Why These Examples?

These documents showcase:

- **Technical depth** - Real architecture and design documentation
- **Variety** - Different document lengths and complexity
- **Production quality** - Content used in actual development
- **Dogfooding** - Using our own tool on our own docs

