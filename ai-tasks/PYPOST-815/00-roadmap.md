# Roadmap: PYPOST-815

**Programming language:** Python

**Suggested branch:** `chore/PYPOST-815-mypy-ui-baseline`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Add `types-PySide6` dev dependency and remove `pypost.ui.*` mypy ignore override
  - [x] Extend `[tool.mypy]` scope and baseline gate to `pypost/ui/` (~67 modules)
  - [x] Bulk `from __future__ import annotations` migration for UI modules (57 added)
  - [x] Generate `mypy-baseline.json` with 177 UI errors frozen (218 total)
  - [x] Update `scripts/check_mypy_baseline.py`, `Makefile`, and tests
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

- `ai-tasks/PYPOST-815/10-requirements.md`
- `ai-tasks/PYPOST-815/20-architecture.md`
- `ai-tasks/PYPOST-815/40-code-cleanup.md`
- `ai-tasks/PYPOST-815/50-observability.md`
- `ai-tasks/PYPOST-815/60-tech-debt.md`
- `ai-tasks/PYPOST-815/70-dev-docs.md`
- `doc/dev/static_type_checking.md`
- `mypy-baseline.json`
