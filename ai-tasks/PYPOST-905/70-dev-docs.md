# PYPOST-905: Dev Docs

## Overview

Documented stamp-gated `venv-test` / `venv-otel` extras installs so
repeated Make pytest targets skip redundant pip when extras are
current, while preserving the PYPOST-872 bare-venv safety net.

## Files updated

| File | Change |
| --- | --- |
| `doc/dev/testing.md` | Rewrite Install-first section for stamps; add PYPOST-905 to Makefile automation table / area checklist |
| `doc/dev/setup.md` | Note stamp files and that `install` refreshes both stamps |

## Architecture (docs)

- Thin phony aliases `venv-test` / `venv-otel` depend on version-aware
  stamp files under `.venv/`.
- Stamp recipes depend on `$(VENV_MARKER)` and `pyproject.toml`.
- `make install` installs `[dev,otel]` then touches both stamps.

## Usage

Prefer `make install` once after clone. Then `make test` (and related
targets) reuse stamps until `pyproject.toml` changes or `make clean`.

## Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| Every `make test` still runs pip | Stamp missing/stale or `pyproject.toml` newer | Check `.venv/.venv-test-*` / `.venv-otel-*`; run `make install` |
| Extras missing after clean | `make clean` removes `.venv` including stamps | Re-run `make install` or let pytest targets auto-install |

## Validation

- Docs match Option B Makefile behavior from Step 4.
- `make verify-ai-tasks` expects this file once Steps 1–7 are marked
  complete on the roadmap.
