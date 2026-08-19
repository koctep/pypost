# Roadmap: PYPOST-1057

## Task Metadata

- **Implementation language**: Python / Makefile / CSV / Requirements Lock
- **Branch name**: feature/PYPOST-1057-dependency-drift-refresh

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Gather requirements for resolving CI dependency drift across requirements.txt, requirements-dev.txt, and LICENSES/transitive.csv
  - [x] Produce requirements artifact `ai-tasks/PYPOST-1057/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Design refresh strategy using `uv pip compile --upgrade` and `scripts/generate_license_inventory.py`
  - [x] Produce architecture artifact `ai-tasks/PYPOST-1057/20-architecture.md`
- [x] **STEP 3: Failing Repro Test / Baseline**
  - [x] Confirmed `make check-lock` failed prior to lock re-generation
- [x] **STEP 4: Development**
  - [x] Recompiled `requirements.txt`, `requirements-dev.txt`, and `requirements-otel.txt` with current upstream releases
  - [x] Regenerated `LICENSES/transitive.csv`
  - [x] Verified `make check-lock`, `make check-lock-dev`, `make check-lock-otel`, and `make check-license-inventory` pass 100% GREEN
- [x] **STEP 5: Code Cleanup**
  - [x] Ran `make lint`, `make check-mcp-fixtures`, `make verify-ai-tasks`
  - [x] Produce `ai-tasks/PYPOST-1057/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Verify CI check-lock and license inventory validation logs
  - [x] Produce `ai-tasks/PYPOST-1057/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Review recurring dependency drift debt (consider scheduled refresh workflow)
  - [x] Produce `ai-tasks/PYPOST-1057/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Verified developer build and quality gates
- [ ] **COMMIT: Commit Changes**
  - Commit hash and message (Conventional Commits + JIRA ID)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

## Artifacts

### STEP 1: Requirements
- `ai-tasks/PYPOST-1057/10-requirements.md`

### STEP 2: Architecture
- `ai-tasks/PYPOST-1057/20-architecture.md`

### STEP 4: Development
- `requirements.txt`
- `requirements-dev.txt`
- `requirements-otel.txt`
- `LICENSES/transitive.csv`
- `Makefile`

### STEP 5: Code Cleanup
- `ai-tasks/PYPOST-1057/40-code-cleanup.md`

### STEP 6: Observability
- `ai-tasks/PYPOST-1057/50-observability.md`

### STEP 7: Technical Debt
- `ai-tasks/PYPOST-1057/60-tech-debt.md`

### COMMIT
- Commit hash and message (Conventional Commits + JIRA ID)
