.PHONY: help venv venv-test install run clean test test-slow test-cov lint check security-audit generate-mcp-fixtures check-mcp-fixtures

.DEFAULT_GOAL := help

PYTHON := python3
PYTHON_VERSION := $(shell $(PYTHON) -c 'import sys; print("%d.%d" % sys.version_info[:2])')
VENV := .venv
BIN := $(VENV)/bin
VENV_MARKER := $(VENV)/.initialized-$(PYTHON_VERSION)
PYTEST_ARGS ?=

help: ## Show available make targets
	@grep -E '^[a-zA-Z0-9_.-]+:.*?##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2}'

venv: $(VENV_MARKER) ## Create Python virtual environment

$(VENV_MARKER):
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m ensurepip --upgrade
	$(BIN)/python -m pip install --upgrade pip
	touch "$(VENV_MARKER)"

venv-test: $(VENV_MARKER) ## Install pytest, flake8, and test tooling into the venv
	$(BIN)/python -m pip install pytest flake8 pytest-cov pytest-timeout

install: $(VENV_MARKER) venv-test ## Install application and test dependencies
	$(BIN)/python -m pip install -r requirements.txt

run: $(VENV_MARKER) ## Run the PyPost desktop application
	PYTHONPATH=. $(BIN)/python pypost/main.py

test: $(VENV_MARKER) ## Run fast test suite (excludes slow integration tests)
	QT_QPA_PLATFORM=offscreen $(BIN)/python -m pytest \
		$(if $(PYTEST_ARGS),$(PYTEST_ARGS),tests/ -m "not slow")

test-slow: $(VENV_MARKER) ## Run slow integration tests only (Makefile install smoke)
	QT_QPA_PLATFORM=offscreen $(BIN)/python -m pytest \
		$(if $(PYTEST_ARGS),$(PYTEST_ARGS),tests/ -m slow)

test-cov: $(VENV_MARKER) venv-test ## Run fast tests with coverage report
	QT_QPA_PLATFORM=offscreen $(BIN)/python -m pytest \
		$(if $(PYTEST_ARGS),$(PYTEST_ARGS),tests/ \
		--cov=pypost --cov-report=term-missing --cov-report=html:htmlcov)

lint: $(VENV_MARKER) ## Run flake8 static analysis on pypost/
	$(BIN)/python -m flake8 --jobs=1 pypost/

check: lint test ## Convenience quality gate: static analysis + full test suite

security-audit: install ## Scan production dependencies for known CVEs (mirrors CI)
	$(BIN)/python -m pip install pip-audit
	$(BIN)/pip-audit -r requirements.txt

generate-mcp-fixtures: $(VENV_MARKER) ## Regenerate MCP test collection and environment JSON fixtures
	$(BIN)/python scripts/generate_mcp_test_fixtures.py

check-mcp-fixtures: $(VENV_MARKER) ## Verify committed MCP test fixtures match canonical builders
	$(BIN)/python scripts/generate_mcp_test_fixtures.py --check

clean: ## Remove virtual environment and Python cache directories
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
