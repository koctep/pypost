# Roadmap: PYPOST-809

**Branch (reference):** `chore/PYPOST-809-transitive-license-inventory`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `pip-licenses>=5,<6` to `requirements-dev.in` and `pyproject.toml` dev extra
  - [x] Regenerated `requirements-dev.txt` via `make lock-dev`
  - [x] Added `scripts/generate_license_inventory.py` and committed `LICENSES/transitive.csv`
  - [x] Added `generate-license-inventory` / `check-license-inventory` Makefile targets
  - [x] Added `check-license-inventory` CI job mirroring `security-audit` pattern
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

- `ai-tasks/PYPOST-809/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-809/20-architecture.md`

### STEP 3: Development

- `requirements-dev.in`, `requirements-dev.txt`, `pyproject.toml`, `Makefile`
- `scripts/generate_license_inventory.py`, `LICENSES/transitive.csv`
- `.github/workflows/test.yml`, `tests/test_makefile.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-809/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-809/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-809/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/licensing.md`, `doc/dev/dependencies_audit.md`, `doc/dev/setup.md`, `doc/dev/testing.md`
- `ai-tasks/PYPOST-809/70-dev-docs.md`
