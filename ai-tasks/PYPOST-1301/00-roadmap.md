# Roadmap: PYPOST-1301

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1301/10-requirements.md`
  - Business goal: tab removal and app exit must run WebSocket stream export
    teardown so a busy export cannot crash shutdown or leave the page leaked
  - Language: Python
  - Source: PYPOST-1286 TD-1 follow-up
  - Fix (review FAIL): resolved exit-after-budget vs deferral contradiction —
    tab close defers disposal; exit releases ownership (abandon/orphan) after
    bounded wait; DoD / stories / NFR / out-of-scope / Q&A aligned
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1301/20-architecture.md`
  - Wire export-safe disposal into `tabs_presenter_close` +
    `tabs_presenter_ws_close` via shared helper; extend
    `tabs_presenter_lifecycle.teardown` for exit; add stream-view abandon
    (orphan worker) after exit budget; tab close defers `deleteLater`
  - Failing repro design: `tests/test_pypost_1301_failing_repro.py`
    (production close_tab + tabs teardown paths, busy/idle)
  - Fix (review FAIL): session teardown owned by close modules / lifecycle
    (not export helper); exit snapshots WS pages then disposes under
    remaining monotonic budget after request/MCP fencing
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_pypost_1301_failing_repro.py`
  - Confirmed red via `make test PYTEST_ARGS="tests/test_pypost_1301_failing_repro.py -vv"`:
    busy close (cleanup never called), idle close (page leaked), busy
    teardown (export ownership not abandoned); idle teardown passes
- [x] **STEP 4: Development**
  - [x] Implemented `WebSocketStreamView.abandon_export_for_shutdown()` with
    module-level orphan worker holder + finished → deleteLater
  - [x] Added `tabs_presenter_ws_export_teardown` helper
    (`dispose_websocket_tab_page`, deferred set, exit snapshot)
  - [x] Wired `close_workspace_tab` + `close_tabs_for_websocket_ids`
    (session teardown → export helper; idle dispose / busy defer)
  - [x] Extended `tabs_presenter_lifecycle.teardown` with snapshot-then-dispose
    WS phase under remaining monotonic budget (`mode=app_exit` / abandon)
  - [x] Step 3 repro green:
    `make test PYTEST_ARGS="tests/test_pypost_1301_failing_repro.py -vv"`
    (4 passed); related 1286 + tabs_presenter suites green; `make lint` OK
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1301/40-code-cleanup.md`
  - `make lint` OK; `make typecheck` baseline OK
  - Fixed mypy disconnect-union in `abandon_export_for_shutdown`
  - Hardened `_schedule_deferred_dispose` post-connect busy re-check
    (Step 4 review race note)
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1301/50-observability.md`
  - Defer/abandon WARNINGs + deferred-complete INFO with `action=` /
    `wait_ms=`; `tests/test_pypost_1301_observability.py`
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1301/60-tech-debt.md`
  - No BLOCKER debt; Low follow-ups TD-1 (wait_ms constant share) and
    TD-4 (ws_ids close busy-export test); PYPOST-1304 already covers helpers
- [x] **STEP 8: Dev Docs**
  - `doc/dev/websocket_message_stream.md` — tab-close / app-exit export disposal
    (helper, modes, abandon, logs, tests); removed obsolete "no production caller" gap
  - `doc/dev/websocket_draft_tab.md` — `close_tab` uses dispose helper for WS tabs
  - `doc/dev/websocket_collections_menu.md` — deleted-profile close uses dispose helper
  - `doc/dev/presenter_teardown.md` — TabsPresenter exit WS export phase
  - `doc/dev/README.md` — TOC note for PYPOST-1286 / PYPOST-1301
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1301/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1301/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1301/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1301/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1301/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are
  reported in chat only, never written to this file.
