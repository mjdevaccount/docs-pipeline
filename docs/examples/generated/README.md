# Generated PDF Examples

Professional documentation demonstrating the full capabilities of the docs-pipeline system across multiple document types and visual profiles.

## 🎯 Portfolio-Ready Examples

This directory contains **12 generated PDFs** (3 documents × 4 profiles) showcasing the complete range of capabilities, with **all CSS collision fixes applied** for production-quality output.

### ✨ Latest Improvements (Dec 2025)

All PDFs generated with the following enhancements:
- ✅ **CSS Collision Resolution** - Clean injection order, no style conflicts
- ✅ **Pandoc CSS Stripping** - Removed embedded style pollution
- ✅ **Profile-Specific Styling** - Colors controlled by CSS classes, not inline styles
- ✅ **Dark Theme Fix** - Full background color support via `-webkit-print-color-adjust`
- ✅ **Proper Margins** - CSS `@page` rules control margins (not hardcoded Python)
- ✅ **Font Stack Priority** - Profile CSS fonts load before Google Fonts
- ✅ **Centralized Pagination** - All page-break rules in `layout.css` (no duplicates)

### Document Types

#### 1. Advanced Markdown Showcase (`showcase-*.pdf`)
**Source:** `../advanced-markdown-showcase.md`

Comprehensive demonstration of all markdown capabilities:
- Complex Mermaid diagrams (flowcharts, sequence diagrams, data flows)
- Nested tables with multi-column formatting
- Multi-language code blocks (Python, JavaScript, YAML, Bash)
- Mathematical equations (inline and display math with KaTeX)
- Hierarchical lists, callouts, and special formatting

#### 2. Technical White Paper (`whitepaper-*.pdf`)
**Source:** `../technical-white-paper.md`

Production-quality technical white paper on event-driven microservices:
- Executive summary with business objectives
- Architecture patterns with C4 diagrams
- Performance benchmarks and comparison tables
- Real-world code examples (Python sagas, orchestration)
- Security considerations and best practices

#### 3. Product Requirements Document (`prd-*.pdf`)
**Source:** `../product-requirements-doc.md`

Enterprise PRD for a real-time collaboration platform:
- User personas and pain point analysis
- Detailed functional requirements with acceptance criteria
- System architecture diagrams
- Gantt charts and project roadmaps
- Competitive analysis matrices

### Visual Profiles

Each document is available in **4 distinct visual profiles:**

- **`-tech.pdf`** - Tech Whitepaper: Professional engineering documentation style (Blue accents, clean margins)
- **`-dark.pdf`** - Dark Pro: Modern dark theme for on-screen presentations (Dark navy background, light text)
- **`-minimalist.pdf`** - Minimalist: Clean, spacious architecture documentation (Maximum whitespace, subtle styling)
- **`-enterprise.pdf`** - Enterprise Blue: Corporate-friendly business documents (Corporate blue, structured layout)

### 📊 File Sizes

| Document | Tech | Dark Pro | Minimalist | Enterprise |
|----------|------|----------|------------|------------|
| **Showcase** | 977 KB | 1,175 KB | 677 KB | 862 KB |
| **White Paper** | 551 KB | 766 KB | 344 KB | 583 KB |
| **PRD** | 735 KB | 1,010 KB | 649 KB | 923 KB |

**Total Portfolio:** 9.9 MB across 12 professional PDFs

*Note: Dark Pro PDFs are larger due to full-page background color preservation and enhanced visual effects.*

## 🚀 Regenerate All Examples

The entire showcase is driven by a single pipeline configuration file:

```bash
# From repo root
python -m tools.docs_pipeline.cli --config docs-pipeline-showcase.yaml
```

This single command generates all 12 PDFs in one pass, demonstrating:
- ✅ Automated batch processing
- ✅ Consistent styling across profiles
- ✅ Reproducible build pipeline
- ✅ Production-ready workflow

### What Gets Generated

