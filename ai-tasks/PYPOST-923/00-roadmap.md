# Roadmap: PYPOST-923

**Programming language:** Python (dependency locks, license inventory, pytest);
GitHub Actions / Makefile for CI gates

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *tests/test_ci_make_install_smoke_qt_runtime.py (+ confirm lock/inventory gates red)*
- [x] **STEP 4: Development**
  - [x] Added Qt/EGL apt step to `make-install-smoke` (full peer package-list copy); Step 3 contract test green
  - [x] Refreshed `requirements-dev.txt` (certifi, coverage, filelock, platformdirs, pip, types-pyyaml)
  - [x] Refreshed `requirements.txt` + `LICENSES/transitive.csv` (certifi, mcp, sse-starlette, uvicorn, annotated-types)
  - [x] Verified `check-lock-dev`, `check-lock`, license inventory `--check`, and contract test green
- [x] **STEP 5: Code Cleanup**
  - [x] `40-code-cleanup.md`; lint/format review of Step 3–4; `make lint` +
    `make check` green
- [x] **STEP 6: Observability**
  - [x] `50-observability.md` — runtime logging N/A (CI/locks/YAML only);
    CI gate visibility documented
- [x] **STEP 7: Review and Technical Debt**
  - [x] `60-tech-debt.md` — SAFE TO CLOSE; TD-1..5 non-blockers (no Jira yet)
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/setup.md` + `testing.md` — smoke Qt/EGL apt parity with
    `test` / `agent-e2e` (PYPOST-923)
  - [x] Artifact: `ai-tasks/PYPOST-923/70-dev-docs.md`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-923/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-923/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_ci_make_install_smoke_qt_runtime.py` — asserts
  `make-install-smoke` has full peer Qt/EGL apt set (red until Step 4)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-923/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-923/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-923/60-tech-debt.md`

### STEP 8: Dev Docs

- `ai-tasks/PYPOST-923/70-dev-docs.md` — summary of doc/dev + lock/inventory notes
- `doc/dev/setup.md` — CI Qt/EGL apt parity for smoke / test / agent-e2e
- `doc/dev/testing.md` — `make-install-smoke` package-list note + contract test
