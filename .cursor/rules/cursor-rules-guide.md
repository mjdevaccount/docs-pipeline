# Cursor Rules Guide for docs-pipeline

## Overview

This guide documents all Cursor rules for zero-interaction documentation generation. Cursor automatically detects and loads these rules from `.cursor/rules/` when you open the repository.

## Rule Files

### 1. architecture.mdc
**Purpose**: System design, Docker stack, data flow, entry points

**Key Sections**:
- System overview and core principles
- Component breakdown (core, generators, pipeline, models)
- Data flow from source to output
- Docker architecture (images, volumes, entrypoint)
- CLI entry point with flags and exit codes

**When Cursor Uses It**:
- When generating code related to system architecture
- When understanding module organization
- When building new pipeline components
- When configuring Docker deployment

### 2. cli-workflows.mdc
**Purpose**: CLI commands, flags, workflows, error handling

**Key Sections**:
- Primary workflows (full pipeline, individual stages, watch mode, Docker execution)
- Flag reference (required and optional)
- Exit codes and their meanings
- Common patterns (CI/CD, local dev, dry-run validation)
- Error handling and structured logging
- Health check procedures

**When Cursor Uses It**:
- When implementing CLI commands
- When writing integration tests
- When setting up CI/CD pipelines
- When debugging workflow issues

### 3. docker-ops.mdc
**Purpose**: Container best practices, layer caching, registry ops, CI/CD integration

**Key Sections**:
- Multi-stage Dockerfile patterns
- Build optimization and layer caching
- .dockerignore configuration
- Volume mounting strategy
- Resource limits and security options
- Docker Compose setup
- Image size optimization
- Registry operations (Docker Hub, GitHub Container Registry, AWS ECR)
- Debugging techniques
- CI/CD integration (GitHub Actions, GitLab CI)

**When Cursor Uses It**:
- When writing or optimizing Dockerfile
- When setting up Docker Compose
- When configuring CI/CD pipelines
- When optimizing image size
- When debugging container issues

### 4. codegen-patterns.mdc
**Purpose**: Python standards, type hints, Pydantic, Jinja2, async patterns

**Key Sections**:
- Python standards (type hints, docstrings, context managers, error handling)
- Pydantic models (validation, serialization)
- Jinja2 template patterns (inheritance, custom filters)
- Code generation best practices

**When Cursor Uses It**:
- When generating Python code
- When creating data models
- When writing functions
- When building templates
- When implementing generators

### 5. testing-standards.mdc
**Purpose**: Unit/integration tests, fixtures, pre-commit, coverage, GitHub Actions

**Key Sections**:
- Test structure and organization
- Unit testing examples (parser, extractor)
- Integration testing (end-to-end pipeline)
- Pytest fixtures and configuration
- Code quality tools (pre-commit, mypy, black, flake8)
- Coverage standards (80%+ target)
- Docker testing
- GitHub Actions test matrix

**When Cursor Uses It**:
- When writing test code
- When setting up test infrastructure
- When configuring CI/CD validation
- When implementing fixtures
- When checking code quality

---

## How Cursor Uses These Rules

### Automatic Detection
When you open the repository, Cursor automatically:
1. Scans `.cursor/rules/` directory
2. Loads all `.mdc` files
3. Makes them available in its context
4. Applies relevant rules based on your queries

### Zero-Interaction Examples

**Example 1: Parser Implementation**
```
You: "Implement the parse stage for the parser module"

→ Cursor uses architecture.mdc (understands ModuleMetadata structure)
→ Uses codegen-patterns.mdc (adds type hints, Pydantic models, error handling)
→ Uses testing-standards.mdc (scaffolds corresponding unit tests)
→ References docker-ops.mdc (keeps containerization in mind)
```

**Example 2: Docker Configuration**
```
You: "Optimize the Dockerfile for production"

→ Cursor uses docker-ops.mdc (multi-stage build, layer caching)
→ References architecture.mdc (correct base image, entrypoint)
→ Considers cli-workflows.mdc (health check implementation)
```

**Example 3: CLI Enhancement**
```
You: "Add a new --validate flag to the CLI"

→ Cursor uses cli-workflows.mdc (flag patterns, exit codes)
→ References architecture.mdc (CLI entry point structure)
→ Uses codegen-patterns.mdc (type hints, error handling)
→ Uses testing-standards.mdc (test the new flag)
```

**Example 4: Test Suite**
```
You: "Write tests for the generator module"

→ Cursor uses testing-standards.mdc (fixture patterns, coverage)
→ References codegen-patterns.mdc (async patterns if needed)
→ Uses architecture.mdc (understands generator components)
```

