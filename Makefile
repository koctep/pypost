.PHONY: help venv venv-test install lock check-lock lock-dev check-lock-dev run clean test test-slow test-cov lint check security-audit generate-mcp-fixtures check-mcp-fixtures

.DEFAULT_GOAL := help

PYTHON := python3
PYTHON_VERSION := $(shell $(PYTHON) -c 'import sys; print("%d.%d" % sys.version_info[:2])')
LOCK_PYTHON_VERSION ?= 3.11
UV ?= uv
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

venv-test: $(VENV_MARKER) ## Install pinned test and lint tooling from requirements-dev.txt
	$(BIN)/python -m pip install -r requirements-dev.txt

install: $(VENV_MARKER) venv-test ## Install application and test dependencies
	$(BIN)/python -m pip install -r requirements.txt

lock: ## Regenerate requirements.txt transitive lock from requirements.in
	$(UV) pip compile requirements.in -o requirements.txt --python-version $(LOCK_PYTHON_VERSION)

check-lock: ## Verify requirements.txt matches requirements.in (needs uv on PATH)
	$(UV) pip compile requirements.in -o requirements.txt.check --python-version $(LOCK_PYTHON_VERSION)
	tail -n +3 requirements.txt > requirements.txt.body
	tail -n +3 requirements.txt.check > requirements.txt.check.body
	diff -q requirements.txt.body requirements.txt.check.body
	rm -f requirements.txt.check requirements.txt.body requirements.txt.check.body

lock-dev: ## Regenerate requirements-dev.txt transitive lock from requirements-dev.in
	$(UV) pip compile requirements-dev.in -o requirements-dev.txt --python-version $(LOCK_PYTHON_VERSION)

check-lock-dev: ## Verify requirements-dev.txt matches requirements-dev.in (needs uv on PATH)
	$(UV) pip compile requirements-dev.in -o requirements-dev.txt.check --python-version $(LOCK_PYTHON_VERSION)
	tail -n +3 requirements-dev.txt > requirements-dev.txt.body
	tail -n +3 requirements-dev.txt.check > requirements-dev.txt.check.body
	diff -q requirements-dev.txt.body requirements-dev.txt.check.body
	rm -f requirements-dev.txt.check requirements-dev.txt.body requirements-dev.txt.check.body

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
