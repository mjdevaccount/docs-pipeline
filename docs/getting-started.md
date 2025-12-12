# Getting Started with Documentation Pipeline

## Installation

### Prerequisites

- Python 3.9+
- Docker (for Structurizr diagrams)
- Git

### Quick Install

**Clone repository:**
```bash
git clone https://github.com/mjdevaccount/docs-pipeline.git
cd docs-pipeline
```

**Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

**Install all tools:**
```bash
pip install -e ".[pdf,ai,structurizr,dev]"
```

**Install Playwright browsers:**
```bash
playwright install chromium
```

## First Project: Generate a PDF

### 1. Create a simple markdown document

Create `my-first-doc.md`:

```markdown
---
title: "My Technical Document"
author: "Your Name"
date: "2025-01-30"
---

# Introduction

This is my first document using the docs-pipeline tooling.

## Architecture Overview

```mermaid
graph LR
    A[User] --> B[Pipeline]
    B --> C[PDF Output]
```

## Conclusion

Professional documentation made easy.
```

### 2. Generate PDF

```bash
cd pdf
python convert_final.py ../my-first-doc.md --output ../my-first-doc.pdf
```

### 3. View Output

Open `my-first-doc.pdf` - you'll see:

- Professional cover page
- Rendered Mermaid diagram
- Clean typography
- Proper pagination

## Next Steps

- [AI Document Enhancement Tutorial](examples/ai-enhanced-doc/)
- [Architecture Diagrams Guide](../structurizr/README.md)
- [Full Pipeline Workflow](examples/full-pipeline/)

