# PYPOST-808: Version unification architecture

## Overview

Replace duplicated static version strings with setuptools dynamic metadata that reads
`pypost.version.__version__` at build/install time. Runtime code and UI keep importing the
module constant directly.

## Before / After

| Location | Before | After |
| --- | --- | --- |
| `pypost/version.py` | `__version__ = "0.1.0"` | Unchanged — canonical source |
| `pyproject.toml` `[project]` | `version = "0.1.0"` | `dynamic = ["version"]` |
| `pyproject.toml` setuptools | — | `version = { attr = "pypost.version.__version__" }` |
| About dialog | imports `__version__` | unchanged |
| `tests/test_pyproject.py` | asserts literal equality | asserts dynamic attr wiring |

## Version flow

```
pypost/version.py (__version__)
    ├── runtime: About dialog, diagnostics, tests
    └── packaging: setuptools dynamic attr → wheel/sdist metadata
```

## Files touched

| File | Change |
| --- | --- |
| `pyproject.toml` | Remove static `version`; add `dynamic` + `[tool.setuptools.dynamic]` |
| `pypost/version.py` | Docstring clarifies packaging role |
| `tests/test_pyproject.py` | Validate dynamic metadata config |
| `doc/dev/setup.md` | Document single version source |

## Out of Scope

- Reading version from `importlib.metadata` at runtime (adds install-time dependency for imports).
- CI release tagging or version bump automation.
