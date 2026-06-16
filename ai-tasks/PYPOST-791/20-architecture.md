# PYPOST-791: Architecture

## Design

Add `PYTEST_ARGS ?=` to the Makefile. When non-empty, it **replaces** the default pytest
arguments for `test`, `test-slow`, and `test-cov`; when empty, behavior is unchanged.

```makefile
test: $(VENV_MARKER)
	QT_QPA_PLATFORM=offscreen $(BIN)/python -m pytest \
		$(if $(PYTEST_ARGS),$(PYTEST_ARGS),tests/ -m "not slow")
```

Replacement (not append) is required so `PYTEST_ARGS="tests/foo.py"` narrows the run
instead of union-collecting with `tests/`.

## Tests

- `test_pytest_args_narrows_test_run` in `tests/test_makefile.py`
- `_run_make` passes `PYTEST_ARGS=` to nested make calls to avoid MAKEFLAGS leakage
