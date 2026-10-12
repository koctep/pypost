# Roadmap: PYPOST-1359

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Artifact: `ai-tasks/PYPOST-1359/10-requirements.md`.
  - Documented business goals, DoD, and scope for resolving dev dependency lock check drift.
- [x] **STEP 2: High-Level Architecture Design**
  - Artifact: `ai-tasks/PYPOST-1359/20-architecture.md`.
  - Defined architecture, compiler mechanics, uv fallback strategy, and Step 3 red repro plan.
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_lockfile_verification.py` — automated red repro of check-lock-dev drift under pinned uv toolchain
- [x] **STEP 4: Development**
  - [x] Makefile: Support $(BIN)/uv automatically when uv is not present on system PATH via `UV ?= $(shell command -v uv 2>/dev/null || ( [ -x $(BIN)/uv ] && echo $(BIN)/uv ) || echo uv)`.
  - [x] Lockfile: Re-generate `requirements-dev.txt` using the pinned uv (`0.11.31`) via `make lock-dev`.
  - [x] Repro & Gate Validation: Verified `make check-lock-dev` passes cleanly (exit code 0), `tests/test_lockfile_verification.py` passes (green), and `make lint` / `make typecheck` / `make verify-ai-tasks` pass.
- [x] **STEP 5: Code Cleanup**
  - Artifact: `ai-tasks/PYPOST-1359/40-code-cleanup.md`.
  - Static analysis, formatting, and line lengths verified cleanly.
- [x] **STEP 6: Observability**
  - Artifact: `ai-tasks/PYPOST-1359/50-observability.md`.
  - Documented retry backoff logs, drift diagnostics on stderr, and CI job summaries.
- [x] **STEP 7: Technical Debt Analysis**
  - Artifact: `ai-tasks/PYPOST-1359/60-tech-debt.md`.
  - Analyzed shortcuts, test bounds, and documented pre-existing test failures and lockfile consolidation debt.
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/setup.md` with Makefile UV automatic fallback, local check-lock-dev usage, and CI toolchain alignment.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1359/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1359/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1359/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1359/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1359/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
