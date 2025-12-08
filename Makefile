.PHONY: venv install run clean test lint

PYTHON := python3
VENV := venv
BIN := $(VENV)/bin

# Create virtual environment
venv:
	$(PYTHON) -m venv $(VENV)
	$(BIN)/pip install --upgrade pip

# Install dependencies
install: venv
	$(BIN)/pip install -r requirements.txt

# Run application
run:
	PYTHONPATH=. $(BIN)/python pypost/main.py

# Run tests
test:
	$(BIN)/pytest tests/

# Linting
lint:
	$(BIN)/flake8 pypost/

# Clean
clean:
	rm -rf $(VENV)
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
