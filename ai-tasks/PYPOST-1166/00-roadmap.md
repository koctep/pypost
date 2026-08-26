# Roadmap: PYPOST-1166

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1166/00-roadmap.md`
  - `ai-tasks/PYPOST-1166/10-requirements.md`
  - Implementation language recorded: Python
  - Business-only summary:
    - Scope: blank MCP Client draft shell (URL, Connect/Disconnect, state,
      empty tool browser)
    - Choosing MCP Client opens an MCP Client workspace (not an HTTP request
      workspace)
    - Unsaved draft excluded from session restore until first save
    - Closing the tab releases the outbound session (FR-4.2)
    - Depends on shipped
      [PYPOST-1165](https://pypost.atlassian.net/browse/PYPOST-1165) picker/stub;
      this story fills draft chrome
    - Architecture pointer for Step 2 (later-step input only):
      `ai-tasks/PYPOST-1164/20-architecture.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1166/20-architecture.md`
  - Fill chrome **inside** shipped `McpClientTab` (PYPOST-1165 stub)
  - Do not grow `tabs_presenter.py` with URL / Connect / tools (cap 785 LOC, now ~765)
  - Draft omitted from `save_tabs_state` until first save (MCP-TM-7)
  - `close_tab` must call `presenter.teardown()`
  - Failing-repro design included for Step 3
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_tabs_presenter.py` :: `TestTabsPresenter`
    - `test_add_blank_mcp_client_tab_creates_draft`
    - `test_save_tabs_state_omits_unsaved_mcp_client_draft`
    - `test_close_tab_calls_mcp_client_presenter_teardown`
  - `tests/test_mcp_client_tab.py`
    - `test_draft_shell_has_url_connect_disconnect_state_and_empty_tools`
  - Red on missing chrome / `connection_data` / `close_tab` teardown (not
    fixture breakage)
- [x] **STEP 4: Development**
  - [x] Implemented `McpClientConnection` + `McpClientSessionState`
  - [x] Implemented `McpClientPresenter` (local connect/disconnect/teardown; no SDK)
  - [x] Filled `McpClientTab` chrome (URL, Connect, Disconnect, state, empty tools)
  - [x] Thin factory wiring + duck-typed `close_tab` teardown; drafts omitted from `save_tabs_state`
  - [x] Targeted tests green; `tabs_presenter.py` 771/785 LOC
  - [x] Regenerated `ai-tasks/PYPOST-376/baseline-metrics.md` snapshot (765 → 771)
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1166/40-code-cleanup.md`
  - PEP 8 import order in `pypost/models/mcp_client.py`
  - Dropped Step 3 ctor fallbacks in `tests/test_mcp_client_tab.py`
  - Hoisted `McpClientConnection` in `tests/test_tabs_presenter.py`
  - Review-gap: direct `set_tab` / tab members; removed unused
    `McpClientToolBrowser.count()`
  - `make lint` passed; targeted `make test` on
    `tests/test_mcp_client_tab.py` and `tests/test_tabs_presenter.py` passed
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1166/50-observability.md`
  - Documented existing picker INFO + `gui_new_tab_actions_total{protocol=mcp_client}`
  - Added INFO: `mcp_client_connect_initiated`, `mcp_client_disconnect_initiated`
    (kept `mcp_client_presenter_teardown`); no URL dumps
  - No new Prometheus counters, Grafana dashboards, or live MCP metrics
  - Caplog: `tests/test_mcp_client_tab.py::test_presenter_logs_connect_disconnect_teardown`
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1166/60-tech-debt.md`
  - No AC-breaking debt; Connect is local chrome (MCP-TM-3)
  - `tabs_presenter.py` **771 / 785** (~14 LOC headroom) recorded as capacity debt
  - Follow-ups classified; new Jira deferred to Phase D except
    already-linked 1167, 1169, 1170, 1168, 1183
- [x] **STEP 8: Dev Docs**
  - `doc/dev/mcp_client_draft_tab.md` (new)
  - Cross-links updated; `doc/user/` not rewritten (PYPOST-1168)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1166/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1166/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_tabs_presenter.py` (draft factory, restore omission, teardown)
- `tests/test_mcp_client_tab.py` (draft-shell chrome)

### STEP 4: Development

- Source code
- Tests
- `ai-tasks/PYPOST-376/baseline-metrics.md` (snapshot regenerated; tabs_presenter 771)

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1166/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1166/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1166/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_client_draft_tab.md` (new)
- Cross-links: `doc/dev/README.md`, `new_tab_protocol_picker.md`,
  `ui_identity.md`, `presenter_architecture.md`, `mcp_integration.md`,
  `request_actions.md`, `websocket_ui_client.md`, `logging.md`,
  `state_manager.md`
- `doc/user/` not rewritten (PYPOST-1168)

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
