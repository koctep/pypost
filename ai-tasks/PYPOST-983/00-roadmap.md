# Roadmap: PYPOST-983

## Task Metadata

- **Implementation language**: Python 3.10+

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *N/A — no behavioral change; timeout ownership is centralized without changing the 0.05-second value, waits, diagnostics, or assertions.*
- [x] **STEP 4: Development**
  - [x] Added the shared `FORCED_SETTLE_TIMEOUT_S = 0.05` helper and updated the golden, dialog, and mapping timeout companions to import it without changing wait behavior.
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Technical Debt Analysis**
- [x] **STEP 8: Dev Docs**
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-983/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-983/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-983/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-983/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-983/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- Final validation completed and the commit gate passed. Branch name and commit hash are
  reported in chat only, never written to this file.

#### Final Validation

- `make lint` — passed
- `make typecheck` — passed
- `make verify-ai-tasks` — passed
- `make check WORKERS=4` — completed: 332 passed, 6 skipped, and 3 known pre-existing
  failures in `tests/test_function_expression_resolver.py`,
  `tests/test_solid_audit_baseline.py`, and `tests/test_template_service.py`
