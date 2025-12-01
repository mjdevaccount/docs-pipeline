# Structurizr Architecture Documentation Tools

Professional C4 model architecture documentation using **Structurizr DSL + CLI** with automatic diagram generation and export capabilities.

**Version:** 1.0.0  
**Status:** Production-ready, FAANG-level architecture documentation

---

## Overview

This tooling provides a complete workflow for creating and maintaining architecture documentation using the C4 model and Structurizr DSL. It follows FAANG-level documentation standards with:

- **Single Source of Truth:** Architecture model defined in Structurizr DSL
- **Automatic Diagram Generation:** Generate System Context, Container, Component, and Deployment views
- **Multiple Export Formats:** Mermaid, PlantUML, PNG, SVG, HTML
- **Version Control Friendly:** DSL files are text-based and reviewable like code
- **CI/CD Integration:** Generate diagrams automatically in build pipelines

---

## Architecture Overview

The Structurizr workflow uses a **model-first approach**:

```
Structurizr DSL (.dsl)
    ↓
[Structurizr CLI]
    ├─ Export to Mermaid → .mmd files
    ├─ Export to PlantUML → .puml files
    ├─ Export to PNG/SVG → Image files
    ├─ Export to HTML → Interactive diagrams
    └─ Structurizr Lite → Interactive web viewer
    ↓
Generated Diagrams
    ├─ Embedded in Markdown docs
    ├─ Included in PDFs (via pdf-tools)
    └─ Published to documentation sites
```

---

## Quick Start

### Prerequisites

1. **Docker** (required for Structurizr CLI)
   ```bash
   # Verify Docker is installed
   docker --version
   ```

2. **Python 3.8+** (for helper scripts)
   ```bash
   python --version
   ```

### Installation

1. **Activate virtual environment** (if using one):
   ```bash
   # Windows
   .\venv-structurizr\Scripts\Activate.ps1
   
   # Linux/macOS
   source venv-structurizr/bin/activate
   ```

2. **Install Python dependencies** (optional, for helper scripts):
   ```bash
   cd tools/structurizr
   pip install -r requirements-structurizr.txt
   ```

3. **Pull Structurizr CLI Docker image**:
   ```bash
   docker pull structurizr/cli
   ```

4. **Verify installation**:
   ```bash
   # Windows
   structurizr.bat --check
   
   # Linux/macOS
   ./structurizr.sh --check
   ```

---

## Usage

### Basic Commands

#### Export Diagrams from DSL

```bash
# Export to Mermaid format
structurizr.bat export --workspace docs/architecture.dsl --format mermaid --output docs/

# Export to PlantUML
structurizr.bat export --workspace docs/architecture.dsl --format plantuml --output docs/

# Export to PNG images
structurizr.bat export --workspace docs/architecture.dsl --format png --output docs/diagrams/

# Export to SVG
structurizr.bat export --workspace docs/architecture.dsl --format svg --output docs/diagrams/
```

#### Interactive Viewer (Structurizr Lite)

```bash
# Start Structurizr Lite server
structurizr.bat serve --workspace docs/architecture.dsl

# Access at http://localhost:8080
```

#### Validate DSL

```bash
# Check DSL syntax
structurizr.bat validate --workspace docs/architecture.dsl
```

---

## File Structure

```
tools/structurizr/
├── README.md                    # This file
├── requirements-structurizr.txt # Python dependencies (optional)
├── structurizr.bat             # Windows batch wrapper
├── structurizr.sh              # Linux/macOS shell wrapper
├── structurizr.py              # Python helper script (optional)
├── structurizr-config.example.json # Configuration file example
└── examples/                   # Example DSL files
    └── example.dsl
```

---

## Workflow Integration

### With PDF Generation (pdf-tools)

1. **Generate diagrams from DSL**:
   ```bash
   structurizr.bat export --workspace docs/architecture.dsl --format mermaid --output docs/
   ```

