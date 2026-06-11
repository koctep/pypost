# Roadmap: PYPOST-432

> **Summary**: [Sprint 134 / PYPOST-88] Raise pytest cov-fail-under toward 70% project target

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - Raised `--cov-fail-under` from 50% to 60%; synced `test.yml` summary threshold
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Artifacts

- `ai-tasks/PYPOST-432/10-requirements.md`
- `ai-tasks/PYPOST-432/20-architecture.md`
- `ai-tasks/PYPOST-432/40-code-cleanup.md`
- `ai-tasks/PYPOST-432/50-observability.md`
- `ai-tasks/PYPOST-432/60-tech-debt.md`
- `ai-tasks/PYPOST-432/70-dev-docs.md`

## Changelog

- **STEP 1** (2026-06-11): Requirements — baseline audit 86.24%; incremental raise to 60%
- **STEP 2** (2026-06-11): Architecture — update `pytest.ini` + `test.yml` THRESHOLD in sync
- **STEP 3** (2026-06-11): Development — threshold 50 → 60; `make test-cov` passes
- **STEP 4** (2026-06-11): Code cleanup — no application code changes
- **STEP 5** (2026-06-11): Observability — CI summary THRESHOLD synced to 60
- **STEP 6** (2026-06-11): Tech debt review — SAFE TO CLOSE; follow-up for 70% threshold
- **STEP 7** (2026-06-11): Dev docs — coverage threshold section added to `doc/dev/testing.md`

**Branch name (reference)**: `chore/PYPOST-432-raise-cov-fail-under-60`

**DONE** — PYPOST-432 complete.
