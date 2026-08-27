# Roadmap: PYPOST-1113

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1113/10-requirements.md`
  - Language: Python (test-suite reliability; no new runtime language)
  - In-scope WIP noted: uncommitted wait hardening in
    `tests/test_mcp_server_manager.py` (do not revert; land with this task)
  - Out-of-scope WIP noted: sibling PYPOST-1178 edits (do not touch)
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1113/20-architecture.md`
  - Approach: land existing compound `wait_until` WIP in
    `test_port_busy_emits_start_failed` (failures + statuses + last False);
    no production / PYPOST-1178 changes
  - Step 3 plan: deterministic red via deferred `status_changed` + incomplete
    wait predicate, then restore compound wait to green
- [x] **STEP 3: Failing Repro Test**
  - Deterministic red:
    `tests/test_mcp_server_manager.py::test_port_busy_emits_start_failed`
  - Harness: incomplete `wait_until(bool(failures))` + deferred
    `status_changed` via `QTimer.singleShot(0, ...)`
  - Confirmed failure: `assert statuses` → `E assert []` (signal-ordering;
    not fixture/import)
  - Command:
    `make test PYTEST_ARGS="tests/test_mcp_server_manager.py -k test_port_busy_emits_start_failed -vv"`
- [x] **STEP 4: Development**
  - [x] Landed compound `wait_until` in
    `test_port_busy_emits_start_failed`; removed Step 3
    `QTimer.singleShot` deferred-status harness; real signal slots restored

- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1113/40-code-cleanup.md`
  - Little cleanup needed: compound `wait_until` already review-ready
  - Validated: `make lint`; `make test` on `tests/test_mcp_server_manager.py`
  - Left untouched: PYPOST-1178 WIP (`mcp_server.py`, `mcp_live_server.py`,
    `port_allocation.py`)
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1113/50-observability.md`
  - N/A for production logging/metrics: test-harness flake fix only
    (`tests/test_mcp_server_manager.py`); no production telemetry change
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1113/60-tech-debt.md`
  - Verdict: no BLOCKER; minimal test-only debt; PYPOST-1178 not claimed
  - No new follow-up Jira issues required
- [x] **STEP 8: Dev Docs**
  - N/A — test-only flake fix (compound `wait_until` in
    `tests/test_mcp_server_manager.py::test_port_busy_emits_start_failed`);
    no new feature, API, or production behavior
  - Existing guidance already covers bounded Qt signal waits:
    `doc/dev/testing.md`, `doc/dev/ui_wait.md` — no `doc/dev/` update required
- [ ] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1113/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1113/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_mcp_server_manager.py::test_port_busy_emits_start_failed`
  (Step 3 red harness removed in Step 4; compound wait landed)

### STEP 4: Development

- `tests/test_mcp_server_manager.py::test_port_busy_emits_start_failed`
  — compound `wait_until(failures AND statuses AND last is False)`

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1113/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1113/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1113/60-tech-debt.md`

### STEP 8: Dev Docs

- N/A — no `doc/dev/` changes; wait guidance already in
  `doc/dev/testing.md` / `doc/dev/ui_wait.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash
  are reported in chat only, never written to this file.
