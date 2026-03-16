.PHONY: venv venv-test install run clean test test-cov lint

PYTHON := python3
PYTHON_VERSION := $(shell $(PYTHON) -c 'import sys; print("%d.%d" % sys.version_info[:2])')
VENV := .venv
BIN := $(VENV)/bin
VENV_MARKER := $(VENV)/.initialized-$(PYTHON_VERSION)

# Create virtual environment
venv: $(VENV_MARKER)

$(VENV_MARKER):
	$(PYTHON) -m venv $(VENV)
	$(BIN)/python -m ensurepip --upgrade
	$(BIN)/python -m pip install --upgrade pip
	touch "$(VENV_MARKER)"

# Create test virtual environment tools
venv-test: $(VENV_MARKER)
	$(BIN)/python -m pip install pytest flake8 pytest-cov

# Install dependencies
install: $(VENV_MARKER) venv-test
	$(BIN)/python -m pip install -r requirements.txt

# Run application
run: $(VENV_MARKER)
	PYTHONPATH=. $(BIN)/python pypost/main.py

# Run tests
test: $(VENV_MARKER)
	QT_QPA_PLATFORM=offscreen $(BIN)/python -m pytest tests/

# Run tests with coverage report (requires pytest-cov)
test-cov: $(VENV_MARKER)
	QT_QPA_PLATFORM=offscreen $(BIN)/python -m pytest tests/ \
		--cov=pypost --cov-report=term-missing --cov-report=html:htmlcov

# Linting
lint: $(VENV_MARKER)
	$(BIN)/python -m flake8 --jobs=1 pypost/

# Clean
clean:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
