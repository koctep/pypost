# PYPOST-736: Architecture

## Approach

Added a "Run lint" step to the existing `test` job in `.github/workflows/test.yml`,
placed after dependency installation and before the (slower) test run so lint
failures surface fast.

Uses `python -m flake8 --jobs=1 pypost/` directly (not `make lint`) because CI
installs dependencies straight into the runner's Python — there is no `.venv` for
`make`'s `$(BIN)/python` to resolve. `flake8` was already present in the
"Install test tools" step, so no new dependency was added.

Runs once per matrix entry (Python 3.11 and 3.13), which incidentally also catches
any version-specific flake8/pyflakes false positives.
