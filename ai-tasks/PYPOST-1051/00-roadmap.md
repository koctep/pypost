# Roadmap: PYPOST-1051

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *Verification via `make check-lock` (fails with exit code 2: `requirements.txt` is stale relative to `requirements.in`)*
- [x] **STEP 4: Development**
  - [x] Regenerated dependency lock `requirements.txt` via `rm -f requirements.txt && make lock`
  - [x] Regenerated license inventory `LICENSES/transitive.csv` via `make generate-license-inventory`
  - [x] Verified `make check-lock` and `make check-license-inventory` succeed cleanly
- [x] **STEP 5: Code Cleanup**
  - [x] Ran `make lint` (passed cleanly)
  - [x] Artifact: `ai-tasks/PYPOST-1051/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Artifact: `ai-tasks/PYPOST-1051/50-observability.md` (N/A — tooling build scripts rely on standard script logging)
- [x] **STEP 7: Review and Technical Debt**
  - [x] Artifact: `ai-tasks/PYPOST-1051/60-tech-debt.md` (SAFE TO CLOSE; no blockers or shortcuts)
- [x] **STEP 8: Dev Docs**
  - [x] Artifact: `ai-tasks/PYPOST-1051/70-dev-docs.md`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming Language

- **Primary**: Makefile / Shell / Python (`.cursor/lsr/do-python.md`)
- **Config / Lock files**: Requirements lock files (`requirements.txt`), License inventory (`LICENSES/transitive.csv`)

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1051/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1051/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test / CI check verification script (`make check-lock` & `make check-license-inventory`)

### STEP 4: Development

- `requirements.txt`
- `LICENSES/transitive.csv`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1051/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1051/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1051/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/` (updates if needed)
- `ai-tasks/PYPOST-1051/70-dev-docs.md`

## Recommended branch name

`fix/PYPOST-1051-ci-check-lock-license-inventory`
