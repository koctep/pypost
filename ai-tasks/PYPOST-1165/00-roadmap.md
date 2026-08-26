# Roadmap: PYPOST-1165

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1165/00-roadmap.md`
  - `ai-tasks/PYPOST-1165/10-requirements.md`
  - Implementation language recorded: Python
  - Scope: third picker item **MCP Client**; protocol identity `mcp_client`;
    new-tab metrics; HTTP Request remains first/default
  - Confirm outcome: non-HTTP placeholder tab is enough; dedicated MCP Client
    draft shell remains [PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166)
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1165/20-architecture.md`
  - Extend existing `NewTabProtocolPicker` (Option A); HTTP Request stays first + `setActiveAction`
  - `TabProtocol.MCP_CLIENT = "mcp_client"`; metrics allow-list must include `mcp_client` (else → `unknown`)
  - Explicit `open_blank_tab` MCP branch — must not fall through to `add_new_tab()` HTTP (1157 trap)
  - Placeholder: dedicated stub class `McpClientTab` (not `RequestTab` / `WebSocketTab` / bare `QLabel`); PYPOST-1166 fills chrome
  - `tabs_presenter.py` stays under 785 LOC (currently 746); stub widget in a new module
  - Failing-repro design: picker three-item tests; MCP confirm ≠ HTTP; scrape `protocol=mcp_client`
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_new_tab_protocol_picker.py` — existing two-item default test unchanged
    - `TestNewTabProtocolPicker::test_build_menu_includes_mcp_client_as_third_item`
      (red: two-item menu vs expected MCP Client third)
    - `TestNewTabProtocolPicker::test_prompt_maps_mcp_client_action`
      (red: `IndexError` on `actions()[2]`; instance `menu.exec` mock, no live exec)
  - `tests/test_tabs_presenter.py` :: `TestHandleNewTabProtocolPicker`
    - `test_handle_new_tab_mcp_client_confirm_opens_mcp_tab_not_http`
    - `test_open_blank_tab_mcp_client_does_not_fall_through_to_http`
    - `test_open_blank_tab_records_mcp_client_protocol`
      (red: `AttributeError` — `TabProtocol.MCP_CLIENT` missing)
    - `test_handle_new_tab_http_is_still_first_default`
      (red: two-item menu; existing two-item test left unchanged)
  - `tests/test_metrics_manager.py::TestMetricsManagerGuiTracking::test_track_gui_new_tab_action_records_mcp_client_protocol`
    (red: scrape records `protocol="unknown"`)
  - `tests/test_metrics_otel.py::test_track_gui_new_tab_action_records_mcp_client_protocol`
    (red: OTel counter for `mcp_client` is missing / `None`)
- [x] **STEP 4: Development**
  - [x] Iteration 1 — `TabProtocol.MCP_CLIENT = "mcp_client"`; third menu item **MCP Client** after WebSocket; HTTP stays first + `setActiveAction`; `prompt()` maps `MCP_CLIENT`
  - [x] Iteration 2 — New stub module `pypost/ui/widgets/mcp_client/mcp_client_tab.py` (`McpClientTab`); `MCP_CLIENT_TAB_PAGE` widget id
  - [x] Iteration 3 — Added `mcp_client` to `_NEW_TAB_PROTOCOLS` in `metrics_registry.py`
  - [x] Iteration 4 — Explicit `open_blank_tab` MCP_CLIENT branch; `add_blank_mcp_client_tab`; `_request_tab_count` includes `McpClientTab`
  - [x] Iteration 5 — Updated leftover two-item picker tests (`test_build_menu_http_request_is_first_default`, `test_handle_new_tab_http_is_default_first_item`)
  - [x] Iteration 6 — Regenerated SOLID snapshot `ai-tasks/PYPOST-376/baseline-metrics.md` (`tabs_presenter.py` 765 / 785)
  - `tabs_presenter.py` 765 LOC (cap 785)
  - Step 3 red tests green (see return for node ids)
  - Full `make test`: SOLID snapshot updated this task; `tests/test_agent_dialog_settle_e2e.py` segfaulted once (exit -11) then passed on re-run — flaky/pre-existing, tracked by [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115)

- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1165/40-code-cleanup.md`
  - `make lint` passed; `make analyze` has no Makefile target
  - Targeted `make test`: 6 files passed (picker, tabs_presenter, metrics
    manager/otel/registry, SOLID snapshot)
  - Cleanup: `prompt()` via `TabProtocol(data)`; package import of `McpClientTab`;
    hoisted test imports
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1165/50-observability.md`
  - No new log lines: existing `new_tab_action_completed source=%s protocol=%s`
    already records `mcp_client` on confirm; cancel stays `new_tab_action_cancelled`
  - Metric (Step 4): `gui_new_tab_actions_total{source, protocol}` with
    `_NEW_TAB_PROTOCOLS` including `mcp_client` (Prometheus + OTel)
  - No extra stub logs; no outbound MCP operation counters; no Grafana dashboards
  - Operator table: `doc/prometheus_monitoring.md` protocol list includes `mcp_client`
  - Validation via existing Step 4 tests (metrics manager / OTel / presenter)
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1165/60-tech-debt.md`
  - Stub vs PYPOST-1166 chrome: intentional; no AC-breaking 1165 debt
  - `tabs_presenter.py` 765 / 785 (~20 LOC headroom)
  - Missing tests: close-last-tab with MCP-only strip; stub title / widget id
  - NON-BLOCKER — pre-existing: `tests/test_agent_dialog_settle_e2e.py` segfault (PYPOST-1115)
- [x] **STEP 8: Dev Docs**
  - `doc/dev/new_tab_protocol_picker.md` — third item **MCP Client**;
    `TabProtocol.MCP_CLIENT` / `mcp_client`; stub `McpClientTab`; metrics;
    HTTP Request remains default
  - Related: `doc/dev/request_actions.md`, `doc/dev/websocket_ui_client.md`,
    `doc/dev/mcp_integration.md`, `doc/dev/README.md`
  - User docs left to PYPOST-1168; `doc/prometheus_monitoring.md` unchanged
    (already listed `mcp_client` in Step 6)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1165/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1165/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_new_tab_protocol_picker.py`
- `tests/test_tabs_presenter.py`
- `tests/test_metrics_manager.py`
- `tests/test_metrics_otel.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1165/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1165/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1165/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
