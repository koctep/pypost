.PHONY: venv install run clean test test-cov lint

PYTHON ?= python3
MIN_PYTHON := 3.11
VENV := .venv
BIN := $(VENV)/bin
VENV_MARKER := $(VENV)/.initialized-$(MIN_PYTHON)

# Create virtual environment
venv: $(VENV_MARKER)

$(VENV_MARKER):
	@$(PYTHON) -c 'import sys; required = (3, 11); current = sys.version_info[:2]; assert current >= required, "Python 3.11+ is required (found %d.%d)" % current'
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m ensurepip --upgrade
	$(BIN)/python -m pip install --upgrade pip
	touch "$(VENV_MARKER)"

# Install project and development dependencies
install: $(VENV_MARKER)
	$(BIN)/python -m pip install -e ".[dev]"

# Run application
run: $(VENV_MARKER)
	$(BIN)/pypost

# Run tests
test: $(VENV_MARKER)
	QT_QPA_PLATFORM=offscreen $(BIN)/python -m pytest tests/

# Run tests with coverage report (requires pytest-cov)
test-cov: $(VENV_MARKER)
	QT_QPA_PLATFORM=offscreen $(BIN)/python -m pytest tests/ \
		--cov=pypost --cov-report=term-missing --cov-report=html:htmlcov

# Linting
lint: $(VENV_MARKER)
	$(BIN)/python -m ruff check pypost/

# Clean
clean:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
