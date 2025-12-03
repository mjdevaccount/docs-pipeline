# 🎉 docs-pipeline v1.0.0 - Production Release

**Transform Markdown into publication-quality PDFs with professional styling, Mermaid diagrams, and zero configuration.**

## 🚀 What's New

### ✨ Metadata Customization (Complete)

Full support for customizing document metadata across all interfaces:

- **CLI Arguments**: `--author`, `--organization`, `--version`, `--classification`, `--doc-type`
- **YAML Pipeline**: Workspace defaults and document-level metadata
- **Environment Variables**: `USER_NAME`, `ORGANIZATION`, `DOC_LOGO_PATH`
- **Frontmatter**: YAML frontmatter in markdown files
- **Priority Chain**: CLI > YAML > Frontmatter > Env Vars > Defaults

### 📝 YAML Pipeline Support

Batch processing with workspace-level defaults:

```yaml
workspaces:
  default:
    defaults:
      author: "Your Name"
      organization: "Your Company"
    documents:
      - input: doc.md
        metadata:
          version: "1.0"
```

### 🎨 Professional Profiles

Four visual profiles for different use cases:

- **tech-whitepaper**: Clean technical documentation
- **dark-pro**: Modern presentations and demos
- **minimalist**: Architecture docs and RFCs
- **enterprise-blue**: Corporate reports and proposals

### 🔧 Environment Variables

Set once, use everywhere:

```bash
export USER_NAME="Your Name"
export ORGANIZATION="Your Company"
export DOC_LOGO_PATH="$HOME/Documents/logo.png"
```

### 📄 Resume Template

Professional resume template included:

- `docs/examples/resume-template.md`
- Ready to customize with your information
- Optimized frontmatter for PDF generation

## 🎯 Key Features

- ✅ **Mermaid Diagram Rendering**: Automatic SVG conversion with theme matching
- ✅ **Multiple Rendering Engines**: Playwright (recommended) and WeasyPrint
- ✅ **Metadata Customization**: Full control over document metadata
- ✅ **YAML Pipeline**: Batch processing with workspace defaults
- ✅ **Web Demo**: Live web interface at http://localhost:8080
- ✅ **Professional Profiles**: 4 visual styles for different document types
- ✅ **Environment Variables**: Personal defaults for convenience
- ✅ **Logo Support**: Automatic logo path resolution
- ✅ **Metadata Validation**: Input sanitization and validation

## 📊 What's Production-Ready

- ✅ CLI interface with all metadata arguments
- ✅ YAML pipeline with workspace defaults
- ✅ Environment variable support
- ✅ Logo path resolution with fallbacks
- ✅ Metadata validation and sanitization
- ✅ Comprehensive documentation
- ✅ Resume template example
- ✅ Real-world usage examples

## 🧪 Tested & Validated

- 100KB+ of tests covering layout, scaling, and diagram rendering
- Tested across multiple document types
- Validated with real-world use cases

## 📖 Documentation

- Complete README with quick start guide
- PDF generation guide with examples
- YAML pipeline configuration examples
- Environment variable documentation
- Real-world usage examples

## 🚀 Quick Start

### Docker (Recommended)

```bash
docker-compose up
# Open http://localhost:8080
```

### CLI

```bash
pip install -r requirements.txt
pip install -r tools/pdf/requirements-pdf.txt

python tools/pdf/md2pdf.py input.md output.pdf --profile tech-whitepaper
```

## 🎯 Use Cases

- **Resumes**: Professional PDF resumes with custom metadata
- **Portfolio Pieces**: Technical write-ups and project documentation
- **Client Deliverables**: Branded proposals and reports
- **Internal Docs**: Technical specifications with proper classification
- **Batch Processing**: Generate multiple documents with workspace defaults

## 📝 Breaking Changes

None! This is a production-ready release with full backward compatibility.

## 🙏 Acknowledgments

Built with:
- [Playwright](https://playwright.dev) - Browser automation
- [Pandoc](https://pandoc.org) - Markdown processing
- [Mermaid](https://mermaid.js.org) - Diagram syntax

## 📦 Installation

See [README.md](README.md) for full installation instructions.

---

**Full Changelog**: https://github.com/mjdevaccount/docs-pipeline/compare/v0.9.0...v1.0.0


