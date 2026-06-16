# PYPOST-791: Add PYTEST_ARGS passthrough to Makefile test targets

## Definition of Done

- `make test`, `make test-slow`, and `make test-cov` append `$(PYTEST_ARGS)` to pytest.
- `make test PYTEST_ARGS="-k foo"` narrows the run.
- Default behavior unchanged when `PYTEST_ARGS` is unset.
- `doc/dev/testing.md` documents the override.
