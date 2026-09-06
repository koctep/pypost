# Roadmap: PYPOST-1278

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1278/10-requirements.md` — business requirements, scope, and
    acceptance criteria
  - Review fixes applied: source-specific deletion safety, deterministic status rules,
    business-level wording, and valid Q&A structure
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1278/20-architecture.md` — high-level module boundaries,
    normalized library state, Qt model/view design, operation flows, risks, and Step 3
    failing-repro plan
  - Research recorded for the official Qt for Python model/view and proxy-model guidance
  - Step 2 artifact review accepted the corrected architecture and research notes
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_ui_library_manager_pypost_1278_repro.py` — focused red repros for
    manageable rows, filtering/sorting/selection, stale offline status, safe operations,
    local-directory connection, source-specific lifecycle, and path actions
- [x] **STEP 4: Development**
  - [x] Added typed connection, synchronization, condition, stale-state, and operation-guard models.
  - [x] Added searchable/filterable stable-ID rows with deterministic name/status/modified sorting,
    selection guidance, badges, source-aware actions, and exact-path clipboard support.
  - [x] Added durable atomic connection storage with duplicate checks and legacy clone discovery.
  - [x] Added connection-based manager service, in-place manifest validation, safe lifecycle rules,
    and path-aware Git adapters for registered directories.
  - [x] Added presenter stale-status retention, operation admission, async worker execution, and
    dialog controls for connect, refresh, copy, disconnect, and source-aware delete.
  - [x] Focused repro, existing Library Manager regressions, and supported static analysis pass.
  - [x] Finalized projected-entry dialog wiring, async lifecycle feedback, and focused quality fixes.
  - [x] Repair review gaps: async dialog lifecycle operations, truthful stale/read-failure status,
    source-safe legacy deletion, credential-safe clone registration, and typed list architecture.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1278/40-code-cleanup.md` — cleanup findings and validation results
  - Wrapped the overlong status-position line and normalized task-scoped import formatting.
  - `make lint`, `make typecheck`, and focused `make test` passed; no `analyze` target exists.
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1278/50-observability.md` — structured operation logs and bounded
    Prometheus/OpenTelemetry Library Manager operation metrics.
  - Independent review accepted safe identifiers, complete sync/async outcomes, and
    protocol/backend parity.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1278/60-tech-debt.md` — trade-offs, optimization candidates, and
    pre-existing baseline debt mappings.
- [x] **STEP 8: Dev Docs**
  - `doc/dev/library_manager_ui.md` — connection/source safety, status semantics, model/view
    boundaries, observability, usage/configuration, troubleshooting, and baseline guidance.
  - Independent review accepted the corrected documentation and path-safety contract.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1278/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1278/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1278/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1278/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1278/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to a file.
