.PHONY: help venv venv-test venv-otel install lock check-lock lock-dev check-lock-dev \
	lock-otel check-lock-otel run run-agent-ui-mcp clean test test-slow \
	test-mcp-collection-e2e test-jira-mcp-live check-jira-mcp-path-freshness \
	test-cov test-agent-e2e lint typecheck verify-ai-tasks check security-audit \
	generate-mcp-fixtures check-mcp-fixtures generate-license-inventory \
	check-license-inventory lint-docs check-docs-links

.DEFAULT_GOAL := help

PYTHON := python3
PYTHON_VERSION := $(shell $(PYTHON) -c 'import sys; print("%d.%d" % sys.version_info[:2])')
LOCK_PYTHON_VERSION ?= 3.11
UV ?= uv
VENV := .venv
BIN := $(VENV)/bin
VENV_MARKER := $(VENV)/.initialized-$(PYTHON_VERSION)
VENV_TEST_STAMP := $(VENV)/.venv-test-$(PYTHON_VERSION)
VENV_OTEL_STAMP := $(VENV)/.venv-otel-$(PYTHON_VERSION)
PYTEST_ARGS ?=

help: ## Show available make targets
	@grep -E '^[a-zA-Z0-9_.-]+:.*?##' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2}'

venv: $(VENV_MARKER) ## Create Python virtual environment

$(VENV_MARKER):
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m ensurepip --upgrade
	$(BIN)/python -m pip install --upgrade pip
	touch "$(VENV_MARKER)"

venv-test: $(VENV_TEST_STAMP) ## Install dev optional extra from pyproject.toml (pytest, flake8, etc.)

venv-otel: $(VENV_OTEL_STAMP) ## Install OpenTelemetry optional extra from pyproject.toml

$(VENV_TEST_STAMP): $(VENV_MARKER) pyproject.toml
	$(BIN)/python -m pip install -e ".[dev]"
	touch "$@"

$(VENV_OTEL_STAMP): $(VENV_MARKER) pyproject.toml
	$(BIN)/python -m pip install -e ".[otel]"
	touch "$@"

install: $(VENV_MARKER) ## Install editable package with dev and OTel extras
	$(BIN)/python -m pip install -e ".[dev,otel]"
	touch "$(VENV_TEST_STAMP)" "$(VENV_OTEL_STAMP)"

lock: ## Regenerate requirements.txt transitive lock from requirements.in
	$(UV) pip compile requirements.in -o requirements.txt --python-version $(LOCK_PYTHON_VERSION)

check-lock: ## Verify requirements.txt matches requirements.in (needs uv on PATH)
	@attempt=1; max_attempts=3; delay=1; \
	while [ $$attempt -le $$max_attempts ]; do \
		if $(UV) pip compile requirements.in -o requirements.txt.check \
			--python-version $(LOCK_PYTHON_VERSION); then \
			break; \
		fi; \
		if [ $$attempt -eq $$max_attempts ]; then \
			echo "check-lock: uv pip compile failed after" \
				"$$max_attempts attempts (network or tool issue)" >&2; \
			rm -f requirements.txt.check requirements.txt.body requirements.txt.check.body; \
			exit 2; \
		fi; \
		echo "check-lock: uv pip compile attempt $$attempt/$$max_attempts failed," \
			"retrying in $${delay}s..." >&2; \
		sleep $$delay; \
		attempt=$$((attempt + 1)); \
		delay=$$((delay * 2)); \
	done
	tail -n +3 requirements.txt > requirements.txt.body
	tail -n +3 requirements.txt.check > requirements.txt.check.body
	@if ! diff -q requirements.txt.body requirements.txt.check.body > /dev/null; then \
		echo "check-lock: requirements.txt is stale relative to requirements.in" \
			"(run 'make lock' and commit)" >&2; \
		rm -f requirements.txt.check requirements.txt.body requirements.txt.check.body; \
		exit 1; \
	fi
	rm -f requirements.txt.check requirements.txt.body requirements.txt.check.body

lock-dev: ## Regenerate requirements-dev.txt transitive lock from requirements-dev.in
	$(UV) pip compile requirements-dev.in -o requirements-dev.txt --python-version $(LOCK_PYTHON_VERSION)

