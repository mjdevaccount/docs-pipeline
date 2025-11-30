# Contributing to Documentation Pipeline

Thank you for considering contributing! This project welcomes contributions from the community.

## How to Contribute

1. **Fork the repository**

2. **Create a feature branch**: `git checkout -b feature/amazing-feature`

3. **Make your changes**

4. **Add tests** for new functionality

5. **Ensure tests pass**: `python -m pytest`

6. **Commit**: `git commit -m 'Add amazing feature'`

7. **Push**: `git push origin feature/amazing-feature`

8. **Open a Pull Request**

## Development Setup

**Clone your fork:**
```bash
git clone https://github.com/YOUR-USERNAME/docs-pipeline.git
cd docs-pipeline
```

**Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

**Install dev dependencies:**
```bash
pip install -e ".[dev,pdf,ai,structurizr]"
```

**Run tests:**
```bash
pytest
```

## Code Standards

### Python Style

- Follow PEP 8
- Use type hints on all functions
- Google-style docstrings
- Line length: 100 characters

### Architecture

- Follow SOLID principles
- One class/module per responsibility
- Interfaces for extensibility
- Dependency injection over global state

### Testing

- Unit tests for business logic
- Integration tests for workflows
- 80%+ code coverage
- Test file naming: `test_*.py`

### Commits

- Use conventional commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`
- Reference issues: `fixes #123`
- Keep commits atomic and focused

## Areas for Contribution

### High Priority

- [ ] GitHub Actions CI/CD pipeline
- [ ] Docker containerization
- [ ] Additional document profiles
- [ ] More AI agent types
- [ ] Performance benchmarking

### Medium Priority

- [ ] Web UI for non-technical users
- [ ] REST API wrapper
- [ ] Additional diagram formats
- [ ] Internationalization
- [ ] Cloud storage integration

### Documentation

- [ ] Video tutorials
- [ ] API reference docs
- [ ] More examples
- [ ] Migration guides

## Questions?

Open an issue or reach out to the maintainer.

