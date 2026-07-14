# Roadmap: PYPOST-700

**Suggested branch:** `refactor/PYPOST-700-split-template-service-helpers`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Extracted render/observability helpers to `template_service_render.py`
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

- `ai-tasks/PYPOST-700/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-700/20-architecture.md`

### STEP 3: Development

- `pypost/core/template_service_render.py` (new)
- `pypost/core/template_service.py` (slimmed orchestration)
- `tests/test_template_service.py` (helper test imports)

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-700/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-700/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-700/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/template_service.md`
- `doc/dev/architecture.md`
- `doc/dev/architecture_audit.md`
- `ai-tasks/PYPOST-700/70-dev-docs.md`
