# Roadmap: PYPOST-734

**Programming language:** Python

**Suggested branch:** `chore/PYPOST-734-static-type-checking`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Add mypy + types-PyYAML to dev lock
  - [x] Configure `[tool.mypy]` scoped to `pypost/core/` and `pypost/models/`
  - [x] Add `scripts/check_mypy_baseline.py` and `mypy-baseline.json`
  - [x] Wire `make typecheck` (optional; not in `make check`)
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

- `ai-tasks/PYPOST-734/10-requirements.md`
- `ai-tasks/PYPOST-734/20-architecture.md`
- `ai-tasks/PYPOST-734/40-code-cleanup.md`
- `ai-tasks/PYPOST-734/50-observability.md`
- `ai-tasks/PYPOST-734/60-tech-debt.md`
- `ai-tasks/PYPOST-734/70-dev-docs.md`
- `doc/dev/static_type_checking.md`
- `mypy-baseline.json`
- `scripts/check_mypy_baseline.py`