---

## Common Commands Your Rules Enable

### Full Pipeline (Zero-Interaction)
```bash
# Local execution
python -m docs_pipeline.cli generate \
  --source-path /path/to/repo \
  --output-path ./output/docs \
  --config ./config/pipeline.yaml \
  --log-level INFO

# Docker execution
docker run --rm \
  -v $(pwd)/source:/workspace/source:ro \
  -v $(pwd)/output:/workspace/output:rw \
  docs-pipeline:latest \
  generate --source-path /workspace/source --output-path /workspace/output
```

### Development & Testing
```bash
# Watch mode (auto-rebuild on changes)
python -m docs_pipeline.cli generate \
  --source-path ./src \
  --output-path ./output/docs \
  --watch \
  --log-level DEBUG

# Validation only
python -m docs_pipeline.cli generate \
  --source-path ./src \
  --output-path ./output/docs \
  --dry-run

# Health check
python -m docs_pipeline.cli health-check
```

### Testing & Quality
```bash
# Run tests with coverage
pytest --cov=docs_pipeline tests/

# Code quality checks
black --check src/ tests/
flake8 src/ tests/
mypy src/ --strict

# Pre-commit hooks
pre-commit run --all-files
```

### Docker Operations
```bash
# Build image
docker build -t docs-pipeline:latest .

# Run with Docker Compose
docker-compose up --build docs-generator

# Push to registry
docker push ghcr.io/mjdevaccount/docs-pipeline:latest

# Interactive debugging
docker run -it --rm docs-pipeline:latest bash
```

---

## Integration with Your Workflow

### Code Generation
When generating new code:
1. Cursor analyzes the context using these rules
2. Applies Python standards (type hints, docstrings)
3. Uses Pydantic patterns for data models
4. Includes comprehensive error handling
5. Generates corresponding tests

### Architecture Decisions
When planning components:
1. Cursor understands the system data flow
2. Knows Docker architecture constraints
3. References CLI workflows for integration points
4. Maintains consistency with existing patterns

### Testing & CI/CD
When setting up validation:
1. Cursor knows 80%+ coverage target
2. Uses pre-commit hook patterns
3. Understands GitHub Actions workflows
4. Includes proper Docker testing

---

## Best Practices

### When Writing Queries
- **Be specific**: "Add type hints to the parser module" (better than "fix parser")
- **Reference rules**: "Per docker-ops.mdc, optimize the Dockerfile"
- **Include context**: "For the orchestrator stage, implement retry logic"

### For Team Members
- All rules are version-controlled in `.cursor/rules/`
- No need to explain system architecture—Cursor knows it
- Changes to rules should be committed alongside code
- Keep rules updated as architecture evolves

### Maintenance
- Review rules quarterly for accuracy
- Update when adding new patterns or standards
- Remove deprecated or obsolete patterns
- Solicit feedback from team on missing guidance

---

## Troubleshooting

**Rules not loading?**
- Check `.cursor/rules/` exists in repo root
- Verify `.mdc` file format is correct
- Restart Cursor
- Check Cursor documentation for rule loading issues

**Cursor ignoring a rule?**
- Ensure rule file is in `.cursor/rules/`
- Check file extension is `.mdc`
- Verify content matches rule syntax
- Consider splitting very large rules into separate files

**Rules conflict?**
- Rules are applied contextually—no hard conflicts
- More specific rules take precedence
- If unclear, mention specific rule in query

---

## File Structure

```
.cursor/
└── rules/
    ├── architecture.mdc          (system design, 2906 chars)
    ├── cli-workflows.mdc         (CLI patterns, 4275 chars)
    ├── docker-ops.mdc            (container ops, 5628 chars)
    ├── codegen-patterns.mdc      (Python/code gen, 3535 chars)
    ├── testing-standards.mdc     (testing patterns, 9338 chars)
    └── cursor-rules-guide.md     (this file, comprehensive reference)
```

**Total**: ~32KB of production-grade guidance for zero-interaction development

---

## Summary

These cursor rules enable:
✅ **Type-safe Python code** (mandatory type hints)
✅ **Production Docker containers** (multi-stage, optimized)
✅ **Comprehensive testing** (80%+ coverage, fixtures)
✅ **Clear CLI workflows** (documented commands, exit codes)
✅ **Zero context loss** (Cursor knows your entire system)

No more "how do I set this up?" questions—Cursor has the context.
