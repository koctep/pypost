# PYPOST-806: Editable install architecture

## Overview

Replace requirements-file install chains with PEP 621 editable installs while preserving compiled
lock files for supply-chain tooling.

## Components

### 1. Makefile install targets

| Target | Before | After |
| --- | --- | --- |
| `venv-test` | `pip install -r requirements-dev.txt` | `pip install -e ".[dev]"` |
| `venv-otel` | `pip install -r requirements-otel.txt` | `pip install -e ".[otel]"` |
| `install` | `venv-test` → `venv-otel` → `pip install -r requirements.txt` | `pip install -e ".[dev,otel]"` |

`test`, `test-cov`, and `security-audit` prerequisite chains unchanged except `install` no longer
depends on `venv-test`/`venv-otel` (single editable step covers all extras).

### 2. CI `.github/workflows/test.yml`

| Job | Before | After |
| --- | --- | --- |
| `test` | Three pip steps (dev, app, otel) | `pip install -e ".[dev,otel]"` |
| `make-install-smoke` | dev + otel lock installs | `pip install -e ".[dev]"` (smoke runs `make install`) |
| `security-audit` | `requirements.txt` + `requirements-dev.txt` | `pip install -e ".[dev]"` + `pip-audit -r requirements.txt` |

Pip cache `cache-dependency-path` gains `pyproject.toml` alongside existing lock files.

### 3. `tests/test_makefile.py` fixtures

| Fixture | Before | After |
| --- | --- | --- |
| `make_workspace` | Empty `requirements.txt` + lock copies | Minimal `pyproject.toml` (no runtime deps) |
| `make_workspace_full_deps` | Real `requirements.txt` | Real `pyproject.toml` |

Dependency-chain test: `install` depends on marker only (not `venv-test`/`venv-otel`).

### 4. Lock files (unchanged role)

```
requirements.in ──► requirements.txt ──► pip-audit scan / Dependabot / make lock
requirements-dev.in ──► requirements-dev.txt ──► make lock-dev / check-lock-dev CI
requirements-otel.in ──► requirements-otel.txt ──► make lock-otel
         ▲
         └── mirrored in pyproject.toml [project] / [optional-dependencies]
```

## Out of Scope

- Removing dual install paths entirely (lock files remain for audit and compile workflows).
- Validating setuptools package discovery in a dedicated slow test (deferred).
