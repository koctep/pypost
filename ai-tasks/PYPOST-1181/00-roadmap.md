# Roadmap: PYPOST-1181

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1181/10-requirements.md`
  - Language: Python
  - Source: debt follow-up from PYPOST-1157 (`60-tech-debt.md` Follow-up 1);
    hang/timeout note from PYPOST-1192 comment on this issue
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1181/20-architecture.md`
  - Pattern: test-only DI via `set_transport_factory` + silent MockTransport
  - No production session/UI changes expected; preserve Connect→Open→Idle UI contract
  - Step 3: deterministic deferred-fail harness (no live DNS), then silent mock for green
- [x] **STEP 3: Failing Repro Test**
  - Red test: `tests/test_websocket_client_ui_repro.py::test_presenter_lifecycle_open_overwritten_by_deferred_transport_failure`
  - Deterministic `DeferredFailTransport` (queued `on_failed` HostNotFoundError, no DNS)
  - Confirmed RED: after simulated Open, deferred failure leaves Connect (assert Disconnect)
- [x] **STEP 4: Development**
  - [x] Iteration 1: Added `_SilentMockTransport` + `set_transport_factory` isolation for
    `test_presenter_connect_and_disconnect_lifecycle` and converted Step 3 red harness
    `test_presenter_lifecycle_open_overwritten_by_deferred_transport_failure` from
    DeferredFailTransport to silent mock so Open/Disconnect survives bounded
    `processEvents` pumping (no live DNS / deferred HostNotFound).
  - [x] Iteration 2: Injected hermetic `_http_protocol_picker` into all TabsPresenter
    constructions in the UI repro file so `test_tabs_presenter_close_websocket_tab_calls_teardown`
    no longer hangs on modal `NewTabProtocolPicker` after closing the last tab (pre-existing
    hang at base `2f33a393`; file TIMED_OUT under worker timeout).
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1181/40-code-cleanup.md`
  - `make lint` passed; in-scope
    `tests/test_websocket_client_ui_repro.py` (19 passed, module timeout 30s)
  - Cleanup: hoisted `WebSocketSessionController` import; dropped unused `_listener` store;
    refreshed module docstring; `_http_protocol_picker` arg names
  - Note: full `make check` has 4 unrelated failing files (documented in 40-code-cleanup.md)
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1181/50-observability.md`
  - N/A for new production logging/metrics: test-only isolation
    (`_SilentMockTransport` + hermetic `_http_protocol_picker`); no `pypost/` changes
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1181/60-tech-debt.md`
  - No AC-breaking debt; leftover: rename/merge redundant silent-mock survival
    test; optional shared MockTransport helper; Step 8 hermetic-test docs
  - Pre-existing suite failures (NON-BLOCKER): PYPOST-1193, PYPOST-1194,
    PYPOST-1195 (same cluster as PYPOST-1192 triage)
  - Timeout markers: no BLOCKER (`pytestmark = timeout(30)` on scope file)
- [x] **STEP 8: Dev Docs**
  - `doc/dev/websocket_ui_client.md` — hermetic Connect/Disconnect +
    TabsPresenter `protocol_picker` isolation (PYPOST-1181)
  - `doc/dev/websocket_session_engine.md` — UI lifecycle note under §5 DI;
    troubleshooting row for Connect/Disconnect flake
  - `doc/dev/gui_testing.md` — short WebSocket UI hermetic checklist
  - `doc/dev/new_tab_protocol_picker.md` /
    `doc/dev/last_tab_protocol_picker.md` — close-last-tab hang + injection
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1181/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1181/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_websocket_client_ui_repro.py::test_presenter_lifecycle_open_overwritten_by_deferred_transport_failure`
  (DeferredFailTransport / queued HostNotFound; asserts Disconnect survives — red today)

### STEP 4: Development

- `tests/test_websocket_client_ui_repro.py` — `_SilentMockTransport`, lifecycle isolation,
  hermetic `_http_protocol_picker` for TabsPresenter tests (no production code changes)
- Iteration summaries under STEP 4 status above

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1181/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1181/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1181/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/websocket_ui_client.md` (primary: hermetic transport + picker)
- `doc/dev/websocket_session_engine.md`
- `doc/dev/gui_testing.md`
- `doc/dev/new_tab_protocol_picker.md`
- `doc/dev/last_tab_protocol_picker.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit
  hash are reported in chat only, never written to this file.
