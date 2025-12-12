# PDF Layout & Metadata Analysis

## Complete Code Location Map

This document identifies ALL files and code sections related to PDF generation, including metadata, page breaks, headers, footers, margins, and layout.

---

## 📁 Core Files

### 1. `pdf-tools/pdf_playwright.py` (1,334 lines)
**Primary PDF generation engine using Playwright/Chromium**

#### **Page Setup & Margins**
- **Lines 494-497**: `@page` CSS rule with margins
  ```css
  @page {
      size: A4;
      margin: 0.75in 0.75in 1in 0.75in;  /* top, right, bottom, left */
  }
  ```
- **Lines 65-68**: Available height calculation for diagram scaling
  ```javascript
  const pageHeight = 10 * 96;  // 960px (A4 height)
  const marginTop = 0.75 * 96;  // 72px
  const marginBottom = 1 * 96;  // 96px
  const availableHeight = pageHeight - marginTop - marginBottom;  // ~792px
  ```

#### **Headers & Footers**
- **Lines 1158-1185**: Header/Footer template generation
  - **Header Template** (lines 1165-1169):
    - Title (font-weight: 600)
    - Organization (color: #666, font-size: 8px)
    - Border-bottom: 1px solid #ddd
    - Centered layout
  - **Footer Template** (lines 1178-1185):
    - Author and Date (if provided)
    - Page numbers: "Page X of Y"
    - Color: #666
- **Lines 1187-1193**: Playwright PDF options with header/footer
  ```python
  options = {
      'format': 'A4',
      'display_header_footer': True,
      'header_template': header_template,
      'footer_template': footer_template,
      'margin': {
          'top': '0.75in',
          'right': '0.75in',
          'bottom': '1in',
          'left': '0.75in'
      }
  }
  ```
- **Lines 828-843**: Default header/footer templates in `html_to_pdf_playwright()`
  - Basic templates with page numbers
  - Used as fallback if not overridden

#### **Cover Page**
- **Lines 711-767**: `inject_cover_page()` function
  - **HTML Structure** (lines 727-760):
    - Fixed height: `10in`
    - Padding: `2in 40px`
    - Flexbox layout (centered)
    - Logo support (base64 encoded)
    - Title: `font-size: 36pt`, `font-weight: 600`
    - Organization: `font-size: 18pt`, `color: #666`
    - Author/Date: `font-size: 14pt`, `color: #999`
  - **Page Break**: CSS class `.cover-page-wrapper` with `page-break-after: always`
- **Lines 580-586**: CSS rules for cover page
  ```css
  .cover-page-wrapper {
      page-break-after: always !important;
      break-after: page !important;
      break-inside: avoid !important;
      page-break-before: auto !important;
  }
  ```

#### **Table of Contents**
- **Lines 639-708**: `inject_toc()` function
  - **HTML Generation** (lines 661-682):
    - Wrapper: `.toc-wrapper` with `page-break-after: always`
    - Title: `font-size: 24pt`, `border-bottom: 2px solid #333`
    - Links: `color: #1976d2`, `font-size: 14pt` (decreases by level)
    - Indentation: `20px` per level
  - **Page Break**: Inline style + CSS class
- **Lines 588-594**: CSS rules for TOC
  ```css
  .toc-wrapper {
      page-break-after: always !important;
      break-after: page !important;
      break-inside: avoid !important;
      page-break-before: auto !important;
  }
  ```

#### **Page Break Rules**
- **Lines 500-505**: Heading page break rules
  ```css
  h1, h2, h3, h4, h5, h6 {
      page-break-after: avoid !important;
      break-after: avoid !important;
      page-break-inside: avoid !important;
      break-inside: avoid !important;
  }
  ```
- **Lines 511-514**: H3 specific rules (keep with diagrams)
- **Lines 517-524**: Diagram page break rules
- **Lines 527-534**: Scaled diagram rules (`[data-scaled]`)
- **Lines 537-544**: Heading collision prevention (after diagrams)
- **Lines 547-553**: Force break after large diagrams
- **Lines 562-571**: Figure, table, list item rules
- **Lines 574-578**: Generic `.page-break` class
- **Lines 596-601**: Spacing after forced breaks

#### **Metadata Embedding**
- **Lines 951-998**: `embed_pdf_metadata()` function
  - Uses PyPDF2 to embed PDF metadata
  - Fields: Title, Author, Subject, Keywords
  - Creator: "Playwright PDF Generator"
  - Producer: "Chromium"
- **Lines 1038-1041**: Function signature accepting metadata
  ```python
  async def generate_pdf_from_html(
      html_file, pdf_file,
      title=None, author=None, organization=None, date=None,
      logo_path=None, generate_toc=False, generate_cover=False,
      watermark=None, css_file=None, verbose=False
  )
  ```

#### **Watermark**
- **Lines 768-803**: `add_watermark()` function
  - Fixed position overlay
  - Rotated -45 degrees
  - Font-size: 120pt
  - Color: rgba(255, 0, 0, 0.1) (red, 10% opacity)
  - z-index: 9999

---

### 2. `pdf-tools/cli/main.py` (1,183 lines)
**Markdown to PDF conversion orchestrator**

#### **Metadata Extraction**
- **Lines 452-684**: `markdown_to_pdf()` function
  - **Lines 500-630**: YAML frontmatter parsing
    - Extracts: `title`, `author`, `organization`, `date`, `version`, `type`, `classification`
    - Optional: `department`, `review_status`, `doc_id`, `prepared_for`
  - **Lines 632-653**: Metadata block HTML generation
    - Structured display of all metadata fields
    - Styled with `<strong>` tags

#### **Title Page (WeasyPrint Path)**
- **Lines 656-670**: Title page HTML structure
  ```html
  <header class="title-page">
      <logo>
      <div class="title-block">
          <h1 class="doc-title">{title}</h1>
          <p class="doc-type">{type}</p>
      </div>
      <div class="classification">{classification}</div>
      <div class="metadata-block">{metadata}</div>
      <div class="disclaimer">{disclaimer}</div>
  </header>
  ```
- **Lines 699-856**: CSS styling for title page
  - **Lines 699-701**: Default page margins: `25mm 15mm 20mm 15mm`
  - **Lines 725-730**: First page margins (different)
  - **Lines 748-756**: Title page page break: `page-break-after: always`
  - **Lines 757-831**: Detailed styling for all title page elements

#### **Page Margins (WeasyPrint)**
- **Lines 699-701**: Default `@page` margins
  ```css
  @page {
      size: A4;
      margin: 25mm 15mm 20mm 15mm;  /* top, right, bottom, left */
  }
  ```
- **Lines 725-730**: First page margins (different from default)

---

### 3. `pdf-tools/custom.css.playwright` (581 lines)
**External CSS file for Playwright rendering**

#### **Page Setup**
- **Lines 20-23**: `@page` rule
  ```css
  @page {
      size: A4;
      margin: 0.75in 0.75in 1in 0.75in;  /* top, right, bottom, left */
  }
  ```

#### **Page Break Rules**
- **Lines 69-71**: Heading page breaks
- **Lines 179, 204, 255, 292, 314**: Various element page breaks
- **Lines 375-394**: Diagram page break rules (with `[data-scaled]` exceptions)
- **Lines 459-470**: Print-specific page break classes
  - `.page-break-before`: `page-break-before: always`
  - `.page-break-after`: `page-break-after: always`
  - `.no-page-break`: `page-break-inside: avoid`

#### **Margins & Spacing**
- **Lines 80-81**: H1 margins
- **Lines 90-91**: H2 margins
- **Lines 97-98**: H3 margins
- **Lines 106-107**: H4 margins
- **Lines 114-115**: H5 margins
- **Lines 123-124**: H6 margins
- **Lines 564-569**: Utility margin classes (`.mt-0`, `.mb-0`, etc.)

---

### 4. `pdf-tools/cli/main.py` (787 lines)
**CLI wrapper and entry point**

#### **Metadata Handling**
- **Lines 317-671**: `main()` function
  - **Lines 646-653**: Metadata extraction and display
    - Reads YAML frontmatter
    - Echoes title, author to console
  - **Lines 668**: Passes metadata to `markdown_to_pdf()`

#### **Command Line Arguments**
- **Lines 317-400**: Argument parser setup
  - `--generate-cover`: Enable cover page
  - `--generate-toc`: Enable table of contents
  - `--watermark`: Add watermark text
  - `--css`: Specify custom CSS file
  - `--renderer`: Choose renderer (playwright/weasyprint)

---

## 🔍 Key Code Sections by Feature

### **Headers & Footers**

#### **Current Implementation:**
1. **`pdf_playwright.py` lines 1158-1185**: Dynamic header/footer template generation
2. **`pdf_playwright.py` lines 1187-1193**: Playwright PDF options with `display_header_footer: True`
3. **`pdf_playwright.py` lines 828-843**: Default templates (fallback)

#### **Missing/Issues:**
- ❌ **No running headers** (headers don't change per section)
- ❌ **No chapter-based footers** (can't show chapter name in footer)
- ❌ **No first-page suppression** (headers/footers appear on cover page)
- ❌ **No different headers for TOC vs content**
- ❌ **Limited customization** (only title/organization in header, author/date in footer)

---

### **Page Margins**

#### **Current Implementation:**
1. **`pdf_playwright.py` lines 494-497**: CSS `@page` margins (0.75in top/right/left, 1in bottom)
2. **`custom.css.playwright` lines 20-23**: Same margins in external CSS
3. **`cli/main.py` lines 699-701**: Different margins for WeasyPrint (25mm/15mm/20mm/15mm)
4. **`pdf_playwright.py` lines 65-68**: Margin calculations for diagram scaling

#### **Issues:**
- ⚠️ **Inconsistent margins** between Playwright and WeasyPrint paths
- ⚠️ **No margin adjustment** for headers/footers (header/footer space not subtracted from content area)
- ⚠️ **Hardcoded values** (not configurable)

---

### **Page Breaks**

#### **Current Implementation:**
1. **`pdf_playwright.py` lines 487-632**: `inject_adaptive_pagination_css()` - Comprehensive page break rules
2. **`pdf_playwright.py` lines 580-594**: Cover page and TOC page breaks
3. **`pdf_playwright.py` lines 500-578**: Heading, diagram, and element page breaks
4. **`custom.css.playwright` lines 69-470**: Additional page break rules

#### **Issues:**
- ⚠️ **Complex rules** (many overlapping `!important` rules)
- ⚠️ **No page break before specific sections** (can't force break before h2, etc.)
- ⚠️ **No widow/orphan control** (can't prevent single lines at page top/bottom)

---

### **Metadata**

#### **Current Implementation:**
1. **`cli/main.py` lines 500-630**: YAML frontmatter extraction
2. **`pdf_playwright.py` lines 951-998**: PDF metadata embedding (PyPDF2)
3. **`pdf_playwright.py` lines 1038-1041**: Function parameters for metadata
4. **`cli/main.py` lines 646-653**: Metadata display in CLI

#### **Supported Fields:**
- ✅ `title`, `author`, `organization`, `date`, `version`, `type`, `classification`
- ✅ `department`, `review_status`, `doc_id`, `prepared_for` (optional)

#### **Missing:**
- ❌ **PDF metadata fields**: Subject, Keywords, Creator, Producer (partially implemented)
- ❌ **Custom metadata** (can't add arbitrary fields)
- ❌ **Metadata in headers/footers** (limited to title/organization/author/date)

---

### **Cover Page**

#### **Current Implementation:**
1. **`pdf_playwright.py` lines 711-767**: `inject_cover_page()` function
2. **`pdf_playwright.py` lines 580-586**: CSS rules for cover page
3. **`pdf_playwright.py` lines 1137-1139**: Cover page injection in main flow

#### **Features:**
- ✅ Logo support (base64 encoded)
- ✅ Title, organization, author, date display
- ✅ Fixed height (10in) with flexbox centering
- ✅ Page break after cover page

#### **Missing:**
- ❌ **No cover page for WeasyPrint path** (only Playwright)
- ❌ **No customization** (can't change layout, fonts, colors)
- ❌ **No classification banner** (security classification not prominently displayed)

---

### **Table of Contents**

#### **Current Implementation:**
1. **`pdf_playwright.py` lines 639-708**: `inject_toc()` function
2. **`pdf_playwright.py` lines 588-594**: CSS rules for TOC
3. **`pdf_playwright.py` lines 1141-1143**: TOC injection in main flow
4. **`pdf_playwright.py` lines 1126-1135**: Pandoc TOC removal

#### **Features:**
- ✅ Auto-generated from h1, h2, h3 headings
- ✅ Excludes headings from cover page
- ✅ Clickable links with anchors
- ✅ Indentation by level
- ✅ Page break after TOC

#### **Missing:**
- ❌ **No page numbers** in TOC (can't show "Page 5" next to each entry)
- ❌ **No TOC depth control** (always includes h1-h3)
- ❌ **No customization** (colors, fonts hardcoded)

---

## 📊 Summary: What's Missing

### **Critical Missing Features:**

1. **Headers/Footers:**
   - ❌ Running headers (chapter/section name)
   - ❌ Different headers for different page types (cover, TOC, content)
   - ❌ First-page header/footer suppression
   - ❌ Left/right page headers (for double-sided printing)
   - ❌ Custom header/footer templates

2. **Page Layout:**
   - ❌ Header/footer space not accounted for in content area calculations
   - ❌ Different margins for first page vs. content pages
   - ❌ Different margins for left/right pages
   - ❌ Configurable margins (currently hardcoded)

3. **Page Breaks:**
   - ❌ Widow/orphan control (prevent single lines at top/bottom)
   - ❌ Section-based page breaks (force break before h2, etc.)
   - ❌ Keep-with-next rules (keep paragraph with following heading)

4. **Metadata:**
   - ❌ PDF metadata not fully populated (Subject, Keywords missing)
   - ❌ Custom metadata fields
   - ❌ Metadata-driven headers/footers

5. **Cover Page:**
   - ❌ WeasyPrint cover page support
   - ❌ Customizable layout
   - ❌ Classification banner

6. **Table of Contents:**
   - ❌ Page numbers in TOC entries
   - ❌ Configurable depth
   - ❌ Customizable styling

---

## 🎯 Files to Review for Expert Consultation

### **Primary Files:**
1. **`pdf-tools/pdf_playwright.py`**
   - Lines 487-632: Page break CSS injection
   - Lines 1158-1193: Header/footer generation
   - Lines 711-767: Cover page generation
   - Lines 639-708: TOC generation
   - Lines 494-497: Page margins

2. **`pdf-tools/custom.css.playwright`**
   - Lines 20-23: Page margins
   - Lines 69-470: Page break rules
   - Lines 375-394: Diagram page breaks

3. **`pdf-tools/cli/main.py`**
   - Lines 500-630: Metadata extraction
   - Lines 699-856: WeasyPrint page setup

### **Secondary Files:**
4. **`pdf-tools/cli/main.py`**: CLI argument handling
5. **`pdf-tools/pdf-mermaid-theme.json`**: Diagram theming (affects layout)

---

## 🔧 Configuration Points

### **Hardcoded Values That Should Be Configurable:**

1. **Page Margins** (currently hardcoded):
   - `pdf_playwright.py` line 496: `margin: 0.75in 0.75in 1in 0.75in`
   - `custom.css.playwright` line 22: Same margins
   - `cli/main.py` line 700: `margin: 25mm 15mm 20mm 15mm` (different!)

2. **Header/Footer Font Sizes** (currently hardcoded):
   - `pdf_playwright.py` line 1166: `font-size: 9px`
   - `pdf_playwright.py` line 1179: `font-size: 9px`

3. **Cover Page Dimensions** (currently hardcoded):
   - `pdf_playwright.py` line 729: `height: 10in`
   - `pdf_playwright.py` line 730: `padding: 2in 40px`

4. **Available Height Calculation** (currently hardcoded):
   - `pdf_playwright.py` lines 65-68: Margin calculations for diagram scaling

---

## 📝 Questions for Expert Consultation

1. **How to implement running headers** (chapter name in header)?
2. **How to suppress headers/footers on first page** (cover page)?
3. **How to account for header/footer space** in content area calculations?
4. **How to add page numbers to TOC** entries?
5. **How to implement widow/orphan control** (prevent single lines)?
6. **How to make margins configurable** (YAML frontmatter or CLI args)?
7. **How to implement different headers for different page types** (cover, TOC, content)?
8. **How to add left/right page headers** (for double-sided printing)?

---

## 🚀 Recommended Next Steps

1. **Create configuration system** for margins, header/footer templates
2. **Implement header/footer space calculation** in content area
3. **Add running headers** support (section/chapter name)
4. **Add page numbers to TOC** (requires page number calculation)
5. **Implement first-page header/footer suppression**
6. **Make all hardcoded values configurable** (YAML frontmatter or CLI)

---

**Last Updated:** 2025-11-16  
**Files Analyzed:** 5 core files, 2 CSS files  
**Total Code Locations:** 50+ specific line ranges identified

