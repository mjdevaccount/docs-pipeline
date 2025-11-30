# Changelog v2.0.0 - Advanced Documentation Features

## 🚀 Major New Features

### 1. Math Support (LaTeX)
- ✅ Full LaTeX math rendering support
- ✅ Inline math: `$E = mc^2$`
- ✅ Display math: `$$E = mc^2$$`
- ✅ Alternative syntax: `\[...\]` and `\(...\)`
- ✅ MathJax integration for HTML output
- ✅ WeasyPrint MathML for PDF output

### 2. Code Highlighting
- ✅ Syntax highlighting with customizable styles
- ✅ Default: GitHub style (clean and readable)
- ✅ Options: `pygments`, `tango`, `kate`, `monochrome`, `espresso`, `zenburn`, `breezedark`
- ✅ CLI option: `--highlight-style STYLE`
- ✅ Config file support

### 3. Cross-References
- ✅ Automatic figure/table numbering
- ✅ Reference syntax: `[@fig:label]` and `[@tbl:label]`
- ✅ Pandoc-crossref filter integration
- ✅ Configurable via YAML config file
- ✅ CLI option: `--crossref-config PATH`

### 4. Glossary & Acronym Expansion
- ✅ Automatic acronym expansion (e.g., "API" → "Application Programming Interface (API)")
- ✅ Glossary appendix generation
- ✅ YAML-based configuration
- ✅ CLI option: `--glossary PATH`
- ✅ Example file: `glossary-example.yaml`

### 5. HTML Output
- ✅ New output format: `--format html`
- ✅ Responsive HTML with navigation sidebar
- ✅ MathJax for math rendering
- ✅ Syntax highlighting
- ✅ Search-friendly structure
- ✅ Custom CSS support
- ✅ Fixed sidebar navigation

### 6. Multiple Diagram Types
- ✅ **Mermaid:** Flowcharts, sequence diagrams, state diagrams (existing, enhanced)
- ✅ **PlantUML:** UML diagrams, sequence diagrams, class diagrams (NEW)
- ✅ **Graphviz/DOT:** Graph visualizations (NEW)
- ✅ All diagram types cached and rendered to SVG/PNG
- ✅ Automatic detection and rendering

## 📝 Implementation Details

### Math Support
- Enabled Pandoc extensions: `tex_math_dollars`, `tex_math_double_backslash`
- MathJax CDN included in HTML output
- WeasyPrint handles MathML for PDF

### Code Highlighting
- Pandoc `--highlight-style` option integrated
- Default: GitHub style (professional and readable)
- All formats support: PDF, DOCX, HTML

### Cross-References
- Requires `pandoc-crossref` filter (optional dependency)
- Configurable via YAML file
- Automatic numbering and reference resolution

### Glossary Expansion
- Pre-processor runs before Pandoc conversion
- YAML format: `acronyms:` and `terms:` sections
- Case-insensitive matching
- Glossary appendix auto-generated

### HTML Output
- New function: `markdown_to_html()`
- Responsive CSS with sidebar navigation
- MathJax CDN included
- Custom CSS support via `--css`

### Diagram Interoperability
- New function: `render_all_diagrams()` (wrapper)
- PlantUML: Requires Java + `plantuml.jar`
- Graphviz: Requires `dot` command (Graphviz package)
- All diagrams cached by content hash

## 🔧 CLI Updates

### New Arguments
- `--format html` - Generate HTML output
- `--highlight-style STYLE` - Code highlighting style
- `--crossref-config PATH` - Cross-reference config file
- `--glossary PATH` - Glossary/acronym expansion file

### Updated Arguments
- `--format` now supports `html` option
- `--css` now works for both PDF and HTML

## 📦 New Files

- `glossary-example.yaml` - Example glossary configuration
- `crossref-config-example.yaml` - Example crossref configuration
- `FEATURE_ANALYSIS.md` - Detailed feature analysis document
- `CHANGELOG-v2.0.md` - This file

## 🔄 Updated Files

- `convert_final.py` - Added all new features
- `md2pdf.py` - Updated CLI for new features
- `README.md` - Comprehensive documentation updates
- `pdf-config.json.example` - Updated with new options

## ⚠️ Optional Dependencies

Some features require additional tools (gracefully handled if missing):

- **pandoc-crossref:** For cross-references (Haskell package)
- **PlantUML:** Java runtime + `plantuml.jar` (for PlantUML diagrams)
- **Graphviz:** `dot` command-line tool (for Graphviz diagrams)

## 📊 Backward Compatibility

✅ **Fully backward compatible**
- All existing features work as before
- New features are opt-in via CLI flags
- Default behavior unchanged
- Config files work with or without new fields

## 🎯 Usage Examples

```bash
# Math support (automatic)
python md2pdf.py docs/report.md

# Code highlighting
python md2pdf.py docs/report.md --highlight-style tango

# Cross-references
python md2pdf.py docs/report.md --crossref-config crossref.yaml

# Glossary expansion
python md2pdf.py docs/report.md --glossary glossary.yaml

# HTML output
python md2pdf.py docs/report.md --format html

# All features together
python md2pdf.py docs/report.md \
  --format pdf \
  --highlight-style github \
  --crossref-config crossref.yaml \
  --glossary glossary.yaml \
  --css styles/custom.css
```

## 🎉 Summary

Version 2.0.0 transforms the toolchain from a PDF/DOCX converter into a **comprehensive documentation generation system** with:
- ✅ Math rendering
- ✅ Code highlighting
- ✅ Cross-references
- ✅ Glossary expansion
- ✅ HTML output
- ✅ Multiple diagram types

All features are production-ready and fully documented!

