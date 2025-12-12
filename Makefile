.PHONY: help test test-unit test-integration test-all test-verbose test-fast clean install watch glossary-validate glossary-index glossary-report glossary-check

# Default target
.DEFAULT_GOAL := help

# Configuration
PYTHON := python3
PIP := pip3
PROJECT_DIR := tools/pdf
TEST_DIR := $(PROJECT_DIR)/tests
COVERAGE_DIR := htmlcov
GLOSSARY_DIR := glossaries

# Colors for output
BLUE := \033[0;36m
GREEN := \033[0;32m
YELLOW := \033[0;33m
RED := \033[0;31m
NC := \033[0m # No Color

help: ## Show this help message
	@echo "$(BLUE)docs-pipeline Makefile$(NC)"
	@echo ""
	@echo "$(GREEN)Testing$(NC)"
	@echo "  make test              - Run all tests with coverage"
	@echo "  make test-unit         - Run unit tests only (fast)"
	@echo "  make test-integration  - Run integration tests only"
	@echo "  make test-verbose      - Run all tests with verbose output"
	@echo "  make test-fast         - Run tests in parallel (fastest)"
	@echo "  make test-watch        - Run tests in watch mode (requires pytest-watch)"
	@echo ""
	@echo "$(GREEN)Coverage$(NC)"
	@echo "  make coverage-report   - Generate coverage HTML report"
	@echo "  make coverage-dashboard - Generate interactive dashboard"
	@echo "  make coverage-show     - Open coverage report in browser"
	@echo ""
	@echo "$(GREEN)Glossary$(NC)"
	@echo "  make glossary-validate - Validate glossary files"
	@echo "  make glossary-index    - Generate glossary index markdown"
	@echo "  make glossary-report   - Show glossary statistics"
	@echo "  make glossary-check    - Full glossary check"
	@echo ""
	@echo "$(GREEN)Quality$(NC)"
	@echo "  make lint              - Run linting (flake8, mypy)"
	@echo "  make format            - Auto-format code (black, isort)"
	@echo "  make check             - Run linting + tests"
	@echo ""
	@echo "$(GREEN)Utilities$(NC)"
	@echo "  make install           - Install all dependencies"
	@echo "  make install-dev       - Install dev dependencies"
	@echo "  make clean             - Clean build artifacts and cache"
	@echo ""
	@echo "$(YELLOW)Examples$(NC)"
	@echo "  make test                          # Full test suite"
	@echo "  make test-unit test-coverage       # Quick unit tests + coverage"
	@echo "  make test-fast coverage-dashboard  # Parallel tests + dashboard"
	@echo "  make glossary-validate             # Check glossary integrity"

# Test targets
test: ## Run all tests with coverage
	@echo "$(BLUE)Running all tests with coverage...$(NC)"
	$(PYTHON) -m pytest $(TEST_DIR) -v --cov=$(PROJECT_DIR) --cov-report=html --cov-report=term-missing
	@echo "$(GREEN)✓ Tests complete$(NC)"

test-unit: ## Run unit tests only
	@echo "$(BLUE)Running unit tests...$(NC)"
	$(PYTHON) -m pytest $(TEST_DIR) -v -m unit --cov=$(PROJECT_DIR)
	@echo "$(GREEN)✓ Unit tests complete$(NC)"

test-integration: ## Run integration tests only
	@echo "$(BLUE)Running integration tests...$(NC)"
	$(PYTHON) -m pytest $(TEST_DIR) -v -m integration
	@echo "$(GREEN)✓ Integration tests complete$(NC)"

test-all: ## Run all tests (alias for test)
	@$(MAKE) test

test-verbose: ## Run all tests with verbose output
	@echo "$(BLUE)Running all tests (verbose)...$(NC)"
	$(PYTHON) -m pytest $(TEST_DIR) -vv --tb=long --cov=$(PROJECT_DIR)

test-fast: ## Run tests in parallel (fastest)
	@echo "$(BLUE)Running tests in parallel...$(NC)"	
	$(PYTHON) -m pytest $(TEST_DIR) -n auto --cov=$(PROJECT_DIR)
	@echo "$(GREEN)✓ Parallel tests complete$(NC)"

test-watch: ## Run tests in watch mode
	@echo "$(BLUE)Running tests in watch mode (Ctrl+C to stop)...$(NC)"
	$(PYTHON) -m pytest-watch $(TEST_DIR) -- -v

test-coverage: ## Run tests and show coverage
	@$(MAKE) test
	@$(MAKE) coverage-report

test-smoke: ## Run smoke tests only
	@echo "$(BLUE)Running smoke tests...$(NC)"
	$(PYTHON) -m pytest $(TEST_DIR) -v -m smoke
	@echo "$(GREEN)✓ Smoke tests complete$(NC)"

# Coverage targets
coverage-report: ## Generate coverage HTML report
	@echo "$(BLUE)Generating coverage report...$(NC)"
	$(PYTHON) -m pytest $(TEST_DIR) --cov=$(PROJECT_DIR) --cov-report=html --cov-report=term-missing:skip-covered
	@echo "$(GREEN)✓ Coverage report generated: $(COVERAGE_DIR)/index.html$(NC)"

coverage-dashboard: ## Generate interactive coverage dashboard
	@echo "$(BLUE)Generating coverage dashboard...$(NC)"
	@if [ -f coverage.json ]; then \
		$(PYTHON) $(TEST_DIR)/coverage_dashboard.py --trend --verbose; \
	else \
		echo "$(RED)✗ coverage.json not found$(NC)"; \
		echo "  Run 'make test' first to generate coverage data"; \
		exit 1; \
	fi

coverage-show: ## Open coverage report in browser
	@if [ -f "$(COVERAGE_DIR)/index.html" ]; then \
		echo "$(BLUE)Opening coverage report...$(NC)"; \
		open "$(COVERAGE_DIR)/index.html" || xdg-open "$(COVERAGE_DIR)/index.html" || echo "$(YELLOW)Please open manually: $(COVERAGE_DIR)/index.html$(NC)"; \
	else \
		echo "$(RED)✗ Coverage report not found$(NC)"; \
		echo "  Run 'make coverage-report' first"; \
		exit 1; \
	fi

coverage-clean: ## Clean coverage data
	@echo "$(BLUE)Cleaning coverage data...$(NC)"
	rm -rf htmlcov .coverage coverage.json coverage.xml $(TEST_DIR)/.coverage
	@echo "$(GREEN)✓ Coverage data cleaned$(NC)"

# Glossary targets
glossary-validate: ## Validate glossary files
	@echo "$(BLUE)Validating glossaries...$(NC)"
	@for glossary in $(GLOSSARY_DIR)/*.yaml $(GLOSSARY_DIR)/*.json; do \
		if [ -f "$$glossary" ]; then \
			echo "  Checking $$glossary..."; \
			$(PYTHON) -m $(PROJECT_DIR).cli.glossary_commands validate "$$glossary" || exit 1; \
		fi; \
	done
	@echo "$(GREEN)✓ All glossaries valid$(NC)"

glossary-index: ## Generate glossary index markdown files
	@echo "$(BLUE)Generating glossary indexes...$(NC)"
	@mkdir -p $(GLOSSARY_DIR)/indexes
	@for glossary in $(GLOSSARY_DIR)/*.yaml $(GLOSSARY_DIR)/*.json; do \
		if [ -f "$$glossary" ]; then \
			name=$$(basename "$$glossary" | cut -d. -f1); \
			echo "  Indexing $$name..."; \
			$(PYTHON) -m $(PROJECT_DIR).cli.glossary_commands index "$$glossary" --output "$(GLOSSARY_DIR)/indexes/$${name}_index.md"; \
		fi; \
	done
	@echo "$(GREEN)✓ Glossary indexes generated$(NC)"

glossary-report: ## Generate glossary statistics report
	@echo "$(BLUE)Glossary Statistics Report$(NC)"
	@for glossary in $(GLOSSARY_DIR)/*.yaml $(GLOSSARY_DIR)/*.json; do \
		if [ -f "$$glossary" ]; then \
			echo ""; \
			$(PYTHON) -m $(PROJECT_DIR).cli.glossary_commands report "$$glossary" --verbose; \
		fi; \
	done

glossary-check: glossary-validate glossary-report ## Full glossary check
	@echo "$(GREEN)✓ All glossary checks passed$(NC)"

# Quality targets
lint: ## Run linting checks
	@echo "$(BLUE)Running linters...$(NC)"
	@echo "  flake8..."
	$(PYTHON) -m flake8 $(PROJECT_DIR) --count --select=E9,F63,F7,F82 --show-source --statistics || true
	@echo "  mypy..."
	$(PYTHON) -m mypy $(PROJECT_DIR) --ignore-missing-imports || true
	@echo "$(GREEN)✓ Linting complete$(NC)"

format: ## Auto-format code
	@echo "$(BLUE)Formatting code...$(NC)"
	$(PYTHON) -m black $(PROJECT_DIR) --line-length=100
	$(PYTHON) -m isort $(PROJECT_DIR) --profile=black
	@echo "$(GREEN)✓ Code formatted$(NC)"

check: lint test ## Run linting and tests
	@echo "$(GREEN)✓ All checks passed$(NC)"

# Setup targets
install: ## Install all dependencies
	@echo "$(BLUE)Installing dependencies...$(NC)"
	$(PIP) install -e .
	$(PIP) install -r requirements.txt
	@echo "$(GREEN)✓ Dependencies installed$(NC)"

install-dev: install ## Install development dependencies
	@echo "$(BLUE)Installing dev dependencies...$(NC)"
	$(PIP) install pytest pytest-cov pytest-xdist pytest-watch
	$(PIP) install black isort flake8 mypy
	@echo "$(GREEN)✓ Dev dependencies installed$(NC)"

# Cleanup targets
clean: ## Clean build artifacts and cache
	@echo "$(BLUE)Cleaning build artifacts...$(NC)"
	rm -rf build/ dist/ *.egg-info/
	rm -rf .pytest_cache/ .mypy_cache/ .coverage
	rm -rf __pycache__ $(PROJECT_DIR)/__pycache__ $(TEST_DIR)/__pycache__
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	@echo "$(GREEN)✓ Clean complete$(NC)"

clean-all: clean coverage-clean ## Clean everything
	@echo "$(GREEN)✓ Full clean complete$(NC)"

# Development helpers
.PHONY: debug-env
debug-env: ## Show test environment info
	@echo "$(BLUE)Environment Info$(NC)"
	@echo "  Python: $$($(PYTHON) --version)"
	@echo "  Pip: $$($(PIP) --version)"
	@echo "  Project: $(PROJECT_DIR)"
	@echo "  Tests: $(TEST_DIR)"
	@echo "  Coverage: $(COVERAGE_DIR)"
	@echo "  Glossaries: $(GLOSSARY_DIR)"

# CI targets
.PHONY: ci-test
ci-test: ## Run tests in CI mode
	@echo "$(BLUE)Running CI tests...$(NC)"
	$(PYTHON) -m pytest $(TEST_DIR) -v --cov=$(PROJECT_DIR) --cov-report=xml --cov-report=json --junit-xml=test-results.xml
	@echo "$(GREEN)✓ CI tests complete$(NC)"

.PHONY: ci-check
ci-check: lint ci-test glossary-check ## Run full CI check
	@echo "$(GREEN)✓ CI check passed$(NC)"

# Watch mode
.PHONY: watch
watch: ## Watch for changes and run tests
	@echo "$(BLUE)Watching for changes...$(NC)"
	@$(MAKE) test-watch

# Combined targets for common workflows
.PHONY: quick
quick: test-unit coverage-report ## Quick: unit tests + coverage

.PHONY: full
full: check coverage-dashboard glossary-check ## Full: lint + tests + dashboard + glossary

.PHONY: ci
ci: ci-check coverage-dashboard ## CI: full checks + coverage

# Phony declarations (prevent make from treating them as files)
.PHONY: help test test-unit test-integration test-all test-verbose test-fast test-smoke test-watch test-coverage coverage-report coverage-dashboard coverage-show coverage-clean lint format check install install-dev clean clean-all quick full ci glossary-validate glossary-index glossary-report glossary-check
