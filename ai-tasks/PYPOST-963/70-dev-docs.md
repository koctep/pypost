# PYPOST-963: Dev Docs

## Overview

Documented slow-smoke **minimum `pypost/` tree policy**: stub package (`__init__.py` +
`version.py`), not a full repo mirror.

## Key artifacts

- `SLOW_SMOKE_MINIMUM_PYPPOST_FILES` in `tests/test_makefile.py`
- `test_slow_smoke_seed_materializes_minimum_pypost_tree` in seed contract module
- `doc/dev/testing.md` § Minimum `pypost/` tree policy

## Usage

```bash
make test PYTEST_ARGS='tests/test_makefile_install_seed_contract.py -v'
```

## When to update

Extend `SLOW_SMOKE_MINIMUM_PYPPOST_FILES` and `_seed_installable_package` when
`pyproject.toml` requires install-time modules under `pypost/` beyond the current stub.
