# Roadmap: PYPOST-1169

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1169/00-roadmap.md`
  - `ai-tasks/PYPOST-1169/10-requirements.md`
  - Implementation language recorded: Python
  - Business-only summary:
    - Scope: live Connect on the MCP Client tab discovers remote tools
      (`list_tools`) and fills the tool browser with name and description
    - Connect failures are shown to the user; success is the only path
      that marks the session connected and populates tools
    - Refresh re-lists tools on an already connected session
    - Depends on shipped
      [PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166) draft
      shell and
      [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167)
      headers / environment templating
    - Invoke, schema forms, and result pane remain MCP-TM-4
    - Architecture pointer for Step 2 (later-step input only):
      `ai-tasks/PYPOST-1164/20-architecture.md`
  - Review FAIL fix (refresh-failure outcome): a failed refresh stays
    connected, keeps last-known tools as stale (not cleared), and shows
    connected-with-error chrome — unlike failed Connect (not connected)
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1169/20-architecture.md`
  - Connect → `execute_outbound("list_tools")` on presenter-owned QThread;
    fill existing `McpClientToolBrowser` with name/description
  - Failed Connect: FAILED + empty tools; failed Refresh: stay CONNECTED
    + stale list + in-tab error
  - `tabs_presenter.py` untouched (779/785); PYPOST-1184 only if factory
    lines are ever required
  - Step 3 red GUI tests planned: Connect fills browser; Connect error;
    Refresh failure keeps connected + stale list
  - Review FAIL fix: GUI-thread `resolve_outbound_fields`; worker calls
    `MCPClientService.run` with already-resolved url/headers (not the
    current `execute_outbound` body). Refresh stays `CONNECTED` via a
    separate in-flight/generation flag; disable Refresh while a list
    runs; late results keep Connect vs Refresh error policies; Refresh
    progress is an in-tab cue, not Failed-Connect chrome. `tabs_presenter.py`
    remains at the 785 cap with no growth.
- [x] **STEP 3: Failing Repro Test**
  - Red GUI tests in `tests/test_mcp_client_tab.py` (mock `MCPClientService.run`,
    no network; `pytestmark = pytest.mark.timeout(30)`)
  - `test_connect_lists_tools_in_browser` — Connect calls `run` with
    `list_tools` + `headers=` and fills the browser with name+description
  - `test_connect_empty_url_does_not_call_run_or_connect` and
    `test_connect_error_leaves_disconnected_and_empty_tools` — Connect error
    leaves not-connected chrome and empty tools
  - `test_refresh_failure_keeps_connected_and_stale_tools` — Refresh failure
    stays connected and keeps the previous list
  - `test_connect_forwards_resolved_url_and_headers` — resolved URL/headers
    forwarded into `run`
  - Confirmed red via `make test PYTEST_ARGS='tests/test_mcp_client_tab.py
    tests/test_mcp_client_presenter.py --tb=short -q'`: 5 new tests fail for
    the intended missing live-Connect behavior; existing tab/presenter tests
    still pass. No production code changed.
- [x] **STEP 4: Development**
  - [x] Live Connect/Refresh: GUI-thread `resolve_outbound_fields`, worker
    `MCPClientService.run` with resolved url/headers (`list_tools`); Connect
    fail → FAILED + empty tools; Refresh fail → stay CONNECTED + stale list
  - [x] Step 3 GUI tests in `tests/test_mcp_client_tab.py` are green
    (`make test PYTEST_ARGS='tests/test_mcp_client_tab.py
    tests/test_mcp_client_presenter.py --tb=short -q'`)
  - [x] `tabs_presenter.py` untouched; Connect/Refresh stay in presenter +
    mcp_client widgets (`McpClientOutboundWorker`, Refresh, error label,
    `FAILED` state)
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1169/40-code-cleanup.md`
  - `make lint` passed; `make analyze` is not a Makefile target
  - Dropped Step 3 `getattr` widget-id fallbacks; wrapped `tool_browser.py`
    imports; `tabs_presenter.py` still 779 / 785, not edited
  - Targeted tests passed: `test_mcp_client_tab.py`,
    `test_mcp_client_presenter.py`, `test_tabs_presenter.py`
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1169/50-observability.md`
  - Connect/Refresh `list_tools` logs: `connection_id`, `kind`, `tool_count` only
    (no secrets, header values, or URLs)
  - Outbound counters `mcp_client_connect_total{result}` and
    `mcp_client_list_tools_total{result,operation}` (distinct from inbound
    `mcp_requests_received_total`); presenter optional `metrics=` so
    `tabs_presenter.py` stays untouched
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1169/60-tech-debt.md`
  - Already-ticketed: PYPOST-1170 (call_tool), PYPOST-1184 (tabs_presenter
    extract), PYPOST-1186 / 1187 / 1188 still relevant
  - Factory `metrics=` injection deferred (tabs_presenter 779 / 785, no
    growth this story)
  - No new Jira creates in this step
- [x] **STEP 8: Dev Docs**
  - `doc/dev/mcp_client_draft_tab.md` — live Connect/Refresh `list_tools`:
    GUI-thread resolve, worker `run`, Connect vs Refresh error chrome,
    tool browser name/description, outbound metrics, secret-safe logs
  - Catalogs: `doc/dev/logging.md`, `doc/prometheus_monitoring.md`,
    `doc/dev/README.md`, `doc/dev/presenter_architecture.md`,
    `doc/dev/ui_identity.md`, `doc/dev/mcp_integration.md`,
    `doc/dev/new_tab_protocol_picker.md`
  - `doc/user/` not rewritten (PYPOST-1168)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1169/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1169/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_mcp_client_tab.py` (red GUI tests for live Connect / Refresh)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1169/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1169/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1169/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_client_draft_tab.md`
- `doc/dev/logging.md`
- `doc/prometheus_monitoring.md`
- `doc/dev/README.md`
- `doc/dev/presenter_architecture.md`
- `doc/dev/ui_identity.md`
- `doc/dev/mcp_integration.md`
- `doc/dev/new_tab_protocol_picker.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and
  commit hash are reported in chat only, never written to this file.
