# Cursor Rules: docs-pipeline Code Generator

## TL;DR System

**docs-pipeline** = Containerized doc automation engine  
**Input**: Codebase (Python/C#/multi-lang) + `config.yaml`  
**Output**: Markdown documentation (README, API docs, architecture)  
**Mode**: Zero-interaction (CLI-driven, CI/CD ready)  

---

## Architecture

### Components
```
core/           Parser (AST), Extractor (metadata), Analyzer (architecture)
generators/     README, API docs, Architecture, Changelog, Index
pipeline/       Orchestrator, Stages, Error handlers
models/         Pydantic dataclasses (CodebaseModel, ModuleMetadata, etc.)
utils/          Logging, Git utilities, Validators
```

### Workflow (6 Stages)
```
1. DISCOVERY    → Detect language/framework, load config
2. PARSING      → AST traversal, extract all metadata
3. ENRICHMENT   → Git history, test coverage, quality metrics
4. RENDERING    → Jinja2 templates → markdown
5. VALIDATION   → Lint, link checks, structure verification
6. OUTPUT       → Write files, compress, generate sitemaps
```

---

## CLI Commands

### Primary
```bash
# Full pipeline
python -m docs_pipeline.cli generate --source-path ./src --output-path ./output

# Individual stages
python -m docs_pipeline.cli parse --source-path ./src
python -m docs_pipeline.cli extract --source-path ./src --output-format json
python -m docs_pipeline.cli validate --output-path ./output

# Dev mode
python -m docs_pipeline.cli generate --source-path ./src --output-path ./output --watch
```

### Flags
| Flag | Type | Purpose |
|------|------|----------|
| `--source-path` | path | Input repository (required) |
| `--output-path` | path | Output directory (required) |
| `--config` | file | Pipeline config YAML (optional) |
| `--log-level` | enum | DEBUG\|INFO\|WARN\|ERROR (default: INFO) |
| `--watch` | flag | Dev mode: auto-rebuild on changes |
| `--skip-validation` | flag | Skip validation stage |
| `--dry-run` | flag | Simulate without writing |

### Exit Codes
```
0   = Success
1   = Runtime/validation error
2   = Config error
130 = Interrupted (SIGINT)
```

---

## Docker

### Build
```bash
docker build -t docs-pipeline:latest .
```

### Run
```bash
docker run --rm \
  -v $(pwd)/source:/workspace/source:ro \
  -v $(pwd)/output:/workspace/output:rw \
  -v $(pwd)/config:/workspace/config:ro \
  -e LOG_LEVEL=INFO \
  docs-pipeline:latest \
  generate --source-path /workspace/source --output-path /workspace/output
```

### Stack
- **Base**: `python:3.11-slim`
- **Security**: Non-root user, minimal capabilities, read-only source
- **Optimization**: Multi-stage build, pinned deps, layer caching
- **Health**: `HEALTHCHECK --interval=30s`

---

## Code Patterns

### Python Standards
```python
# Type hints on all functions
def parse(path: str) -> CodebaseModel:
    """Parse source code and extract metadata.
    
    Args:
        path: Source directory path
        
    Returns:
        CodebaseModel with all parsed data
        
    Raises:
        ValueError: If path invalid
    """
    pass

# Use async for I/O
async def extract_git_history(repo_path: str) -> list[GitCommit]:
    pass

# Context managers for cleanup
with open(file_path) as f:
    data = f.read()
```

### Pydantic Models (Data)
```python
from pydantic import BaseModel, Field, validator

class ModuleMetadata(BaseModel):
    name: str
    path: str
    functions: list[FunctionMetadata]
    dependencies: set[str] = Field(default_factory=set)
    
    @validator('path')
    def validate_path(cls, v):
        if not v.endswith('.py'):
            raise ValueError('Must be .py file')
        return v
```

### Generator Pattern
```python
class DocGenerator(ABC):
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.env = jinja2.Environment(autoescape=True)
    
    @abstractmethod
    def generate(self, codebase: CodebaseModel) -> str:
        """Render template with codebase data."""
        pass
```

### Jinja2 Templates
```jinja2
{# Use autoescape for security #}
# {{ codebase.name }}

{{ codebase.description }}

## Modules

{% for module in codebase.modules %}
### {{ module.name }}
{{ module.docstring }}
{% endfor %}
```

---

## Testing

### Structure
```
tests/
├── unit/           → Individual function tests
├── integration/    → Full pipeline tests
└── fixtures/       → Example codebases, configs
```

### Standards
- **Coverage**: Minimum 80% (excluding CLI)
- **Mocks**: Use `unittest.mock` for git, file I/O
- **Parametrization**: `@pytest.mark.parametrize` for multiple cases
- **Fixtures**: Reusable in `conftest.py`

### Run
```bash
# Local
pytest --cov=docs_pipeline tests/

# Docker
docker run --rm docs-pipeline:test pytest --cov=docs_pipeline tests/

# CI validation
black --check .
flake8 docs_pipeline/
mypy docs_pipeline/
bandit -r docs_pipeline/
```

---

## Zero-Interaction Principles

1. **Deterministic** — Same input → same output always
2. **Idempotent** — Running twice safe, no duplication
3. **Fail-fast** — Exit early with clear messages
4. **Observable** — Structured JSON logging for debugging
5. **Recoverable** — Graceful degradation, state preservation
6. **Containerized** — No host environment dependencies
7. **Versioned** — All transitive deps pinned

---

## Error Handling

### Strategy
```python
try:
    # Attempt operation
    result = parse_module(path)
except ParseError as e:
    # Log + skip, continue pipeline
    logger.warning(f"Skipping {path}: {e}")
    return None
except Exception as e:
    # Unrecoverable: dump state, exit
    logger.error(f"Fatal: {e}", exc_info=True)
    dump_state()
    sys.exit(1)
```

### Logging (Structured)
```python
import structlog

logger = structlog.get_logger()
logger.info("stage_start", stage="parsing", path="/src")
logger.error("parse_failed", module="api.py", error=str(e))
logger.info("stage_complete", stage="parsing", duration_ms=1234)
```

---

## Configuration (YAML)

### Example
```yaml
# pipeline.yaml
source:
  language: python
  patterns:
    - "src/**/*.py"
    - "!tests/"

output:
  format: markdown
  sections:
    - readme
    - api
    - architecture

documentation:
  title: "Universal Agent Nexus"
  description: "AI agent orchestration framework"
  template_dir: ./templates/
  
validation:
  skip: false
  check_links: true
  lint_markdown: true
```

---

## Multi-Repo Support (Your Ecosystem)

### Architecture
You have multiple repos:
- `universal_agent_nexus` (Python agents)
- `universal_agent_examples` (Python examples)
- `universal_agent_fabric` (Python framework)
- C# ETRM backend
- Market-data platform

### Pipeline Per Repo
```bash
# Generate docs for each
for repo in nexus examples fabric; do
  docker run --rm \
    -v ~/projects/$repo:/workspace/source:ro \
    -v ~/projects/docs-output/$repo:/workspace/output:rw \
    docs-pipeline:latest \
    generate --source-path /workspace/source --output-path /workspace/output
done

# Unified site generated from output/
```

---

## CI/CD Integration (GitHub Actions)

```yaml
name: Generate Docs
on:
  push:
    paths: ["src/**", "docs/**"]

jobs:
  generate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Build image
        run: docker build -t docs-pipeline:${{ github.sha }} .
      
      - name: Generate docs
        run: |
          docker run --rm \
            -v $GITHUB_WORKSPACE/source:/workspace/source:ro \
            -v $GITHUB_WORKSPACE/output:/workspace/output:rw \
            docs-pipeline:${{ github.sha }} \
            generate --source-path /workspace/source --output-path /workspace/output
      
      - name: Validate
        run: |
          docker run --rm \
            -v $GITHUB_WORKSPACE/output:/workspace/output:ro \
            docs-pipeline:${{ github.sha }} \
            validate --output-path /workspace/output
      
      - name: Upload artifact
        uses: actions/upload-artifact@v4
        with:
          name: generated-docs
          path: output/
```

---

## Quick Reference

### File Organization
```
docs-pipeline/
├── docs_pipeline/cli.py              # Entry point
├── docs_pipeline/core/{parser,extractor,analyzer}.py
├── docs_pipeline/generators/{readme,api,architecture,changelog}.py
├── docs_pipeline/models/{codebase,module,function_sig,config}.py
├── docs_pipeline/pipeline/{orchestrator,stages,handlers}.py
├── docs_pipeline/utils/{logging,git,validators}.py
├── Dockerfile                        # Multi-stage
├── docker-compose.yml
├── pyproject.toml                    # Config, deps
├── tests/{unit,integration,fixtures}/
└── README.md
```

### Key Modules
- **core/parser.py** → AST analysis, metadata extraction
- **generators/readme_gen.py** → Project overview + quick-start
- **generators/api_doc_gen.py** → Function/class reference
- **generators/architecture_gen.py** → System design + data flow
- **pipeline/orchestrator.py** → Coordinates all stages
- **pipeline/handlers.py** → Error recovery, retry logic

### Common Tasks
```bash
# Lint
black docs_pipeline/ && flake8 docs_pipeline/

# Type check
mypy docs_pipeline/ --strict

# Test
pytest tests/ --cov=docs_pipeline --cov-report=html

# Build Docker
docker build -t docs-pipeline:latest .

# Full generate
python -m docs_pipeline.cli generate \
  --source-path ./universal_agent_nexus \
  --output-path ./output/nexus
```

---

## Versioning & Dependencies

### pyproject.toml
```toml
[project]
name = "docs-pipeline"
version = "2.0.0"

[project.dependencies]
pydantic = ">=2.0"
jinja2 = ">=3.1"
click = ">=8.1"        # CLI
structlog = ">=23.1"   # Logging

[project.optional-dependencies]
dev = [
    "pytest>=7.4",
    "pytest-cov>=4.1",
    "black>=23.9",
    "flake8>=6.0",
    "mypy>=1.5",
    "bandit>=1.7"
]
```

---

## Debugging

### Structured Logs
```bash
# Set log level
LOG_LEVEL=DEBUG python -m docs_pipeline.cli generate --source-path ./src

# Parse logs (JSON)
jq 'select(.event == "error")' pipeline.log
```

### State Dumps
```bash
# On fatal error, check:
cat debug/state-dump.json       # Full pipeline state
cat debug/parsing-errors.txt    # Parse failures
```

### Docker Debug
```bash
# Interactive shell
docker run -it --rm -v $(pwd)/src:/workspace/source docs-pipeline:latest bash

# Run with verbose logging
docker run --rm -e LOG_LEVEL=DEBUG docs-pipeline:latest generate ...
```

---

## Summary

✅ **Zero-interaction**: CLI + Docker handles everything  
✅ **Type-safe**: Pydantic models, type hints throughout  
✅ **Extensible**: Add new generators without core changes  
✅ **Observable**: Structured JSON logging  
✅ **Tested**: 80%+ coverage, fixtures included  
✅ **Production-ready**: Error recovery, graceful degradation  

**Status**: Ready for multi-repo doc generation across your ecosystem  
