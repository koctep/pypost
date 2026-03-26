# Roadmap: PYPOST-88

> **Summary**: [PYPOST-52] No pytest cov-fail-under threshold
> **Type**: Debt | **Priority**: Medium
> **Source**: ai-tasks/PYPOST-52/60-review.md

## Step Execution Status

- [x] **STEP 1: Requirements** — gather and document coverage threshold requirements
- [x] **STEP 2: Architecture** — design `--cov-fail-under` configuration approach
- [x] **STEP 3: Development** — implement coverage threshold in CI and/or pytest config
- [x] **STEP 4: Code Cleanup** — review and clean up modified files
- [x] **STEP 5: Observability** — confirm threshold enforcement is visible in CI output
- [x] **STEP 6: Review** — tech debt analysis post-implementation
- [x] **STEP 7: Dev Docs** — document coverage threshold policy
- [x] **STEP 8: Commit** — final commit and Jira closure

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-88/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-88/20-architecture.md`

### STEP 3: Development

- `pytest.ini` / `pyproject.toml` / `.github/workflows/test.yml` (TBD by architecture)

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-88/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-88/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-88/60-review.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-88/70-dev-docs.md`

---

## Project Manager Update

**Date**: 2026-03-25 (finalization sync)

### Completed Milestones

- **STEP 1** (2026-03-25): Requirements complete — `ai-tasks/PYPOST-88/10-requirements.md`
  produced. Threshold agreed at 70% (subject to baseline audit per §5). Preferred enforcement
  via `pytest.ini` `addopts` as single source of truth. Impacted files: `pytest.ini`,
  `Makefile`, `.github/workflows/test.yml`. Acceptance criteria AC-1…AC-5 defined.
  All dependencies satisfied (PYPOST-89 merged at `9f0a52d`).
- **STEP 2** (2026-03-25): Architecture complete — `ai-tasks/PYPOST-88/20-architecture.md`
  produced. Baseline audit result: **54%**. Chosen threshold: **50%**
  (`floor(54/5)*5 = 50`). Single-file change: append `--cov-fail-under=50` to `addopts` in
  `pytest.ini`. No changes to `Makefile` or `.github/workflows/test.yml` (both inherit
  `addopts` automatically). Follow-up ticket required to raise threshold to 70% once
  coverage improves.
- **STEP 3** (2026-03-25): Development complete — `pytest.ini` updated with
  `--cov-fail-under=50` and rationale comment. `make test-cov` exits 0 at 53.62% ≥ 50%.
  AC-1, AC-2, AC-5 verified by junior_engineer.
- **STEP 4** (2026-03-25): Code cleanup complete — `ai-tasks/PYPOST-88/40-code-cleanup.md`
  produced. No dead code or formatting issues. Single file changed (`pytest.ini`), all
  added lines within 100-char limit, no trailing whitespace, single final newline.
- **STEP 5** (2026-03-25): Observability complete — `ai-tasks/PYPOST-88/50-observability.md`
  produced. All AC-1…AC-5 verified. Coverage summary block added to GitHub Actions step
  summary (`test.yml`), surfacing line coverage %, threshold, and PASS/FAIL status without
  extra log expansion. AC-4 corrected: failure simulation confirmed via
  `--cov-fail-under=99` (exits 2, 53% < 99%). No application-code changes required.
- **STEP 6** (2026-03-25): Tech debt review complete — `ai-tasks/PYPOST-88/60-review.md`
  produced. All AC-1…AC-5 PASS. Three residual debt items identified: TD-1 (HIGH) threshold
  gap 50%→70%; TD-2 (LOW) hardcoded threshold in `test.yml` summary; TD-3 (LOW) no branch
  coverage. No blockers; follow-up ticket for TD-1/TD-2 required.
- **STEP 7** (2026-03-25): Developer documentation complete —
  `ai-tasks/PYPOST-88/70-dev-docs.md` produced. Documents threshold mechanics, CI visibility,
  how to raise the threshold, selection rationale, and related tickets.
- **STEP 8** (2026-03-25): Final commit complete — `df542ac`
  `feature(config): PYPOST-88 enforce pytest cov-fail-under threshold at 50%`. All
  deliverables merged. Jira closure in progress.

### Active Risks / Blockers

- **No blockers.** All deliverables are complete and committed.
- **Follow-up required (TD-1/F-1)**: Create a new Jira ticket to raise `--cov-fail-under`
  from 50% to 70% once overall test coverage reaches ≥ 70%.
- **Follow-up required (TD-2/F-2)**: When raising threshold, update `THRESHOLD=50` in
  `.github/workflows/test.yml` summary script to match.

### Next Action

**DONE** — PYPOST-88 is fully complete. Jira issue moved to Done.
Follow-up: create new ticket for raising `--cov-fail-under` to 70% (TD-1).
