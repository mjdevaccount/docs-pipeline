# 🚀 Quick Start Guide
## Cache Metrics & Test Coverage Dashboard

**Priority 1 + Priority 2 Implementation**  
December 12, 2025

---

## In 30 Seconds

### See Cache Effectiveness
```bash
python -m tools.pdf.cli.main doc.md output.pdf --verbose
```

**Output**:
```
[OK] Created: output.pdf
[INFO] Cache Performance Report
       Hit Ratio: 75.0% (3/4)
       Time Saved: 1500ms
       Size Reduction: 38.4%
```

### See Test Quality
```bash
make test
```

**Output**:
```
======================== 25 passed in 4.32s ==========================
Coverage: 94.1%
✓ Tests complete
```

---

## Most Common Commands

### Testing

| Command | What It Does | Time |
|---------|-------------|------|
| `make test` | Full test suite | ~5s |
| `make test-unit` | Fast unit tests | ~2s |
| `make test-fast` | Parallel (faster) | ~2s |
| `make test-watch` | Auto-run on changes | Continuous |

### Coverage

| Command | What It Does |
|---------|----------|
| `make coverage-report` | HTML report in `htmlcov/` |
| `make coverage-dashboard` | Beautiful dashboard |
| `make coverage-show` | Open in browser |

### Development

| Command | What It Does |
|---------|----------|
| `make lint` | Check code quality |
| `make format` | Auto-format code |
| `make check` | Lint + tests |

---

## Installation (First Time)

```bash
# Install dev dependencies
make install-dev

# Verify setup
make test-unit
```

Done! Now you have:
- ✅ pytest configured
- ✅ Coverage tracking enabled
- ✅ Dashboard generator ready
- ✅ All automation set up

---

## Priority 1: Cache Metrics

### See How Much Caching Helps

**First Run** (no cache):
```bash
$ python -m tools.pdf.cli.main doc.md output.pdf --verbose

[INFO] Cache Performance Report
       Hit Ratio: 0.0% (0/5)
       Time Saved: 0ms
       Size Reduction: 0.0%
```

**Second Run** (fully cached):
```bash
$ python -m tools.pdf.cli.main doc.md output.pdf --verbose

[INFO] Cache Performance Report
       Hit Ratio: 100.0% (5/5)
       Time Saved: 2500ms
       Size Reduction: 38.4%
```

### Understanding the Metrics

- **Hit Ratio**: % of diagrams served from cache
  - 0% = all diagrams re-rendered
  - 100% = all diagrams from cache
  
- **Time Saved**: Estimated render time saved (ms)
  - ~500ms per diagram (estimate)
  - 5 diagrams = 2500ms saved
  
- **Size Reduction**: % smaller from caching
  - Depends on SVG optimization
  - Typical: 30-45% reduction

---

## Priority 2: Test Coverage Dashboard

### Generate Dashboard

```bash
# Run tests and generate coverage data
make test

# Generate beautiful dashboard
make coverage-dashboard

# Open in browser
make coverage-show
```

### Dashboard Shows

```
📊 Test Coverage Dashboard

Overall Coverage:   94.1%  [██████████░░]
Status:              ✅ Excellent
Lines Covered:      234/248
Missing Coverage:   14 lines

Modules:
  cache.py           97%  ✅ Excellent
  orchestrator.py    95%  ✅ Excellent  
  cli/main.py        92%  ✅ Excellent
  core/converter.py  87%  🟢 Good
```

### Color Meanings

- 🟢 **Good** (75-90%): Acceptable coverage
- ✅ **Excellent** (90%+): Excellent coverage
- 🟡 **Fair** (50-75%): Needs improvement
- 🔴 **Poor** (<50%): Needs work

---

## Daily Workflow

### Option 1: Watch Mode (Recommended)

```bash
# Terminal 1: Watch for changes
make watch

# Terminal 2: View dashboard
open coverage-dashboard.html

# Now just code - tests run automatically!
```

### Option 2: Quick Validation

```bash
# Before committing
make check

# Runs linting + tests
# Takes ~8 seconds
```

### Option 3: Fast Feedback

```bash
# During development
make test-unit

# Just unit tests
# Takes ~2 seconds
```

---

## Before Committing

