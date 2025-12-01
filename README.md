# Documentation Pipeline

Professional documentation tooling for AI-assisted technical writing, architecture diagrams, and PDF generation.

## Overview

A modular toolkit for building publication-quality technical documentation with:

- **PDF Generation** - Markdown → PDF/DOCX with Mermaid diagrams, custom styling, and adaptive layouts
- **AI Document Refinement** - Multi-agent system for structure analysis, content enhancement, and technical review
- **Architecture Diagrams** - Structurizr DSL → Mermaid/PlantUML/SVG with automated export
- **Pipeline Orchestration** - Coordinate multi-stage document workflows with YAML configuration

Built with SOLID principles, type safety, and extensibility. Designed for enterprise documentation workflows but flexible for any technical writing project.

## 🚀 Try It Now

### Option 1: Live Web Demo (Recommended)

The fastest way to see docs-pipeline in action:

```bash
# Clone the repository
git clone https://github.com/mjdevaccount/docs-pipeline.git
cd docs-pipeline

# Start the web demo (requires Docker)
./scripts/start-demo.sh
# Windows: scripts\start-demo.bat

# Opens at http://localhost:8080
```

**One command. Everything works.**

Features:
- 📤 Upload Markdown files via web interface
- 📥 Download generated PDFs instantly
- 📚 Browse pre-generated examples
- 🐳 Fully containerized (no dependency hell)

### Option 2: CLI Usage

For command-line enthusiasts:

```bash
# Install dependencies
pip install -r requirements.txt
pip install -r tools/pdf/requirements-pdf.txt

# Generate PDF
python -m tools.pdf.convert_final input.md output.pdf
```

### Option 3: Generate Example PDFs

```bash
# Generate all example PDFs locally
./scripts/generate-examples.sh
```

## 📦 What's Included

```
docs-pipeline/
├── 🌐 Web Demo (Flask + Docker)
├── 🛠️ CLI Tools (Python)
├── 📄 PDF Generation (Playwright + Pandoc)
├── 🎨 Mermaid Diagrams
├── 🏗️ Architecture Visualization (Structurizr)
└── 📚 AI-Powered Prompts
```

## Quick Start

### PDF Generation

```bash
cd tools/pdf
pip install -r requirements-pdf.txt
python md2pdf.py your-document.md --profile enterprise
```

### AI Document Enhancement

```bash
cd tools/prompts
pip install -r requirements.txt
python -m cli rough-draft.md polished.md -c pipelines/architecture.yaml
```

### Architecture Diagrams

```bash
cd tools/structurizr
docker pull structurizr/cli:latest
python structurizr.py --config your-workspace.json
```

## Documentation

- [PDF Generation Guide](tools/pdf/README.md) - Layout engine, Mermaid optimization, document profiles
- [AI Agents Architecture](tools/prompts/ARCHITECTURE.md) - Multi-agent system design and extension
- [Structurizr Integration](tools/structurizr/README.md) - Docker-based diagram generation

## Features

### PDF Generation Engine

- Playwright-based rendering for pixel-perfect output
- Adaptive pagination with intelligent diagram scaling
- Pre-rendered Mermaid diagrams with theme optimization
- Custom document profiles (cover pages, headers, footers)
- Layout policies for fine-grained control

### AI Document Refinement

- Four specialized agents: Structure Analyzer, Content Enhancer, Technical Reviewer, Style Polisher
- Support for OpenAI (GPT-4) and Anthropic (Claude)
- YAML-based pipeline configuration
- Automated gap analysis and technical validation
- Extensible agent framework

### Architecture Diagram Generation

- Docker-based Structurizr CLI wrapper
- Batch export to multiple formats (Mermaid, PNG, SVG, PlantUML)
- Clean interface-based architecture
- Parallel processing support

## Architecture

Each tool follows SOLID principles with:

- **Single Responsibility** - Focused modules with one purpose
- **Open/Closed** - Extend without modification
- **Liskov Substitution** - Proper interface abstraction
- **Interface Segregation** - Clean, focused interfaces
- **Dependency Inversion** - Depend on abstractions

```
docs-pipeline/
├── tools/                  # All standalone CLI tools
│   ├── pdf/                # Markdown → PDF/DOCX generation
│   │   ├── playwright_pdf/ # Browser-based rendering
│   │   └── tests/          # Layout verification and benchmarks
│   ├── prompts/            # AI-powered document refinement
│   │   ├── agents/         # Document processing agents
│   │   ├── library/        # Prompt templates
│   │   └── pipelines/      # Workflow configurations
│   └── structurizr/        # Architecture diagram generation
│       └── structurizr_tools/
├── docs/                   # Central documentation
│   ├── examples/           # Working examples
│   ├── development/        # Dev docs
│   └── images/             # Screenshots/diagrams
├── tests/                  # Integration tests
└── scripts/                # Helper scripts
```

## Requirements

- Python 3.9+
- Docker (for Structurizr diagrams)
- Playwright (auto-installed with pdf requirements)
- OpenAI or Anthropic API key (for AI agents)

## Installation

### Option 1: Full Install

```bash
pip install -r requirements.txt  # All tools
```

### Option 2: Tool-Specific

```bash
pip install -r tools/pdf/requirements-pdf.txt              # PDF only
pip install -r tools/prompts/requirements.txt             # AI agents only
pip install -r tools/structurizr/requirements-structurizr.txt  # Diagrams only
```

## Configuration

Each tool uses YAML configuration:

- PDF: Document profiles in `tools/pdf/profiles.py` or custom CSS
- AI Agents: Pipeline configs in `tools/prompts/pipelines/*.yaml`
- Structurizr: Workspace configs in `tools/structurizr/*.json`

See tool-specific README files for detailed configuration options.

## Examples

Complete examples in each tool directory:

- `tools/pdf/docs/` - Sample markdown documents with diagrams
- `tools/prompts/examples/` - Rough drafts and pipeline configurations
- `tools/structurizr/` - Example DSL files and export configs

## Development

### Running Tests

**PDF layout verification:**
```bash
cd tools/pdf/tests
python test_project_docs_layout.py
```

**AI agents (requires API key):**
```bash
cd tools/prompts
python -m pytest tests/
```

**Structurizr:**
```bash
cd tools/structurizr
python structurizr.py --validate
```

### Code Standards

- Type hints on all functions
- Google-style docstrings
- PEP 8 compliance
- 100% test coverage on core logic

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## License

MIT License - see [LICENSE](LICENSE) for details.

## Author

Built by [Matt Jeffcoat](https://github.com/mjdevaccount) - Senior Software Engineer specializing in AI-powered tooling, distributed systems, and developer experience.

## Acknowledgments

- Playwright team for excellent browser automation
- Structurizr for C4 model tooling
- OpenAI and Anthropic for LLM APIs