check-lock-dev: ## Verify requirements-dev.txt matches requirements-dev.in (needs uv on PATH)
	@attempt=1; max_attempts=3; delay=1; \
	while [ $$attempt -le $$max_attempts ]; do \
		if $(UV) pip compile requirements-dev.in -o requirements-dev.txt.check \
			--python-version $(LOCK_PYTHON_VERSION); then \
			break; \
		fi; \
		if [ $$attempt -eq $$max_attempts ]; then \
			echo "check-lock-dev: uv pip compile failed after" \
				"$$max_attempts attempts (network or tool issue)" >&2; \
			rm -f requirements-dev.txt.check requirements-dev.txt.body requirements-dev.txt.check.body; \
			exit 2; \
		fi; \
		echo "check-lock-dev: uv pip compile attempt $$attempt/$$max_attempts failed," \
			"retrying in $${delay}s..." >&2; \
		sleep $$delay; \
		attempt=$$((attempt + 1)); \
		delay=$$((delay * 2)); \
	done
	tail -n +3 requirements-dev.txt > requirements-dev.txt.body
	tail -n +3 requirements-dev.txt.check > requirements-dev.txt.check.body
	@if ! diff -q requirements-dev.txt.body requirements-dev.txt.check.body > /dev/null; then \
		echo "check-lock-dev: requirements-dev.txt is stale relative to requirements-dev.in" \
			"(run 'make lock-dev' and commit)" >&2; \
		rm -f requirements-dev.txt.check requirements-dev.txt.body requirements-dev.txt.check.body; \
		exit 1; \
	fi
	rm -f requirements-dev.txt.check requirements-dev.txt.body requirements-dev.txt.check.body

lock-otel: ## Regenerate requirements-otel.txt transitive lock from requirements-otel.in
	$(UV) pip compile requirements-otel.in -o requirements-otel.txt --python-version $(LOCK_PYTHON_VERSION)

check-lock-otel: ## Verify requirements-otel.txt matches requirements-otel.in (needs uv on PATH)
	@attempt=1; max_attempts=3; delay=1; \
	while [ $$attempt -le $$max_attempts ]; do \
		if $(UV) pip compile requirements-otel.in -o requirements-otel.txt.check \
			--python-version $(LOCK_PYTHON_VERSION); then \
			break; \
		fi; \
		if [ $$attempt -eq $$max_attempts ]; then \
			echo "check-lock-otel: uv pip compile failed after" \
				"$$max_attempts attempts (network or tool issue)" >&2; \
			rm -f requirements-otel.txt.check requirements-otel.txt.body requirements-otel.txt.check.body; \
			exit 2; \
		fi; \
		echo "check-lock-otel: uv pip compile attempt $$attempt/$$max_attempts failed," \
			"retrying in $${delay}s..." >&2; \
		sleep $$delay; \
		attempt=$$((attempt + 1)); \
		delay=$$((delay * 2)); \
	done
	tail -n +3 requirements-otel.txt > requirements-otel.txt.body
	tail -n +3 requirements-otel.txt.check > requirements-otel.txt.check.body
	@if ! diff -q requirements-otel.txt.body requirements-otel.txt.check.body > /dev/null; then \
		echo "check-lock-otel: requirements-otel.txt is stale relative to requirements-otel.in" \
			"(run 'make lock-otel' and commit)" >&2; \
		rm -f requirements-otel.txt.check requirements-otel.txt.body requirements-otel.txt.check.body; \
		exit 1; \
	fi
	rm -f requirements-otel.txt.check requirements-otel.txt.body requirements-otel.txt.check.body

run: $(VENV_MARKER) ## Run the PyPost desktop application
	PYTHONPATH=. $(BIN)/python pypost/main.py

run-agent-ui-mcp: $(VENV_MARKER) ## Stdio MCP sidecar for agent UI actions (PYPOST-952)
	QT_QPA_PLATFORM=offscreen PYTHONPATH=. $(BIN)/python -m pypost.agent.ui_actions_mcp

test: $(VENV_MARKER) venv-test venv-otel ## Run fast test suite (excludes slow integration tests)
	QT_QPA_PLATFORM=offscreen $(BIN)/python -m pytest \
		$(if $(PYTEST_ARGS),$(PYTEST_ARGS),tests/ -m "not slow")

test-slow: $(VENV_MARKER) venv-test venv-otel ## Run slow integration tests only (Makefile install smoke)
	QT_QPA_PLATFORM=offscreen $(BIN)/python -m pytest \
		$(if $(PYTEST_ARGS),$(PYTEST_ARGS),tests/ -m slow)