2. **Include in Markdown**:
   ```markdown
   ## System Context
   
   <!-- Mermaid diagram would be included here if generated -->
   <!-- See docs/examples/diagrams/structurizr-SystemContext.mmd for source -->

3. **Generate PDF**:
   ```bash
   cd tools/pdf
   python md2pdf.py ../../docs/architecture-diagrams.md
   ```

### With Git / Version Control

1. **Commit DSL files** (source of truth):
   ```bash
   git add docs/architecture.dsl
   git commit -m "Add architecture model"
   ```

2. **Generate diagrams in CI/CD**:
   ```yaml
   # GitHub Actions example
   - name: Generate architecture diagrams
     run: |
       docker run --rm -v ${{ github.workspace }}:/workspace structurizr/cli export \
         -workspace /workspace/docs/architecture.dsl \
         -format mermaid \
         -output /workspace/docs/
   ```

---

## Structurizr DSL Basics

### Workspace Structure

```dsl
workspace "Workspace Name" "Description" {
    model {
        # Define people, software systems, containers, components
    }
    
    views {
        # Define views (System Context, Container, Component, etc.)
    }
    
    configuration {
        # Configuration settings
    }
}
```

### Example DSL

See `docs/architecture.dsl` for a complete example.

---

## C4 Model Levels

### Level 1: System Context
- **Audience:** Executives, Product Managers, Business Stakeholders
- **Shows:** System in context of external users and systems
- **Generated View:** `systemContext`

### Level 2: Container
- **Audience:** Architects, Senior Engineers
- **Shows:** Deployable runtime containers and their interactions
- **Generated View:** `container`

### Level 3: Component
- **Audience:** Developers implementing features
- **Shows:** Internal structure of containers (components)
- **Generated View:** `component`

### Level 4: Code
- **Audience:** Developers (detailed implementation)
- **Shows:** Class diagrams, detailed code structure
- **Note:** Typically auto-generated from code

---

## Export Formats

| Format | Extension | Use Case | Notes |
|--------|-----------|----------|-------|
| **Mermaid** | `.mmd` | Markdown docs, PDF generation | Best for documentation workflows |
| **PlantUML** | `.puml` | Advanced customization | More powerful, requires Java |
| **PNG** | `.png` | Presentations, Word docs | Raster format, fixed resolution |
| **SVG** | `.svg` | Web, scalable diagrams | Vector format, best quality |
| **HTML** | `.html` | Interactive viewing | Full Structurizr viewer |
| **JSON** | `.json` | API integration | Machine-readable format |

---

## Configuration

### structurizr-config.json

```json
{
  "workspace": "docs/architecture.dsl",
  "output_dir": "docs/diagrams",
  "formats": ["mermaid", "png"],
  "views": {
    "systemContext": true,
    "container": true,
    "component": true,
    "deployment": true
  },
  "docker_image": "structurizr/cli:latest"
}
```

---

## Advanced Usage

### Custom Views

Define custom views in your DSL:

```dsl
views {
    systemContext etrmPlatform "SystemContext" {
        include *
        title "System Context - Project Documentation"
        autoLayout lr
    }
    
    dynamic systemFlow "CustomFlow" {
        user -> portal "1. Action"
        portal -> manager "2. Process"
        autoLayout tb
    }
}
```

### Styling

Customize element styles:

```dsl
styles {
    element "Container" {
        shape RoundedBox
        color #ffffff
        background #438dd5
    }
    
    element "Tag:Backend" {
        background #85bbf0
    }
}
```

---

## Troubleshooting

### Docker Issues

**Problem:** Docker not running
```bash
# Check Docker status
docker ps

# Start Docker Desktop (Windows/macOS)
# Or start Docker service (Linux)
sudo systemctl start docker
```

**Problem:** Permission denied
```bash
# Linux: Add user to docker group
sudo usermod -aG docker $USER
# Log out and back in
```

### DSL Syntax Errors

**Problem:** Invalid DSL syntax
```bash
# Validate DSL
structurizr.bat validate --workspace docs/your-file.dsl

# Check Structurizr documentation:
# https://github.com/structurizr/dsl
```

### Export Failures

**Problem:** Diagrams not generating
```bash
# Run with verbose output
structurizr.bat export --workspace docs/your-file.dsl --format mermaid --output docs/ --verbose

# Check Docker logs
docker logs $(docker ps -lq)
```

---

## Best Practices

### 1. Single Source of Truth
- ✅ Define architecture once in DSL
- ✅ Generate all diagrams from DSL
- ❌ Don't manually edit generated diagrams

### 2. Version Control
- ✅ Commit DSL files to Git
- ✅ Generate diagrams in CI/CD
- ✅ Review DSL changes like code

### 3. Naming Conventions
- Use consistent naming: `{System}_{Phase}_{View}.dsl`
- Example: `architecture.dsl`

### 4. Documentation
- Document each view's audience and purpose
- Include examples in DSL comments
- Keep DSL files organized and readable

### 5. Integration
- Generate diagrams before PDF generation
- Include diagrams in Markdown documentation
- Use consistent output directories

---

## CI/CD Integration

### GitHub Actions

```yaml
name: Generate Architecture Diagrams

on:
  push:
    paths:
      - 'docs/**/*.dsl'

jobs:
  generate-diagrams:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Generate diagrams
        run: |
          docker run --rm \
            -v ${{ github.workspace }}:/workspace \
            structurizr/cli export \
            -workspace /workspace/docs/architecture.dsl \
            -format mermaid \
            -output /workspace/docs/
      
      - name: Commit generated diagrams
        run: |
          git config --local user.email "action@github.com"
          git config --local user.name "GitHub Action"
          git add docs/*.mmd
          git commit -m "Auto-generate architecture diagrams" || exit 0
          git push
```

### Azure DevOps

```yaml
steps:
- task: Docker@2
  inputs:
    containerRegistry: 'Docker Hub'
    command: 'run'
    arguments: '--rm -v $(System.DefaultWorkingDirectory):/workspace structurizr/cli export -workspace /workspace/docs/architecture.dsl -format mermaid -output /workspace/docs/'
```

---

## Resources

- **Structurizr DSL Documentation:** https://github.com/structurizr/dsl
- **C4 Model:** https://c4model.com/
- **Structurizr Lite:** https://github.com/structurizr/lite
- **Examples:** See `docs/architecture.dsl`

---

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review Structurizr DSL documentation
3. Validate your DSL syntax
4. Check Docker logs for errors

---

**Last Updated:** November 2025

