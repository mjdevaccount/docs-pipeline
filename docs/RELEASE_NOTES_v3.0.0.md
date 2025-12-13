# Release Notes v3.0.0

**Release Date:** December 13, 2025

## 🎯 Overview

v3.0.0 is a **major release** representing 4,700+ lines of new code across 8 priority features, a complete design system overhaul, Mermaid 11 integration, and architectural improvements. This release transforms docs-pipeline into a production-grade documentation platform.

---

## ✨ New Features

### 🎨 Design System (Phases 1-3)
Complete design token system with automated CSS generation:
- **Phase 1:** Centralized design tokens with Pydantic validation
- **Phase 2:** CSS generator and unified theme manager
- **Phase 3:** TOML-based profile configuration and build automation

### 📊 Mermaid 11 Integration
Full theme synchronization for diagrams:
- 80+ CSS variables for complete diagram control
- Dark-pro profile with automatic color mapping
- CSS variable enhancement step in pipeline
- Per-profile Mermaid color schemes (Priority 8)

### 🔄 Watch Mode (Priority 7)
Live file reloading for rapid development:
- Automatic re-render on file changes
- Dev loop optimization
- 1,200 lines of watch infrastructure

### 📚 EPUB Export (Priority 6)
E-book generation with full metadata support:
- EPUB 3.0 compliant output
- Table of contents generation
- Cover page support
- 5 output formats now supported (PDF, DOCX, HTML, Markdown, EPUB)

### 📝 Markdown Export (Priority 5)
Convert processed documents back to clean markdown:
- Glossary term preservation
- Cross-reference maintenance
- Round-trip document processing

### 📖 Glossary Integration (Priority 4)
Term highlighting and definitions:
- CLI commands for glossary management
- Technical and business glossary templates
- Automatic term detection and linking
- Comprehensive usage guide

### ⚡ Incremental Builds (Priority 3)
Smart re-rendering with dependency tracking:
- Build cache for unchanged files
- Dependency graph analysis
- Significant build time reduction

### 📈 Test Coverage Dashboard (Priority 2)
Quality visibility and automation:
- Coverage report generation
- Makefile automation targets
- pytest configuration for metrics

### 📊 Cache Metrics (Priority 1)
Performance tracking and reporting:
- Hit ratio tracking
- Time saved calculations
- Size reduction metrics
- `--verbose` CLI flag for detailed stats

---

## 🔧 Improvements

### Architecture
- **Clean Architecture Refactor:** Separated core library from CLI
- **Playwright-Only Migration:** Removed WeasyPrint, simplified renderer stack
- **CLI as Primary Entry Point:** Consolidated CLI with full feature access

### Compatibility
- **PyPDF2 → pypdf Migration:** Updated to maintained library
- **Pydantic v2 Compatibility:** Theme validator updated
- **Docker Sandbox Fix:** `--no-sandbox` for Mermaid CLI compatibility

### Styling
- **WCAG AA Compliance:** Improved text contrast in dark themes
- **CSS Profile Modernization:** All profiles updated (dark-pro, enterprise-blue, minimalist)
- **Table Improvements:** Fixed overflow and centering issues
- **Syntax Highlighting:** Added to all profiles
- **Callout Boxes:** Professional alert/info styling

### Developer Experience
- **Cursor Rules:** 5 modular .mdc files for IDE integration
- **Comprehensive Documentation:** Quick start guides for all features
- **Makefile Targets:** Automation for common tasks

---

## 🐛 Bug Fixes

- Fixed Mermaid color mapping pipeline ordering issue
- Fixed theme validator encoding and regex patterns
- Fixed chart text contrast in dark themes
- Fixed full-width content layout across profiles
- Fixed cover page centering calculations
- Fixed PDF margin asymmetry
- Removed emojis from Python code files

---

## 📦 Breaking Changes

- **WeasyPrint Removed:** Playwright is now the only PDF renderer
- **CLI Primary Entry Point:** Direct module imports deprecated in favor of CLI

---

## 📈 Stats

| Metric | Value |
|--------|-------|
| Commits since v2.0.0 | 120+ |
| Lines of Code Added | 4,700+ |
| New Features | 8 priorities |
| Output Formats | 5 (PDF, DOCX, HTML, MD, EPUB) |

---

## 🔄 Upgrade Path

```bash
# Pull latest
git pull origin main

# Rebuild Docker image
docker-compose build

# Verify installation
python -m docs_pipeline.cli --help
```

---

## 🙏 Acknowledgments

This release represents a complete platform evolution, transforming docs-pipeline from a document converter into a full-featured documentation platform with enterprise-grade theming, caching, and multi-format export.

---

**Full Changelog:** https://github.com/mjdevaccount/docs-pipeline/compare/v2.0.0...v3.0.0