```
docs/examples/generated/
├── showcase-tech.pdf              # Markdown showcase - Tech Whitepaper
├── showcase-dark.pdf              # Markdown showcase - Dark Pro
├── showcase-minimalist.pdf        # Markdown showcase - Minimalist
├── showcase-enterprise.pdf        # Markdown showcase - Enterprise Blue
├── whitepaper-tech.pdf            # White paper - Tech Whitepaper
├── whitepaper-dark.pdf            # White paper - Dark Pro
├── whitepaper-minimalist.pdf      # White paper - Minimalist
├── whitepaper-enterprise.pdf      # White paper - Enterprise Blue
├── prd-tech.pdf                   # PRD - Tech Whitepaper
├── prd-dark.pdf                   # PRD - Dark Pro
├── prd-minimalist.pdf             # PRD - Minimalist
└── prd-enterprise.pdf             # PRD - Enterprise Blue
```

## 🎨 Manual Single-File Generation

Generate individual PDFs with specific profiles:

```bash
# Tech Whitepaper profile with cover page and TOC
python tools/pdf/md2pdf.py docs/examples/technical-white-paper.md \
  whitepaper-tech.pdf \
  --profile tech-whitepaper \
  --renderer playwright \
  --generate-cover \
  --generate-toc

# Dark Pro profile with cover page and TOC
python tools/pdf/md2pdf.py docs/examples/product-requirements-doc.md \
  prd-dark.pdf \
  --profile dark-pro \
  --renderer playwright \
  --generate-cover \
  --generate-toc

# Add --verbose flag to see CSS loading order and debug info
python tools/pdf/md2pdf.py docs/examples/advanced-markdown-showcase.md \
  showcase-enterprise.pdf \
  --profile enterprise-blue \
  --renderer playwright \
  --generate-cover \
  --generate-toc \
  --verbose
```

**Note:** Output files are automatically placed in `<repo>/output/` by default.

## 📊 What These Examples Demonstrate

**Content Variety:**
- ✅ Technical white papers (500+ lines)
- ✅ Product requirements documents (525+ lines)
- ✅ Comprehensive markdown showcases (456+ lines)
- ✅ Real-world professional content

**Technical Capabilities:**
- ✅ 15+ Mermaid diagrams across all documents
- ✅ Syntax-highlighted code blocks in 5+ languages
- ✅ Mathematical equations (KaTeX integration)
- ✅ Complex table formatting with cell styling
- ✅ Multi-page layouts with automatic pagination
- ✅ Professional typography and spacing
- ✅ Professional cover pages with metadata
- ✅ Auto-generated table of contents
- ✅ PDF bookmarks for navigation (36+ per document)

**Profile System:**
- ✅ **Tech Whitepaper** - Blue accents, clean margins, engineering focus
- ✅ **Dark Pro** - High contrast, modern aesthetic, screen-optimized (with full background color support)
- ✅ **Minimalist** - Maximum whitespace, subtle styling, architecture focus
- ✅ **Enterprise Blue** - Corporate colors, conservative styling, business focus

**Production Quality:**
- ✅ CSS collision resolution (4-source problem → 2-source clean solution)
- ✅ Proper CSS specificity (profile CSS controls styling, no inline overrides)
- ✅ Chromium PDF compliance (`-webkit-print-color-adjust: exact` for dark themes)
- ✅ Pandoc CSS isolation (embedded styles stripped before rendering)
- ✅ Font stack priority (profile fonts load before web fonts)
- ✅ Centralized pagination rules (no duplicates across profiles)

## 📖 Pipeline Configuration

The `docs-pipeline-showcase.yaml` configuration demonstrates best practices:

```yaml
workspaces:
  markdown-showcase:
    documents:
      - input: docs/examples/advanced-markdown-showcase.md
        output: docs/examples/generated/showcase-tech.pdf
        format: pdf
        renderer: playwright
        profile: tech-whitepaper
      # ... 3 more profiles
  
  white-paper:
    documents:
      # ... 4 profiles for white paper
  
  prd:
    documents:
      # ... 4 profiles for PRD
```

This approach enables:
- Version-controlled configuration
- Reproducible builds
- CI/CD integration
- Batch processing

