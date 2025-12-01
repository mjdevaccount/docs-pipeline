# Generated PDF Examples

Professional documentation demonstrating the full capabilities of the docs-pipeline system across multiple document types and visual profiles.

## 🎯 Portfolio-Ready Examples

### 1. Advanced Markdown Showcase

**Source:** `../advanced-markdown-showcase.md`  
**Output:** `advanced-markdown-showcase.pdf`

Comprehensive demonstration of all markdown capabilities including:
- Complex Mermaid diagrams (flowcharts, sequence diagrams, data flows)
- Nested tables with formatting
- Multi-language code blocks (Python, JavaScript, YAML, Bash)
- Mathematical expressions (inline and display math)
- Hierarchical lists and callouts

**Generate:**
```bash
python tools/pdf/md2pdf.py docs/examples/advanced-markdown-showcase.md \
  --output docs/examples/generated/advanced-markdown-showcase.pdf \
  --profile tech-whitepaper --renderer playwright
```

### 2. Technical White Paper

**Source:** `../technical-white-paper.md`  
**Output:** `technical-white-paper.pdf`

Production-quality technical white paper on event-driven microservices:
- Executive summary with business objectives
- Architecture patterns with C4 diagrams
- Performance benchmarks and comparison tables
- Real-world code examples (Python sagas, orchestration)
- Security considerations and best practices

**Generate:**
```bash
python tools/pdf/md2pdf.py docs/examples/technical-white-paper.md \
  --output docs/examples/generated/technical-white-paper.pdf \
  --profile tech-whitepaper --renderer playwright
```

### 3. Product Requirements Document

**Source:** `../product-requirements-doc.md`  
**Output:** `product-requirements-doc.pdf`

Enterprise PRD for a real-time collaboration platform:
- User personas and pain points
- Detailed functional requirements
- System architecture diagrams
- Gantt charts and roadmaps
- Competitive analysis matrices

**Generate:**
```bash
python tools/pdf/md2pdf.py docs/examples/product-requirements-doc.md \
  --output docs/examples/generated/product-requirements-doc.pdf \
  --profile enterprise-blue --renderer playwright
```

### 4. Architecture Specifications

**Multiple profile demonstrations:**
- `architecture-overview-tech.pdf` - Tech Whitepaper profile
- `architecture-overview-dark.pdf` - Dark Pro profile
- `architecture-overview-minimalist.pdf` - Minimalist profile
- `architecture-overview-enterprise.pdf` - Enterprise Blue profile

Same content, four completely different visual styles.

## 🎨 Multi-Profile Generation

Generate the same document in all four profiles:

```bash
# Tech Whitepaper (default)
python tools/pdf/md2pdf.py docs/examples/technical-white-paper.md \
  --output output/white-paper-tech.pdf --profile tech-whitepaper

# Dark Pro (modern)
python tools/pdf/md2pdf.py docs/examples/technical-white-paper.md \
  --output output/white-paper-dark.pdf --profile dark-pro

# Minimalist (clean)
python tools/pdf/md2pdf.py docs/examples/technical-white-paper.md \
  --output output/white-paper-minimal.pdf --profile minimalist

# Enterprise Blue (corporate)
python tools/pdf/md2pdf.py docs/examples/technical-white-paper.md \
  --output output/white-paper-enterprise.pdf --profile enterprise-blue
```

## 📊 What These Examples Demonstrate

**Content Variety:**
- ✅ Technical white papers
- ✅ Product requirements documents
- ✅ Architecture specifications
- ✅ Comprehensive markdown showcases

**Technical Capabilities:**
- ✅ Complex Mermaid diagrams (10+ diagram types)
- ✅ Syntax-highlighted code blocks
- ✅ Mathematical equations (KaTeX)
- ✅ Advanced table formatting
- ✅ Multi-page document layout
- ✅ Professional typography

**Visual Profiles:**
- ✅ Tech Whitepaper - Engineering documentation
- ✅ Dark Pro - Modern presentations
- ✅ Minimalist - Architecture docs
- ✅ Enterprise Blue - Business reports

## 🚀 Quick Start

Generate all examples:

```bash
# From repo root
python tools/pdf/md2pdf.py docs/examples/advanced-markdown-showcase.md --output docs/examples/generated/advanced-markdown-showcase.pdf
python tools/pdf/md2pdf.py docs/examples/technical-white-paper.md --output docs/examples/generated/technical-white-paper.pdf
python tools/pdf/md2pdf.py docs/examples/product-requirements-doc.md --output docs/examples/generated/product-requirements-doc.pdf
```