test-mcp-collection-e2e: $(VENV_MARKER) venv-test venv-otel ## Run Jira MCP e2e
	QT_QPA_PLATFORM=offscreen $(BIN)/python -m pytest tests/test_mcp_collection_e2e.py

test-jira-mcp-live: $(VENV_MARKER) venv-test venv-otel ## Run the explicitly opted-in read-only Jira MCP smoke
	QT_QPA_PLATFORM=offscreen $(BIN)/python -m pytest tests/test_jira_mcp_live_smoke.py -m live_jira

check-jira-mcp-path-freshness: $(VENV_MARKER) venv-test venv-otel ## Offline jira_mcp critical REST paths vs locked catalog (PYPOST-1030)
	QT_QPA_PLATFORM=offscreen $(BIN)/python -m pytest \
		tests/test_example_fixtures.py::test_jira_mcp_critical_rest_paths_match_locked_catalog \
		tests/test_example_fixtures.py::test_jira_mcp_critical_rest_paths_rejects_url_drift -q

test-cov: $(VENV_MARKER) venv-test venv-otel ## Run fast tests with coverage report
	QT_QPA_PLATFORM=offscreen $(BIN)/python -m pytest \
		$(if $(PYTEST_ARGS),$(PYTEST_ARGS),tests/ \
		--cov=pypost --cov-report=term-missing --cov-report=html:htmlcov)

test-agent-e2e: $(VENV_MARKER) venv-test venv-otel ## Broader agent e2e beyond golden (-m agent_e2e; PYTEST_ARGS overrides)
	QT_QPA_PLATFORM=offscreen $(BIN)/python -m pytest \
		$(if $(PYTEST_ARGS),$(PYTEST_ARGS),-m "agent_e2e and not slow")

lint-docs: $(VENV_MARKER) ## Run Markdown formatting checks on doc/user/ and doc/README.md (PYPOST-1020)
	$(BIN)/python scripts/lint_user_docs.py
	$(BIN)/python scripts/check_user_docs_links.py

check-docs-links: $(VENV_MARKER) ## Check relative links in User Guide and README files (PYPOST-1021)
	$(BIN)/python scripts/check_user_docs_links.py

lint: $(VENV_MARKER) venv-test ## Run flake8 static analysis on pypost/ and documentation checks
	$(BIN)/python -m flake8 --jobs=1 pypost/
	$(BIN)/python scripts/lint_user_docs.py
	$(BIN)/python scripts/check_user_docs_links.py

typecheck: $(VENV_MARKER) venv-test ## Optional mypy on pypost/core/, models/, and ui/ (baseline gate)
	$(BIN)/python scripts/check_mypy_baseline.py

verify-ai-tasks: $(VENV_MARKER) ## Verify closed ai-tasks folders have required workflow artifacts
	$(BIN)/python scripts/verify_ai_task_artifacts.py

check: lint test verify-ai-tasks ## Convenience quality gate: static analysis + full test suite

security-audit: install ## Scan production dependencies for known CVEs (mirrors CI)
	$(BIN)/pip-audit -r requirements.txt

generate-mcp-fixtures: $(VENV_MARKER) ## Regenerate MCP test collection and environment JSON fixtures
	$(BIN)/python scripts/generate_mcp_test_fixtures.py

check-mcp-fixtures: $(VENV_MARKER) ## Verify committed MCP test fixtures match canonical builders
	$(BIN)/python scripts/generate_mcp_test_fixtures.py --check

generate-license-inventory: install ## Regenerate LICENSES/transitive.csv from requirements.txt
	$(BIN)/python scripts/generate_license_inventory.py

check-license-inventory: install ## Verify LICENSES/transitive.csv matches production lock (mirrors CI)
	$(BIN)/python scripts/generate_license_inventory.py --check

refresh-ci-duration-evidence: $(VENV_MARKER) ## Print agent-e2e overlap timings from GitHub Actions (paste into testing.md)
	$(BIN)/python scripts/refresh_ci_duration_evidence.py

check-ci-duration-evidence: $(VENV_MARKER) ## Verify testing.md documents CI duration refresh procedure
	$(BIN)/python scripts/refresh_ci_duration_evidence.py --check

clean: ## Remove virtual environment and Python cache directories
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
