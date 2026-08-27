# Roadmap: PYPOST-1178

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1178/10-requirements.md`
  - Language: Python
  - In-scope WIP noted (do not revert): `pypost/core/qt/mcp_server.py`,
    `tests/helpers/mcp_live_server.py`, `tests/helpers/port_allocation.py`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1178/20-architecture.md`
  - Land WIP: `_wait_until_port_bindable` after stop in `update_tools`;
    `allocate_tcp_port` + `free_port` wiring
  - Step 3 failing-repro plan: held listening socket + caplog
    `mcp_port_still_busy` and/or monkeypatch wait to no-op (test-only);
    not rare full-suite flake alone; do not strip WIP from production
  - Out of scope: PYPOST-1113 signal-order wait
- [x] **STEP 3: Failing Repro Test**
  - Red: `tests/test_mcp_server_manager.py` —
    `test_update_tools_restart_waits_until_port_bindable`
    (monkeypatch `_wait_until_port_bindable` → hold listen socket / no wait;
    assert `is_listening` + no `start_failed`; fails with EADDRINUSE /
    port-busy `start_failed`; production WIP untouched)
  - Confirmed red via
    `make test PYTEST_ARGS="tests/test_mcp_server_manager.py -k test_update_tools_restart_waits_until_port_bindable -vv"`
- [x] **STEP 4: Development**
  - [x] Landed WIP: `_wait_until_port_bindable` in `update_tools`;
    `allocate_tcp_port` + `free_port` wiring
  - [x] Removed Step 3 monkeypatch/hold harness; permanent green
    `test_update_tools_restart_waits_until_port_bindable` asserts
    listening / no `start_failed` via real wait
  - [x] Targeted `make test` restart/port_bindable suite passed
- [x] **STEP 5: Code Cleanup**
  - Scoped: `pypost/core/qt/mcp_server.py`,
    `tests/helpers/port_allocation.py`,
    `tests/helpers/mcp_live_server.py`,
    `tests/test_mcp_server_manager.py`
  - `ai-tasks/PYPOST-1178/40-code-cleanup.md`
  - Lint clean; typing/`typing` import cleanup; import spacing;
    targeted `make test` passed
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1178/50-observability.md`
  - Existing WARNING `mcp_port_still_busy` on `_wait_until_port_bindable` deadline documented; no new production logs/metrics required
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1178/60-tech-debt.md`
  - Main follow-up: SO_REUSEADDR probe false-positive (deferred by architecture)
  - No BLOCKER; pytest timeouts present; PYPOST-1113 left Done (different flake)
- [x] **STEP 8: Dev Docs**
  - Updated existing MCP/testing/logging docs for `_wait_until_port_bindable`
    (stop→wait→start in `update_tools`), `mcp_port_still_busy`, and
    `allocate_tcp_port` / `free_port` (no new `doc/dev/` file)
  - `doc/dev/mcp_integration.md`, `doc/dev/logging.md`,
    `doc/dev/testing.md`, `doc/dev/mcp_server_registry.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1178/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1178/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1178/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1178/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1178/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
