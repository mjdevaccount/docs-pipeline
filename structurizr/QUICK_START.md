# Structurizr Tools Quick Start

Get up and running in 5 minutes!

---

## 1. Check Prerequisites

```bash
# Check Docker
docker --version

# Check Python (optional)
python --version
```

---

## 2. Verify Installation

```bash
# Windows
cd structurizr-tools
.\structurizr.bat check

# Linux/macOS
cd structurizr-tools
./structurizr.sh check
```

---

## 3. Generate Your First Diagrams

```bash
# Export from existing DSL file
.\structurizr.bat export --workspace ../docs/ReportingManager_Phase0_Architecture.dsl --format mermaid --output ../docs/

# Or validate your DSL
.\structurizr.bat validate --workspace ../docs/ReportingManager_Phase0_Architecture.dsl
```

---

## 4. View Interactively

```bash
# Start Structurizr Lite server
.\structurizr.bat serve --workspace ../docs/ReportingManager_Phase0_Architecture.dsl

# Open browser to http://localhost:8080
```

---

## Common Commands

```bash
# Export to Mermaid (for Markdown/PDF)
structurizr.bat export --workspace docs/Architecture.dsl --format mermaid --output docs/

# Export to PNG (for presentations)
structurizr.bat export --workspace docs/Architecture.dsl --format png --output docs/diagrams/

# Validate DSL syntax
structurizr.bat validate --workspace docs/Architecture.dsl

# Interactive viewer
structurizr.bat serve --workspace docs/Architecture.dsl
```

---

## Next Steps

- Read `README.md` for full documentation
- See `SETUP.md` for detailed setup instructions
- Check `docs/ReportingManager_Phase0_Architecture.dsl` for DSL examples

---

**That's it!** You're ready to create FAANG-level architecture documentation.

