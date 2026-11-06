# Roadmap: PYPOST-1347

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Requirements documented in `10-requirements.md`.
- [x] **STEP 2: High-Level Architecture Design**
  - Architecture documented in `20-architecture.md`.
  - Prefer widening PYPOST-1352 library-sourced branches for reconcile / reconfigure /
    refresh_environment; ordinary `refresh_environment` still raw-env (primary residual defect).
  - Failing-repro plan: `tests/test_mcp_library_lifecycle.py` (three defects + workspace guard).
- [x] **STEP 3: Failing Repro Test**
  - Red suite: `tests/test_mcp_library_lifecycle.py`
  - RED (intended): `test_ordinary_library_server_stops_when_library_collection_missing`
    (connection-thin reconcile leaves zombie after collection file removal)
  - RED (intended): `test_ordinary_library_server_refresh_environment_preserves_library_layers`
    (raw `environment.variables` drops manifest `base_url` default)
  - GREEN (contract lock / regression): survive reconcile, reconfigure running row,
    workspace reconcile+refresh unchanged
  - `make test PYTEST_ARGS='tests/test_mcp_library_lifecycle.py -v'` → 2 failed, 3 passed;
    no production code changed
- [x] **STEP 4: Development**
  - [x] Widened ordinary library reconcile to require collection resolve; stop diagnostic
    `"missing library collection"` when the selected collection file/manifest path is gone
  - [x] Widened `refresh_environment` Built-in branch to all `library_id` rows; ordinary
    rows re-enter `LibraryRuntimeResolver` (service + `candidate_overlay=None`)
  - [x] Widened `_validate_replacement_references` ordinary path to reject unresolved
    library collections
  - [x] Added `_ordinary_library_collection_resolves` helper (resolver-aligned readability
    checks without variable-layer merge)
  - [x] Step 3 suite green: `make test PYTEST_ARGS='tests/test_mcp_library_lifecycle.py
    tests/test_mcp_builtin_lifecycle.py -v'` — all passed; workspace path unchanged
  - [x] `make lint` / `make typecheck` OK; `make check` → 438 passed, 5 failed —
    all five NON-BLOCKER pre-existing (PYPOST-1474, PYPOST-1475, PYPOST-1397);
    see `60-tech-debt.md` Follow-up Tasks
- [x] **STEP 5: Code Cleanup**
  - Artifact: `ai-tasks/PYPOST-1347/40-code-cleanup.md`
  - `make lint` / `make typecheck` OK; lifecycle suites green
  - Minor readability cleanup in `_ordinary_library_collection_resolves` root-path branch
- [x] **STEP 6: Observability**
  - Artifact: `ai-tasks/PYPOST-1347/50-observability.md`
  - Added DEBUG/WARNING library refresh + unresolved-collection events in
    `mcp_server_registry.py`; coverage in
    `test_ordinary_library_lifecycle_observability_and_logging`
- [x] **STEP 7: Technical Debt Analysis**
  - Artifact: `ai-tasks/PYPOST-1347/60-tech-debt.md` (full template; no new Jira)
  - Pre-existing NON-BLOCKER failures remain PYPOST-1474 / 1475 / 1397
  - User docs (`doc/user`): N/A — no end-user workflow or UI change
- [x] **STEP 8: Dev Docs**
  - Updated `doc/dev/mcp_server_registry.md` (ordinary library lifecycle section,
    refresh/reconcile semantics, observability, troubleshooting, focused tests)
  - Updated `doc/dev/logging.md`, `doc/dev/collection_scoped_variables.md`,
    `doc/dev/predefined_collection_library.md`, `doc/dev/README.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1347/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1347/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_mcp_library_lifecycle.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1347/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1347/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1347/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
