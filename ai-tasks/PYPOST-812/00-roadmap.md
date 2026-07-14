# Roadmap: PYPOST-812

**Branch (reference):** verification close-out (no code changes required)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Verified `make venv-otel` → `pip install -e ".[otel]"`
  - [x] Verified `make install` → `pip install -e ".[dev,otel]"`
  - [x] Verified CI `test` job → `pip install -e ".[dev,otel]"`
  - [x] Updated stale `doc/dev/setup.md` OTel install guidance
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-812/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-812/20-architecture.md`

### STEP 3: Development

- Verification only (implementation landed in PYPOST-806)
- `doc/dev/setup.md` — remove `requirements-otel.txt` as primary install path

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-812/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-812/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-812/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/setup.md`
- `ai-tasks/PYPOST-812/70-dev-docs.md`
