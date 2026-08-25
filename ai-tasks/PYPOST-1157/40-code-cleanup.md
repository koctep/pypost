# PYPOST-1157: Code Cleanup Report

## Linter Fixes

No in-scope linter errors or warnings. `make lint` passed (flake8 on `pypost/` plus
documentation checks). `make analyze` is not a Makefile target.

## Code Formatting

Applied formatting changes:

- [x] Automatic code formatting — no project auto-format Make target; PEP 8 import
  grouping applied by hand in `tabs_presenter.py` and the PYPOST-1157 test modules
- [x] Indentation and alignment fixes — none required beyond the import regroup
- [x] Line length correction — all in-scope lines are at most 100 characters

## Code Cleanup

Cleanup actions performed:

- Removed unused imports: 1 (`inspect` from `tests/test_tabs_presenter.py`)
- Removed unused variables: 0
- Removed commented-out code: none
- Removed debug prints: none

Dead Step 3 scaffolding removed now that the production API exists:

- `inspect.signature` / `protocol_picker` constructor fallback in
  `TestHandleNewTabProtocolPicker._make_presenter`
- `_tab_protocol()` `ImportError` / `SimpleNamespace` fallback
- `getattr(protocol, "value", protocol)` in `TabsPresenter.open_blank_tab` (now
  `protocol.value`)

Hoisted `TabProtocol` / `NewTabProtocolPicker` / `WebSocketTab` imports to module
scope in `tests/test_tabs_presenter.py` and `tests/test_agent_golden_e2e.py`.

`ai-tasks/PYPOST-376/baseline-metrics.md` was regenerated so measured LOC matches
the post-cleanup tree (`tabs_presenter.py` 740 / cap 785;
`metrics_tracking.py` 138 / cap 145). That snapshot is listed out of scope except
when a PYPOST-1157 in-scope change causes the drift; Step 4 and this cleanup did.

No unused imports, unused variables, commented-out code, or debug prints remain
in the other in-scope production files.

## Validation Results

Validation results:

- [x] All tests passed (`make test`: 272 passed, 0 failed, 1 skipped)
- [x] All tests have explicit timeout markers
- [x] No merge conflicts
- [x] Syntax is valid
- [x] Types are correct (if applicable) — no new type issues in in-scope files;
  `make typecheck` was not required for this step

Timeout markers (module `pytestmark`):

- `tests/test_tabs_presenter.py` — `timeout(60)`
- `tests/test_new_tab_protocol_picker.py` — `timeout(60)`
- `tests/test_agent_golden_e2e.py` — `timeout(60)`
- `tests/test_metrics_manager.py` — `timeout(30)`
- `tests/test_metrics_otel.py` — `timeout(30)`

The skipped file is `tests/test_agent_dialog_settle_teardown_stress.py`
(unrelated to this ticket).

## Notes

### MCP test (documented Step 4 leftover)

`tests/test_mcp_server_manager.py::test_update_tools_restarts_when_exposed_set_changes`
did **not** fail in either full `make test` run this step. Out of scope; do not
fix in PYPOST-1157. Existing ticket: PYPOST-1178.

### First `make test` run (before snapshot regen)

Two file failures. Classified with a throwaway worktree at base commit
`1cc642b2ef7ff554228a5022cc5de866be6e72fb` (`HEAD` before this task's uncommitted
work).

#### Caused by this task (fixed)

- Node id:
  `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline`
  `::test_markdown_snapshot_matches_current_metrics`
- Excerpt: `AssertionError: ... | 741 | 785 | ... != ... | 740 | 785 | ...`
  (snapshot still had 741 after cleanup dropped `tabs_presenter.py` by one line)
- Action: regenerated `ai-tasks/PYPOST-376/baseline-metrics.md`. Second
  `make test` passed this node.

#### Flaky (not caused by this task)

- Node id:
  `tests/test_websocket_client_ui_repro.py`
  `::test_presenter_connect_and_disconnect_lifecycle`
- Excerpt:

  ```text
  assert connect_btn.text() == "Disconnect"
  AssertionError: assert 'Connect' == 'Disconnect'
  websocket_transport_socket_error category=HostNotFoundError message=Host not found
  websocket_handshake_failed session_id=... category=HostNotFoundError
  ```

- Evidence:
  - Full suite (this tree): FAIL
  - Isolated re-run (this tree): PASS
  - Base commit `1cc642b2` isolated: PASS
  - Full suite after snapshot regen: PASS
- Observed rate: 1 fail / 2 full parallel suite runs; 0 fail / 2 isolated runs
- Jira search (`text ~ "test_presenter_connect_and_disconnect_lifecycle"` and
  `text ~ "websocket_client_ui_repro"`, open issues): no match. Not skipped,
  xfailed, or deleted. Step 7 should file a Debt follow-up.
