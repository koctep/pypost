# PYPOST-812: Editable OTel extra architecture

## Overview

Confirm that OpenTelemetry packages install via the PEP 621 `[otel]` optional extra everywhere
Makefile and CI provision OTel dependencies. Lock files remain for compile and cache workflows.

## Verification matrix

| Surface | Expected command | Status |
| --- | --- | --- |
| `make venv-otel` | `pip install -e ".[otel]"` | Verified |
| `make install` | `pip install -e ".[dev,otel]"` | Verified |
| CI `test` job | `pip install -e ".[dev,otel]"` | Verified |
| `make test` / `test-slow` / `test-cov` | prerequisite `venv-otel` | Verified |

## Install flow

```
pyproject.toml [optional-dependencies.otel]
        │
        ├── make venv-otel ──► pip install -e ".[otel]"
        │
        └── make install ──► pip install -e ".[dev,otel]"
                                    │
                                    └── CI test job (same command)

requirements-otel.in ──► requirements-otel.txt ──► make lock-otel / check-lock-otel
        ▲                                              (lock only — not install path)
        └── mirrored in pyproject.toml [otel]
```

## Relationship to PYPOST-806

PYPOST-806 migrated all Makefile install targets from requirements-file installs to editable
extras. PYPOST-812 closes the PYPOST-787 follow-up specifically for the OTel extra path and
updates documentation that still referenced `requirements-otel.txt` as an install alternative.

## Out of scope

- CI job dedicated to `pip install -e ".[otel]"` without dev extra (not required; main job
  covers OTel test imports).
- Removing dual lock/pyproject pin maintenance (guarded by `tests/test_pyproject.py`).
