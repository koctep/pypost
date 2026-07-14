# PYPOST-807: Pytest config migration architecture

## Overview

Move pytest configuration from INI to TOML under the standard `[tool.pytest.ini_options]` table.
No runtime or Makefile behavior changes — pytest discovers config from `pyproject.toml` when
`pytest.ini` is absent.

## Before / After

| Setting | `pytest.ini` (removed) | `pyproject.toml` |
| --- | --- | --- |
| `pythonpath` | `.` | `pythonpath = "."` |
| `addopts` | single line | TOML array (same flags) |
| `markers` | multiline INI | TOML string array |
| `log_cli*` | INI booleans/strings | TOML equivalents |

## Config flow (unchanged behavior)

```
make test / CI pytest
    └── reads [tool.pytest.ini_options] from pyproject.toml
            ├── addopts: -v --tb=short --cov-fail-under=70 -m "not slow"
            ├── markers: timeout, slow
            ├── log_cli: true (local); CI overrides with -o log_cli=false
            └── pythonpath: . (PYPOST-434 fallback)
```

## Files touched

| File | Change |
| --- | --- |
| `pyproject.toml` | Add `[tool.pytest.ini_options]` block |
| `pytest.ini` | Delete |
| `doc/dev/setup.md` | pythonpath reference |
| `doc/dev/testing.md` | threshold, markers, log_cli, empty_tests_policy |
| `doc/dev/observability_audit.md` | local config column |
| `doc/dev/test_audit.md` | coverage gate source |
| `doc/dev/tech-debt/PYPOST-434.md` | historical note |

## Out of Scope

- Syncing `test.yml` THRESHOLD via parsing `pyproject.toml` (manual mirror retained).
- Removing `pythonpath` now that editable install is default (still useful without install).