```bash
# Full validation
make check

# This runs:
# 1. Linting (flake8, mypy)
# 2. Full test suite with coverage

# If all green, commit safely!
```

---

## For CI/CD Setup

### GitHub Actions

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - run: pip install -e . && make install-dev
      - run: make ci
      - uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
```

### Local CI Test

```bash
# Test your CI setup locally
make ci

# Runs:
# - Linting
# - Full tests
# - Coverage dashboard
# - Generates XML for CI systems
```

---

## Troubleshooting

### Tests won't run

```bash
# Make sure dependencies are installed
make install-dev

# Verify pytest works
python -m pytest --version
```

### Dashboard won't generate

```bash
# Dashboard needs coverage.json from tests
make test

# Then generate
make coverage-dashboard
```

### Slow tests

```bash
# Run in parallel
make test-fast

# Much faster!
```

### Cache metrics not showing

```bash
# Cache metrics only show with --verbose
python -m tools.pdf.cli.main doc.md out.pdf --verbose

# Without --verbose, runs silently (faster)
```

---

## Advanced Commands

### Run Specific Test Type

```bash
# Only unit tests
pytest -m unit

# Only integration tests  
pytest -m integration

# Only cache tests
pytest -m cache
```

### Generate Coverage Reports

```bash
# HTML report
make coverage-report
# Opens: htmlcov/index.html

# JSON (for dashboard)
coverage json

# XML (for CI systems)
coverage xml
```

### Parallel Testing

```bash
# Auto-detect CPU cores
make test-fast

# Or specific threads
pytest -n 4
```

### Watch Specific Files

```bash
# Watch and re-test on changes
pytest-watch

# With options
pytest-watch -- -v -k cache
```

---

## Key Files to Know

| File | Purpose |
|------|----------|
| `pytest.ini` | Pytest configuration |
| `Makefile` | Test automation |
| `tools/pdf/tests/coverage_dashboard.py` | Dashboard generator |
| `coverage.json` | Coverage data (generated) |
| `coverage-dashboard.html` | Dashboard (generated) |
| `htmlcov/index.html` | Coverage report (generated) |

---

## Quick Reference Card

```bash
# Testing
make test              # Full suite
make test-unit         # Fast
make test-fast         # Parallel
make test-watch        # Watch mode

# Coverage
make coverage-report   # HTML report
make coverage-dashboard # Dashboard
make coverage-show     # Open in browser

# Quality
make lint              # Check code
make format            # Format code
make check             # Lint + tests

# Setup
make install           # Install deps
make install-dev       # Install all
make clean             # Clean artifacts

# Cache Metrics (Priority 1)
python -m tools.pdf.cli.main doc.md out.pdf --verbose
```

---

## FAQ

**Q: How do I see cache metrics?**  
A: Add `--verbose` flag: `python -m tools.pdf.cli.main doc.md out.pdf --verbose`

**Q: How often should I run tests?**  
A: Use `make watch` for continuous testing during development

**Q: What's the difference between `make test` and `make test-fast`?**  
A: `test` is sequential (~5s), `test-fast` is parallel (~2s). Same results, faster.

**Q: Can I skip tests before committing?**  
A: You can, but don't. Run `make check` - takes ~8 seconds and catches bugs.

**Q: Where's the coverage dashboard?**  
A: Generated by `make coverage-dashboard` as `coverage-dashboard.html`

**Q: How do I track coverage over time?**  
A: The dashboard automatically tracks trends (last 30 days)

---

## Next Steps

1. **Try It Out**
   ```bash
   make install-dev
   make test
   make coverage-dashboard
   ```

2. **Set Up Watch Mode**
   ```bash
   # Terminal 1
   make watch
   
   # Terminal 2
   open coverage-dashboard.html
   ```

3. **See Cache Metrics**
   ```bash
   python -m tools.pdf.cli.main doc.md out.pdf --verbose
   ```

4. **Share with Team**
   - Show them the dashboard
   - Demonstrate cache metrics
   - Celebrate improved visibility!

---

## Support

For more details, see:
- `PRIORITY_1_IMPLEMENTATION_COMPLETE.md` - Cache metrics details
- `PRIORITY_2_IMPLEMENTATION_COMPLETE.md` - Dashboard details
- `PRIORITY_1_2_SUMMARY.md` - Complete overview

---

**Happy testing! 🗣️**
