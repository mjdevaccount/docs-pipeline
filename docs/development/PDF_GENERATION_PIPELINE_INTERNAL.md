# PDF Generation Pipeline - Internal Technical Documentation

**Purpose:** Complete technical reference for debugging and understanding the PDF generation pipeline. This document traces every step, decision point, and configuration option.

**Last Updated:** 2025-01-XX (after margin extraction and cover page width fixes)

---

## Table of Contents

1. [High-Level Architecture](#high-level-architecture)
2. [Complete Pipeline Flow](#complete-pipeline-flow)
3. [Step-by-Step Breakdown](#step-by-step-breakdown)
4. [Playwright PDF Rendering Phases](#playwright-pdf-rendering-phases)
5. [Decision Points & Configuration](#decision-points--configuration)
6. [File Locations & Dependencies](#file-locations--dependencies)
7. [Common Issues & Debugging](#common-issues--debugging)

---

## High-Level Architecture

The PDF generation system uses a **two-stage architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│ STAGE 1: Markdown → HTML Pipeline (tools/pdf/pipeline/)     │
│ - Preprocessing (metadata, diagrams, math)                  │
│ - Pandoc conversion (Markdown → HTML)                       │
│ - Post-processing (CSS stripping, metadata injection)        │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    HTML File (temporary)
                            ↓
┌─────────────────────────────────────────────────────────────┐
│ STAGE 2: HTML → PDF Rendering (tools/pdf/playwright_pdf/)  │
│ - Load HTML into Playwright/Chromium                       │
│ - Inject CSS, fonts, cover page, TOC                       │
│ - Analyze layout, scale diagrams                           │
│ - Generate PDF via Chromium print engine                   │
│ - Post-process (bookmarks, metadata)                       │
└─────────────────────────────────────────────────────────────┘
                            ↓
                    Final PDF File
```

**Key Design Decision:** Separation allows HTML to be generated once and rendered by multiple backends (Playwright, WeasyPrint, etc.)

---

## Complete Pipeline Flow

### Entry Point

**Canonical Command (Recommended):**
```bash
python -m tools.pdf.convert_final input.md output.pdf \
    --profile tech-whitepaper \
    --generate-cover \
    --generate-toc \
    --renderer playwright \
    --verbose
```

**Function:** `tools/pdf/convert_final.py::markdown_to_pdf()`

**Called from:**
- CLI: `python -m tools.pdf.convert_final` (canonical)
- CLI: `tools/pdf/cli/main.py` (alternative)
- Python API: Direct import `from tools.pdf.convert_final import markdown_to_pdf`
- Web demo: `web_demo.py`

**Flow:**
```python
markdown_to_pdf(md_file, output_pdf, renderer='playwright', **kwargs)
  → process_document(input_file, output_file, OutputFormat.PDF, **kwargs)
  → create_pdf_pipeline()
  → PipelineContext(input_file, output_file, work_dir, config=kwargs)
  → pipeline.execute(context)
```

---

## Step-by-Step Breakdown

### Step 1: Read Content
**File:** `tools/pdf/pipeline/steps/preprocessing.py::ReadContentStep`

**What it does:**
- Reads raw Markdown file from disk
- Stores in `context.raw_content`

**Decision points:**
- None (always reads file)

**Output:**
- `context.raw_content` = full markdown string

**Potential issues:**
- File encoding (assumes UTF-8)
- File not found → raises `PipelineError`

---

### Step 2: Metadata Extraction
**File:** `tools/pdf/pipeline/steps/preprocessing.py::MetadataExtractionStep`

**What it does:**
- Extracts YAML frontmatter from markdown (between `---` delimiters)
- Parses with PyYAML `safe_load()`
- Merges with CLI/config metadata (CLI takes precedence)
- Stores in `context.metadata` dict

**Decision points:**
- If frontmatter exists → extract it
- If CLI provides metadata → override frontmatter
- If neither → use defaults/empty

**Supported metadata fields:**
- `title`, `author`, `organization`, `date`
- `version`, `type`, `classification`
- `subtitle` (for cover page)

**Output:**
- `context.metadata` = dict with all metadata

**Potential issues:**
- Invalid YAML → PyYAML error (caught, continues with empty metadata)
- Duplicate keys → last one wins

---

### Step 3: Glossary Expansion (Optional)
**File:** `tools/pdf/pipeline/steps/preprocessing.py::GlossaryExpansionStep`

**What it does:**
- Loads glossary YAML file (if provided)
- Finds acronyms/terms in markdown
- Expands them (e.g., "MTM" → "Mark-to-Market (MTM)")

**Decision points:**
- Only runs if `glossary_file` in config
- Only runs if `include_glossary=True` in pipeline creation

**Output:**
- `context.preprocessed_markdown` = markdown with expanded terms

**Potential issues:**
- Glossary file not found → step skipped
- Circular references → could cause infinite loop (not currently handled)

---

### Step 4: Math Rendering (Optional)
**File:** `tools/pdf/pipeline/steps/preprocessing.py::MathRenderingStep`

**What it does:**
- Finds LaTeX math blocks (`$...$` and `$$...$$`)
- Pre-renders with KaTeX to HTML
- Replaces math blocks with rendered HTML

**Decision points:**
- Only runs if `include_math=True` in pipeline creation
- Uses KaTeX (not MathJax) for better PDF compatibility

**Output:**
- `context.preprocessed_markdown` = markdown with math rendered as HTML

**Potential issues:**
- KaTeX not installed → step skipped
- Invalid LaTeX → renders as error message

---

### Step 5: Diagram Rendering
**File:** `tools/pdf/pipeline/steps/diagram_step.py::DiagramRenderingStep`

**What it does:**
- Finds Mermaid code blocks (```mermaid ... ```)
- Renders each diagram to SVG using Mermaid-CLI
- Caches rendered diagrams (if `use_cache=True`)
- Replaces code blocks with `<img src="diagram.svg">` tags

**Decision points:**
- **Cache lookup:** If diagram hash exists in cache → use cached SVG
- **Render method:** Uses `mmdc` (Mermaid-CLI) command-line tool
- **Output format:** Always SVG (not PNG) for better quality

**Configuration:**
- `cache_dir`: Where to store cached diagrams
- `use_cache`: Enable/disable caching
- `theme_config`: Mermaid theme JSON file

**Output:**
- `context.preprocessed_markdown` = markdown with diagrams as image tags
- `context.svg_files` = list of generated SVG file paths

**Potential issues:**
- Mermaid-CLI not installed → diagrams render as code blocks
- Invalid Mermaid syntax → renders as error SVG
- Cache corruption → re-renders (no error)

**File locations:**
- Rendered diagrams: `cache_dir/` or `work_dir/`
- Cache index: `cache_dir/.mermaid_cache.json`

---

### Step 6: Pandoc Conversion
**File:** `tools/pdf/pipeline/steps/pandoc_step.py::PandocConversionStep`

**What it does:**
- Converts Markdown → HTML5 using Pandoc
- Uses Pandoc extensions (tables, fenced_code, etc.)
- Generates TOC (if enabled)
- Embeds rendered diagrams as images

**Decision points:**
- **Pandoc executable:** Searches PATH, then common install locations
- **Markdown format:** `markdown+extensions` (tables, fenced_code, etc.)
- **TOC generation:** Always enabled (we remove it later if needed)
- **Syntax highlighting:** Uses `highlight_style` config (default: 'pygments')

**Pandoc command:**
```bash
pandoc input.md \
  -f markdown+extensions \
  -t html5 \
  --standalone \
  --toc \
  --toc-depth=3 \
  --highlight-style=pygments \
  --mathjax \
  -o output.html
```

**Output:**
- `context.html_content` = full HTML string
- `context.html_file` = Path to HTML file (written to `work_dir/output.html`)

**Potential issues:**
- Pandoc not installed → raises `PipelineError`
- Pandoc version incompatibility → may fail silently
- Large documents → slow conversion

**File locations:**
- HTML output: `work_dir/output.html`

---

### Step 7: CSS Stripping
**File:** `tools/pdf/pipeline/steps/postprocessing.py::CSSStrippingStep`

**What it does:**
- Removes inline styles from Pandoc-generated HTML
- Keeps only class names (for CSS styling)

**Decision points:**
- Always runs (no config option)
- Uses regex to find and remove `style="..."` attributes

**Output:**
- `context.html_content` = HTML with inline styles removed

**Potential issues:**
- May remove styles we want to keep (rare)
- Regex edge cases with nested quotes

---

### Step 8: Title Page Injection (Skipped for Playwright)
**File:** `tools/pdf/pipeline/steps/postprocessing.py::TitlePageInjectionStep`

**What it does:**
- For WeasyPrint: Injects title page HTML before `<body>`
- For Playwright: **SKIPPED** (Playwright handles cover page separately)

**Decision points:**
- Checks `context.get_config('renderer')`
- If `renderer == 'playwright'` → skips this step
- Otherwise → injects title page HTML

**Output:**
- `context.html_content` = HTML with title page (if not Playwright)

---

### Step 9: Metadata Injection
**File:** `tools/pdf/pipeline/steps/postprocessing.py::MetadataInjectionStep`

**What it does:**
- Injects metadata as HTML `<meta>` tags in `<head>`
- Used by Playwright to read document metadata

**Decision points:**
- Only runs if `renderer == 'playwright'`
- Tries new `HTMLMetadataInjector` first, falls back to manual injection

**Output:**
- `context.html_content` = HTML with `<meta>` tags in `<head>`

**Potential issues:**
- Metadata injector may fail → falls back to manual injection
- Missing `</head>` tag → metadata appended to end (may not work)

**Meta tags injected:**
```html
<meta name="author" content="...">
<meta name="organization" content="...">
<meta name="date" content="...">
<meta name="type" content="...">
<meta name="classification" content="...">
<meta name="version" content="...">
```

---

### Step 10: PDF Rendering
**File:** `tools/pdf/pipeline/steps/rendering_step.py::PdfRenderingStep`

**What it does:**
- Chooses renderer (Playwright or WeasyPrint)
- Builds renderer configuration
- Calls renderer to generate PDF

**Decision points:**
- **Renderer selection:**
  - `config.get('renderer', 'playwright')` → preferred renderer
  - Falls back to WeasyPrint if Playwright unavailable
- **Profile/CSS selection:**
  - If `css_file` provided → use it
  - Else if `profile` provided → load CSS from profile
  - Else → no custom CSS

**Configuration built:**
```python
RenderConfig(
    html_file=context.html_file,
    output_file=context.output_file,
    css_file=Path(css_file) if css_file else None,
    generate_toc=context.get_config('generate_toc', False),
    generate_cover=context.get_config('generate_cover', False),
    # ... metadata fields from context.metadata
)
```

**Output:**
- `context.output_file` = final PDF file

**Potential issues:**
- Renderer not available → falls back to WeasyPrint
- Profile not found → continues without custom CSS
- PDF generation fails → raises `PipelineError`

---

## Playwright PDF Rendering Phases

**File:** `tools/pdf/playwright_pdf/pipeline.py::generate_pdf()`

Once the HTML is ready, Playwright takes over with its own 7-phase pipeline:

### Phase 1: Load HTML into Playwright Page
**Function:** `tools/pdf/playwright_pdf/browser.py::open_page()`

**What it does:**
- Launches Chromium browser (headless)
- Creates new page
- Sets viewport to 1920×1080 (for accurate measurements)
- Loads HTML file via `file://` URL
- Waits for `networkidle` state

**Decision points:**
- Browser args: `--disable-gpu`, `--no-sandbox`, `--disable-dev-shm-usage`
- Viewport size: Fixed 1920×1080 (doesn't affect PDF, but needed for measurements)

**Output:**
- Playwright `Page` object ready for manipulation

**Potential issues:**
- Playwright not installed → raises exception
- HTML file not found → navigation error
- Network resources → may timeout (diagrams, fonts)

---

### Phase 2: Extract Metadata from HTML
**Location:** `pipeline.py` lines 56-94

**What it does:**
- Reads `<meta>` tags from HTML `<head>`
- Extracts: author, organization, date, type, classification, version
- Updates `config` object with extracted values (if not already set)

**Decision points:**
- If config already has value → don't override
- If HTML has value → use it
- If neither → leave as None

**Output:**
- `config` object updated with metadata

---

### Phase 3: Wait for Resources
**Location:** `pipeline.py` lines 96-107

**What it does:**
- Waits for `networkidle` (all network requests complete)
- Waits for `document.fonts.ready` (fonts loaded)
- Waits for SVG elements to render (timeout 5s, continues if none found)
- Additional 1s buffer for layout stabilization

**Decision points:**
- SVG timeout: 5 seconds (then continues)
- Layout buffer: 1 second (hardcoded)

**Potential issues:**
- Slow network → may timeout
- Missing fonts → may render with fallbacks

---

### Phase 4: Inject CSS and Fonts
**Location:** `pipeline.py` lines 109-148

**What it does:**
1. **Inject profile CSS** (if `config.css_file` provided)
   - File: `tools/pdf/playwright_pdf/styles.py::inject_custom_css()`
   - Adds `<style>` tag with CSS content
   - **CRITICAL:** This sets `@page` margins that affect entire document

2. **Inject Google Fonts** (if requested or no profile CSS)
   - File: `tools/pdf/playwright_pdf/styles.py::inject_fonts()`
   - Loads fonts from Google Fonts API
   - Waits for `document.fonts.ready`

3. **Inject pagination CSS**
   - File: `tools/pdf/playwright_pdf/styles.py::inject_pagination_css()`
   - Loads `tools/pdf/styles/layout.css`
   - Handles page breaks, diagram grouping

**Decision points:**
- **CSS loading order:** Profile CSS → Google Fonts → Pagination CSS
- **Font injection:** Only if `font_families` provided OR no profile CSS
- **Pagination CSS:** Always injected last

**CSS files loaded:**
- Profile CSS: `tools/pdf/styles/{profile}.css` (e.g., `tech-whitepaper.css`)
- Layout CSS: `tools/pdf/styles/layout.css`
- Google Fonts: Loaded from CDN

**Potential issues:**
- CSS file not found → continues without it
- Google Fonts network error → falls back to system fonts
- CSS syntax errors → may break rendering

---

### Phase 5: Remove Pandoc TOC (if generating our own)
**Location:** `pipeline.py` lines 150-159

**What it does:**
- Finds `<nav id="TOC">` or `<div id="TOC">` in HTML
- Removes it (we generate our own TOC)

**Decision points:**
- Only runs if `config.generate_toc == True`

---

### Phase 6: Extract Margins from CSS
**Location:** `pipeline.py` lines 161-172

**What it does:**
- Parses CSS file to find `@page { margin: ... }` rule
- **Excludes pseudo-selectors** like `@page:first`, `@page:left`, `@page:right`
- Extracts margin values (top, right, bottom, left)
- Stores in `margin_config` dict
- **Logs symmetry check** (warns if left ≠ right)

**Function:** `tools/pdf/playwright_pdf/utils.py::extract_margins_from_css()`

**Parsing logic:**
- Finds `@page` rule with regex: `@page(?!:)(?!\/)\s*\{` (excludes pseudo-selectors)
- Finds `margin:` property
- Parses CSS margin shorthand:
  - 1 value → all sides same
  - 2 values → top/bottom, left/right
  - 3 values → top, left/right, bottom
  - 4 values → top, right, bottom, left

**Decision points:**
- If CSS file provided → extract margins
- **Ignores `@page:first` rules** (Playwright applies margins to all pages, not just first)
- If extraction fails → use `DEFAULT_MARGINS` = `{'top': '2cm', 'right': '1.8cm', 'bottom': '2cm', 'left': '1.8cm'}`
- **Symmetry check:** Warns if left margin ≠ right margin (may indicate intentional asymmetry)

**Output:**
- `margin_config` = dict with margin values (e.g., `{'top': '2.5cm', 'right': '2cm', 'bottom': '2cm', 'left': '2cm'}`)
- Verbose logging: `[INFO] Using margins from CSS: {...}`
- Symmetry check: `[INFO] Margins are symmetric: left=2cm, right=2cm` or `[WARN] Margins are asymmetric: ...`

**Potential issues:**
- CSS parsing fails → uses defaults (may cause margin mismatch)
- **Multiple `@page` rules → uses base `@page` rule (not `@page:first`)**
- Invalid margin syntax → parsing fails
- **Bug fix (2025-01-XX):** Previously would match `@page:first` and get wrong margins; now correctly excludes pseudo-selectors

---

### Phase 7: Inject Cover Page
**Location:** `pipeline.py` lines 174-177

**Function:** `tools/pdf/playwright_pdf/decorators/cover.py::inject_cover_page()`

**What it does:**
- Generates cover page HTML
- Inserts at beginning of `<body>`
- Uses **dynamic negative margins** to extend into page margin area

**Cover page structure:**
```html
<div class="cover-page-wrapper" style="
    width: calc(100% + {margin_left} + {margin_right});
    height: calc(100vh + {margin_top});
    min-height: 11in;
    margin-top: -{margin_top};
    margin-left: -{margin_left};
    margin-right: -{margin_right};
    margin-bottom: 0;
    padding: 2.5in 0 1.5in 0;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    box-sizing: border-box;
    page-break-after: always;
    break-after: page;
">
    <!-- Logo, classification, title, subtitle, author, date, version -->
</div>
```

**Full-bleed calculation:**
- **Width:** `calc(100% + {margin_left} + {margin_right})` - **CRITICAL** for proper centering
  - `100%` = body content width (excludes margins)
  - Adding margins makes it span FULL page width
  - Flexbox centers children across FULL page width (not just body width)
- **Negative margins:** Pulls cover page back into margin space
- **Why calc() is needed:** Without it, flexbox centers within body width only, causing left-alignment

**Decision points:**
- Only runs if `config.generate_cover == True`
- **Margin calculation:** Uses `margin_config` passed from Phase 6
- **Centering:** Uses flexbox + `width: 100%` on children + `text-align: center`

**Cover page elements:**
1. Logo (if `config.logo_path` provided) → base64 encoded image
2. Classification badge (if `config.classification` provided)
3. Title (from `config.title`)
4. Divider line (gradient)
5. Subtitle/Organization (from `config.subtitle` or `config.organization`)
6. Author + Date (from `config.author` and `config.date`)
7. Version/Type (if provided)

**Potential issues:**
- Logo file not found → logo omitted (no error)
- Negative margins don't match CSS margins → cover page misaligned
- Centering fails → content appears left-aligned

**Recent fixes (2025-01-XX):**
1. **Margin extraction:** Now correctly excludes `@page:first` pseudo-selectors (was matching wrong rule)
2. **Cover page width:** **CRITICAL** - Must use `calc(100% + margins)` to span full page width
   - Without calc(), flexbox centers within body width only → left-aligned text
   - With calc(), flexbox centers across full page width → properly centered
3. **Dynamic margins:** Changed from hardcoded `-1.8cm` margins to dynamic margins from CSS extraction
4. **Centering:** Added explicit `width: 100%` on all children for reliable centering
5. **Padding:** Changed from `2.5in 1in 1.5in 1in` to `2.5in 0 1.5in 0` with children having `padding: 0 1in`

**Note:** The width calculation was initially "fixed" incorrectly. The real bugs were margin extraction and hardcoded margins. The `calc(100% + margins)` approach is correct and necessary for proper centering.

---

### Phase 8: Inject Table of Contents
**Location:** `pipeline.py` lines 179-181

**Function:** `tools/pdf/playwright_pdf/decorators/toc.py::inject_toc()`

**What it does:**
- Finds all `<h1>`, `<h2>`, `<h3>` headings (excluding cover page)
- Generates TOC HTML with links
- Inserts after cover page (or at beginning if no cover)

**TOC structure:**
```html
<div class="toc-wrapper" style="page-break-after: always;">
    <h1>Table of Contents</h1>
    <ul>
        <li><a href="#heading-id">Heading Text</a></li>
        ...
    </ul>
</div>
```

**Decision points:**
- Only runs if `config.generate_toc == True`
- Skips headings inside `.cover-page-wrapper`
- Indentation: `(level - 1) * 20px`

**Potential issues:**
- No headings found → TOC empty (but still inserted)
- Heading IDs missing → generates IDs like `heading-0`, `heading-1`

---

### Phase 9: Measure Page Dimensions
**Location:** `pipeline.py` lines 186-209

**Function:** `tools/pdf/playwright_pdf/page_measurements.py::measure_page_dimensions()`

**What it does:**
- Measures actual header/footer heights by creating test elements
- Calculates page dimensions based on format (A4, Letter, Legal)
- Calculates content area (page size - margins - header - footer)

**Measurement process:**
1. Creates hidden container with header/footer HTML
2. Measures `offsetHeight` of header/footer elements
3. Parses margin values from `margin_config` (converts cm/in to pixels)
4. Calculates page size from format (A4 = 794×1122px at 96dpi)

**Decision points:**
- Page format: From `config.page_format` (default: 'A4')
- DPI: Assumes 96dpi for pixel calculations
- Margin parsing: Supports `cm`, `in`, `mm`, `px` units

**Output:**
- `PageMeasurements` object with:
  - `page_width`, `page_height`
  - `margin_top`, `margin_right`, `margin_bottom`, `margin_left`
  - `header_height`, `footer_height`
  - `content_width`, `content_height`
  - `available_height` (content_height - header - footer)

**Potential issues:**
- Header/footer measurement fails → uses default heights
- Page format not recognized → falls back to A4
- Margin unit not supported → assumes inches

---

### Phase 10: Build Header/Footer Templates
**Location:** `pipeline.py` lines 189-199

**Function:** `tools/pdf/playwright_pdf/pdf_renderer.py::build_header_footer()`

**What it does:**
- Builds HTML templates for running headers/footers
- Uses Playwright's `display_header_footer` feature

**Header template:**
```html
<div style="font-size: 9px; text-align: center; padding: 8px 20px; ...">
    {title} | {organization}
</div>
```

**Footer template:**
```html
<div style="font-size: 9px; text-align: center; padding: 8px 20px; ...">
    {author} | {date} | Page <span class="pageNumber"></span> of <span class="totalPages"></span>
</div>
```

**Decision points:**
- Dark mode: Detected from profile name or CSS file
- Colors: Different for dark vs light mode
- Placeholder filtering: Removes placeholder values like "Organization", "Author Name"

**Potential issues:**
- Header/footer too tall → overlaps content
- Placeholder values not filtered → shows "Organization" in header

---

### Phase 11: Analyze Layout
**Location:** `pipeline.py` line 214

**Function:** `tools/pdf/playwright_pdf/dom_analyzer.py::analyze_layout()`

**What it does:**
- Scans DOM for headings and diagrams
- Groups headings with their associated diagrams
- Measures diagram dimensions
- Calculates if diagrams overflow page boundaries
- Detects page break issues

**Analysis process:**
1. Finds all headings (`<h1>` through `<h6>`)
2. For each heading, finds following diagrams (SVG or IMG)
3. Groups into "diagram blocks" (heading + diagrams that shouldn't split)
4. Measures total height of each block
5. Compares to `available_height` from measurements
6. Calculates overflow ratios

**Output:**
- `LayoutAnalysis` object with:
  - `diagram_blocks`: List of blocks with overflow info
  - `heading_groups`: Grouped headings for TOC
  - `total_pages`: Estimated page count

**Decision points:**
- Diagram detection: Looks for `<svg>`, `<img>`, `<figure>` elements
- Grouping: Diagrams belong to preceding heading until next heading
- Overflow threshold: Block height > `available_height` = overflow

**Potential issues:**
- Large diagrams → detected as overflow (will be scaled)
- Missing measurements → uses defaults (may be inaccurate)

---

### Phase 12: Compute Scaling Decisions
**Location:** `pipeline.py` line 217

**Function:** `tools/pdf/playwright_pdf/layout_transformer.py::compute_scaling()`

**What it does:**
- Analyzes overflow from Phase 11
- Decides which diagrams need scaling
- Calculates scale factors to fit diagrams on page
- Determines if page breaks are needed

**Scaling logic:**
1. For each diagram block with overflow:
   - Calculate scale factor: `available_height / block_height`
   - Apply minimum scale limits (don't scale below 0.15x)
   - Decide: scale diagram only, or scale entire block
2. For severe overflow (>2.5x):
   - Allow more aggressive scaling (down to 0.10x)
3. For blocks that still won't fit:
   - Force page break before block

**Decision points:**
- **Scale factor calculation:** Conservative (leaves buffer)
- **Minimum scale:** 0.15x for moderate overflow, 0.10x for severe
- **Page break:** Only if scaling won't help

**Output:**
- List of `ScalingDecision` objects:
  - `heading_id`: Which heading's diagram to scale
  - `scale_factor`: How much to scale (e.g., 0.75 = 75% size)
  - `force_page_break`: Whether to force break before

**Potential issues:**
- Over-aggressive scaling → diagrams too small to read
- Under-scaling → diagrams still overflow
- Page break decisions → may create awkward page breaks

---

### Phase 13: Apply Scaling
**Location:** `pipeline.py` lines 218-220

**Function:** `tools/pdf/playwright_pdf/layout_transformer.py::apply_scaling()`

**What it does:**
- Applies scaling decisions from Phase 12
- Mutates DOM: adds `data-scaled` attribute, applies CSS transforms
- Wraps diagrams in containers if needed

**Scaling implementation:**
1. Finds heading by ID
2. Finds associated diagram (SVG or IMG)
3. Calculates new dimensions: `original_size * scale_factor`
4. Applies CSS transform: `transform: scale(scale_factor)`
5. Sets `data-scaled="true"` attribute
6. Wraps in container if needed for page break control

**Decision points:**
- Transform origin: `top center` (scales from top, centered)
- Container wrapping: Only if page break needed

**Potential issues:**
- Transform causes clipping → diagram cut off
- Scale factor calculation error → wrong size
- DOM mutation fails → diagram not scaled

---

### Phase 14: Post-Scaling Analysis (Optional)
**Location:** `pipeline.py` lines 229-274

**What it does:**
- Re-analyzes layout after scaling (Phase 11 again)
- Checks if new problems appeared
- Applies additional scaling if needed

**Decision points:**
- Only runs if first scaling pass found issues
- Only scales diagrams that weren't already scaled
- Prevents infinite loops (max 2 passes)

**Potential issues:**
- Infinite loop if scaling creates new problems (prevented by max 2 passes)
- Over-scaling → diagrams become too small

---

### Phase 15: Add Watermark (Optional)
**Location:** `pipeline.py` lines 222-224

**Function:** `tools/pdf/playwright_pdf/decorators/watermark.py::add_watermark()`

**What it does:**
- Adds watermark text to every page
- Uses CSS `::before` pseudo-element on body

**Decision points:**
- Only runs if `config.watermark` provided
- Watermark appears on ALL pages (including cover)

---

### Phase 16: Extract Headings for Bookmarks
**Location:** `pipeline.py` line 277

**Function:** `tools/pdf/playwright_pdf/postprocess.py::extract_headings_from_page()`

**What it does:**
- Scans DOM for headings
- Extracts heading text, level, and ID
- Builds bookmark structure for PDF

**Output:**
- List of heading dicts: `[{'text': '...', 'level': 1, 'id': '...'}, ...]`

---

### Phase 17: Render PDF
**Location:** `pipeline.py` lines 282-291

**Function:** `tools/pdf/playwright_pdf/pdf_renderer.py::render_pdf()`

**What it does:**
- Calls Playwright's `page.pdf()` method
- Passes header/footer templates, margins, page format
- Generates PDF file

**Playwright PDF options:**
```python
{
    'format': 'A4',  # or 'Letter', 'Legal'
    'print_background': True,
    'display_header_footer': True,
    'header_template': header_html,
    'footer_template': footer_html,
    'margin': {
        'top': '2.5cm',
        'right': '2cm',
        'bottom': '2cm',
        'left': '2cm'
    }
}
```

**Decision points:**
- Page format: From `config.page_format` (default: 'A4')
- Margins: From `margin_config` (extracted in Phase 6)
- Header/footer: Always enabled (can't disable for first page only)

**Debug logging (if verbose):**
- `[OK] Passing margins to page.pdf(): {...}` - Shows exact margins being passed
- `[OK] Page format: A4` - Shows page format
- `[OK] Generating PDF...` - Confirms PDF generation started

**Potential issues:**
- Header/footer appears on cover page (Playwright limitation)
- Margin mismatch → content misaligned
- PDF generation fails → returns False

**CRITICAL:** The margins passed to `page.pdf()` MUST match the `@page` margins in CSS, otherwise content will be misaligned. Use verbose mode to verify margin extraction and pass-through match.

---

### Phase 18: Post-Process PDF (Outside Browser)
**Location:** `pipeline.py` lines 296-308

**Functions:**
- `tools/pdf/playwright_pdf/postprocess.py::add_bookmarks_to_pdf()`
- `tools/pdf/playwright_pdf/postprocess.py::embed_metadata()`

**What it does:**
1. **Add bookmarks:** Uses PyPDF2 to add navigation bookmarks
2. **Embed metadata:** Sets PDF metadata (title, author, subject, keywords)

**Decision points:**
- Only runs if headings found (for bookmarks)
- Only runs if metadata provided (for embedding)

**Potential issues:**
- PyPDF2 not installed → bookmarks/metadata skipped
- PDF file locked → can't modify
- Invalid metadata → may be ignored

---

## Decision Points & Configuration

### Configuration Hierarchy (Highest to Lowest Priority)

1. **CLI arguments** (`tools/pdf/cli/main.py`)
2. **Pipeline config** (`context.config` dict)
3. **YAML frontmatter** (in markdown file)
4. **Defaults** (hardcoded in code)

### Key Configuration Options

| Option | Default | Location | Used By |
|--------|---------|----------|---------|
| `renderer` | `'playwright'` | CLI/config | `PdfRenderingStep` |
| `profile` | `None` | CLI/config | `PdfRenderingStep` → CSS selection |
| `css_file` | `None` | CLI/config | `PdfRenderingStep` → CSS injection |
| `generate_cover` | `False` | CLI/config | `PdfRenderingStep` → Cover injection |
| `generate_toc` | `False` | CLI/config | `PdfRenderingStep` → TOC injection |
| `watermark` | `None` | CLI/config | `PdfRenderingStep` → Watermark |
| `page_format` | `'A4'` | CLI/config | `PdfRenderingStep` → PDF format |
| `cache_dir` | `None` | CLI/config | `DiagramRenderingStep` |
| `use_cache` | `True` | CLI/config | `DiagramRenderingStep` |
| `verbose` | `False` | CLI/config | All steps |

### Profile System

**Location:** `tools/pdf/config/profiles.py`

**Profiles available:**
- `tech-whitepaper` → `tools/pdf/styles/tech-whitepaper.css`
- `dark-pro` → `tools/pdf/styles/dark-pro.css`
- `enterprise-blue` → `tools/pdf/styles/enterprise-blue.css`
- `minimalist` → `tools/pdf/styles/minimalist.css`

**Profile selection:**
1. If `css_file` provided → use it (ignore profile)
2. Else if `profile` provided → load CSS from profile
3. Else → no custom CSS (uses browser defaults)

---

## File Locations & Dependencies

### Core Pipeline Files

```
tools/pdf/
├── pipeline/
│   ├── __init__.py              # Pipeline factory functions
│   ├── base.py                   # PipelineContext, PipelineStep, Pipeline
│   ├── config.py                 # OutputFormat enum
│   └── steps/
│       ├── preprocessing.py      # ReadContent, Metadata, Glossary, Math
│       ├── diagram_step.py       # Diagram rendering
│       ├── pandoc_step.py        # Pandoc conversion
│       ├── postprocessing.py     # CSS stripping, metadata injection
│       └── rendering_step.py    # PDF/DOCX/HTML rendering
│
├── playwright_pdf/
│   ├── pipeline.py               # Main Playwright PDF generation
│   ├── browser.py                # Browser lifecycle
│   ├── config.py                 # PdfGenerationConfig
│   ├── dom_analyzer.py           # Layout analysis
│   ├── layout_transformer.py     # Scaling decisions & application
│   ├── page_measurements.py      # Page dimension measurement
│   ├── pdf_renderer.py           # PDF rendering (page.pdf call)
│   ├── postprocess.py            # Bookmarks, metadata embedding
│   ├── styles.py                 # CSS/font injection
│   ├── utils.py                  # Margin extraction, dark mode detection
│   └── decorators/
│       ├── cover.py              # Cover page generation
│       ├── toc.py                # TOC generation
│       └── watermark.py         # Watermark injection
│
├── styles/
│   ├── layout.css                # Pagination rules (page breaks)
│   ├── tech-whitepaper.css       # Tech whitepaper profile
│   ├── dark-pro.css              # Dark pro profile
│   ├── enterprise-blue.css       # Enterprise blue profile
│   └── minimalist.css            # Minimalist profile
│
└── renderers/
    ├── base.py                   # PdfRenderer base class
    ├── playwright_wrapper.py     # Playwright renderer wrapper
    └── weasyprint_renderer.py    # WeasyPrint renderer
```

### Temporary Files

**Work directory:** `tempfile.mkdtemp(prefix='doc_')`

**Files created:**
- `work_dir/output.html` - Pandoc-generated HTML
- `work_dir/preprocessed.md` - Markdown after preprocessing
- `work_dir/*.svg` - Rendered diagrams (if not cached)
- `cache_dir/.mermaid_cache.json` - Diagram cache index
- `cache_dir/*.svg` - Cached diagram renders

### External Dependencies

**Required:**
- `pandoc` - Markdown → HTML conversion
- `playwright` (Python) - Browser automation
- `chromium` (via Playwright) - PDF rendering engine

**Optional:**
- `mmdc` (Mermaid-CLI) - Diagram rendering
- `weasyprint` - Alternative PDF renderer
- `PyPDF2` - PDF post-processing (bookmarks, metadata)

---

## Common Issues & Debugging

### Issue: Margins Asymmetric / Content Misaligned

**Symptoms:**
- Left margin different from right margin
- Content appears shifted left or right
- Cover page misaligned

**Root causes:**
1. **CSS margin mismatch:** `@page` margins in CSS don't match margins passed to `page.pdf()`
   - **Fix:** Ensure `extract_margins_from_css()` correctly parses CSS
   - **Check:** `margin_config` in verbose output should match CSS file
   - **Recent fix (2025-01-XX):** Now correctly excludes `@page:first` rules that were causing wrong margin extraction

2. **Hardcoded margins:** Cover page or other elements use hardcoded negative margins
   - **Fix:** Use dynamic margins from `margin_config`
   - **Recent fix (2025-01-XX):** Cover page now uses `margin_config` instead of hardcoded `-1.8cm`

3. **Cover page width calculation:** Using `width: 100%` causes left-alignment
   - **Fix:** Use `calc(100% + margins)` to span full page width for proper centering
   - **Why:** `100%` = body width only; flexbox centers within that, not full page
   - **Check:** Cover page HTML should have `width: calc(100% + {margin_left} + {margin_right})`

4. **Body width constraint:** Body element has `max-width` or fixed width
   - **Check:** CSS file for `body { max-width: ... }` or `width: ... }`
   - **Fix:** Remove width constraints or adjust

**Debug steps:**
1. Enable verbose mode: `verbose=True`
2. Check margin extraction: Look for `[INFO] Using margins from CSS: {...}`
3. Check PDF margins: Look for `[MEASURE] Margins: top=..., right=..., left=...`
4. Verify margins match: Left should equal right (unless intentionally asymmetric)

---

### Issue: Cover Page Not Centered

**Symptoms:**
- Cover page content left-aligned
- Title, author, etc. not centered

**Root causes:**
1. **Cover page width:** Using `width: 100%` causes left-alignment (centers within body width only)
   - **Fix:** Use `calc(100% + margins)` to span full page width
   - **Why:** Flexbox `align-items: center` centers children within the element's width
   - If width = body width (100%), children center within body → appears left-aligned on page
   - If width = full page (calc(100% + margins)), children center across full page → properly centered
   - **Recent fix (2025-01-XX):** Reverted to `calc(100% + margins)` after initial incorrect fix

2. **Flexbox alignment:** `align-items: center` doesn't work if children have fixed width
   - **Fix:** Use `width: 100%` on children + `text-align: center`
   - **Recent fix:** Added explicit width and text-align to all cover elements

3. **Negative margins:** Negative margins not matching CSS margins
   - **Fix:** Use dynamic margins from `margin_config`
   - **Recent fix:** Cover page now uses `margin_config` for negative margins

**Debug steps:**
1. Check cover page HTML: Look for `cover-page-wrapper` in verbose output
2. Check computed styles: Use browser DevTools on generated HTML
3. Verify margins: Ensure negative margins match CSS margins

---

### Issue: Diagrams Overflow Page

**Symptoms:**
- Diagrams cut off at page boundaries
- Diagrams too large for page

**Root causes:**
1. **Scaling not applied:** Layout analysis didn't detect overflow
   - **Check:** Look for `[ANALYZE]` output in verbose mode
   - **Fix:** Ensure `analyze_layout()` runs and detects overflow

2. **Scaling too conservative:** Scale factor not aggressive enough
   - **Check:** Look for `[SCALE]` output in verbose mode
   - **Fix:** Adjust minimum scale limits in `layout_transformer.py`

3. **Page measurements wrong:** `available_height` calculation incorrect
   - **Check:** Look for `[MEASURE] Available height: ...` in verbose mode
   - **Fix:** Verify header/footer heights and margins are correct

**Debug steps:**
1. Enable verbose mode
2. Check analysis output: Look for overflow ratios
3. Check scaling decisions: Look for scale factors applied
4. Check measurements: Verify available height is reasonable

---

### Issue: Header/Footer on Cover Page

**Symptoms:**
- Running header/footer appears on cover page
- Should only appear on content pages

**Root cause:**
- **Playwright limitation:** `display_header_footer: true` applies to ALL pages
- No built-in way to disable for first page only

**Workarounds:**
1. **Negative margins:** Cover page uses negative margins to extend into header area
   - **Current approach:** Cover page has `margin-top: -{margin_top}` to mask header
   - **Limitation:** Header still renders, just covered by content

2. **Separate PDF generation:** Generate cover page separately, merge PDFs
   - **Not implemented:** Would require PDF merging library

**Status:** Known limitation, no perfect solution

---

### Issue: Profile CSS Not Applied

**Symptoms:**
- PDF doesn't match profile styling
- Default browser styles used instead

**Root causes:**
1. **Profile not found:** Profile name doesn't match available profiles
   - **Check:** Profile name in config vs. available profiles
   - **Fix:** Use correct profile name or provide `css_file` directly

2. **CSS file not found:** Profile CSS file missing
   - **Check:** `tools/pdf/styles/{profile}.css` exists
   - **Fix:** Ensure CSS file exists or use different profile

3. **CSS injection failed:** CSS not injected into page
   - **Check:** Look for `[INFO] Loaded custom CSS: ...` in verbose mode
   - **Fix:** Ensure `inject_custom_css()` runs successfully

**Debug steps:**
1. Enable verbose mode
2. Check CSS loading: Look for CSS loading order output
3. Check profile resolution: Look for profile → CSS file mapping
4. Verify CSS file exists: Check file system

---

### Issue: Diagrams Not Rendered

**Symptoms:**
- Mermaid code blocks appear as code instead of diagrams
- Missing diagram images

**Root causes:**
1. **Mermaid-CLI not installed:** `mmdc` command not found
   - **Check:** Run `mmdc --version` in terminal
   - **Fix:** Install Mermaid-CLI: `npm install -g @mermaid-js/mermaid-cli`

2. **Diagram rendering failed:** Mermaid syntax error or rendering error
   - **Check:** Look for diagram rendering errors in verbose output
   - **Fix:** Fix Mermaid syntax or check Mermaid-CLI logs

3. **Image paths wrong:** Diagrams rendered but paths incorrect
   - **Check:** Look for `context.svg_files` in debug output
   - **Fix:** Ensure diagram paths are relative to HTML file

**Debug steps:**
1. Enable verbose mode
2. Check diagram rendering: Look for `[Diagram Rendering]` output
3. Check SVG files: Verify SVG files exist in work directory
4. Check HTML: Verify `<img>` tags have correct `src` paths

---

## Debugging Checklist

When debugging PDF generation issues:

1. **Use canonical command:** `python -m tools.pdf.convert_final input.md output.pdf --verbose --renderer playwright`
2. **Enable verbose mode:** `--verbose` flag shows all steps, margin extraction, and pass-through
3. **Check pipeline steps:** Look for step failures in output
4. **Verify file paths:** Ensure all files exist and paths are correct
5. **Check margins:** 
   - Look for `[INFO] Using margins from CSS: {...}` 
   - Look for `[INFO] Margins are symmetric: ...` or `[WARN] Margins are asymmetric: ...`
   - Look for `[OK] Passing margins to page.pdf(): {...}`
   - Verify all three match
6. **Check CSS loading:** Verify CSS files are loaded in correct order
7. **Check measurements:** Verify page dimensions and available height
8. **Check scaling:** Verify diagrams are detected and scaled if needed
9. **Check browser:** Verify Playwright/Chromium is working
10. **Check dependencies:** Verify all external tools are installed
11. **Check temp files:** Inspect generated HTML and intermediate files

---

## Key Takeaways

1. **Canonical command:** Use `python -m tools.pdf.convert_final` for consistency
2. **Two-stage pipeline:** Markdown → HTML (Pandoc) → PDF (Playwright)
3. **Margin matching critical:** CSS `@page` margins must match `page.pdf()` margins
4. **Margin extraction fix:** Now correctly excludes `@page:first` pseudo-selectors
5. **Cover page width fix:** Uses `calc(100% + margins)` to span full page width for proper centering
6. **Cover page uses dynamic margins:** No more hardcoded `-1.8cm` values
7. **Scaling happens automatically:** Large diagrams are scaled to fit
8. **Profile system:** CSS loaded from profile name or explicit `css_file`
9. **Header/footer limitation:** Can't disable on first page (Playwright limitation)
10. **Verbose mode essential:** Always enable for debugging - shows margin extraction, symmetry checks, and pass-through

---

**End of Document**

