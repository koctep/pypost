# PYPOST-785: pyproject.toml architecture

## Research

- **PEP 621** defines `[project]` metadata and `[project.optional-dependencies]` extras.
- **PYPOST-779/780** established `requirements.in` and `requirements-dev.in` as editable
  sources with uv-compiled locks as install artifacts.
- **PYPOST-434** history: tests use `pytest.ini` `pythonpath = .`; editable install is not
  required for this ticket.

## Implementation Plan

1. Add root `pyproject.toml` with `[build-system]` (setuptools) for future editable installs.
2. Copy 15 direct production constraints from `requirements.in` into `[project].dependencies`.
3. Copy dev direct pins from `requirements-dev.in` into `[project.optional-dependencies].dev`.
4. Add `[project.optional-dependencies].otel` with pinned OpenTelemetry API/SDK (same versions
   as production lock).
5. Add `tests/test_pyproject.py` to fail CI when `pyproject.toml` drifts from `.in` sources.
6. Document the file in `doc/dev/setup.md` without changing `make install` behavior.

## Architecture

```
requirements.in ──────────────► [project].dependencies (pyproject.toml)
requirements-dev.in ────────► [project.optional-dependencies].dev
(opentelemetry pins) ─────────► [project.optional-dependencies].otel

requirements.txt ─────────────► make install / CI (unchanged)
requirements-dev.txt ─────────► make venv-test / CI (unchanged)
```

| File | Role after PYPOST-785 |
| --- | --- |
| `pyproject.toml` | PEP 621 metadata + optional extras (declarative policy) |
| `requirements.in` | Production direct deps (still edited by maintainers) |
| `requirements.txt` | Compiled lock (still consumed by install) |
| `requirements-dev.in` | Dev direct deps |
| `requirements-dev.txt` | Dev compiled lock |

**Version source:** `pyproject.toml` `version` matches `pypost/version.py` (`0.1.0`) for now;
runtime About dialog continues reading `pypost.version.__version__`.

## Q&A

- **Why setuptools build backend?** Minimal, widely supported, and sufficient for a flat
  `pypost/` package layout when editable install is wired later.
- **Why not migrate pytest config into `[tool.pytest.ini_options]`?** Out of scope; `pytest.ini`
  remains authoritative until a dedicated config consolidation ticket.
