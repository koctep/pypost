# Roadmap: PYPOST-1167

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1167/00-roadmap.md`
  - `ai-tasks/PYPOST-1167/10-requirements.md`
  - Implementation language recorded: Python
  - Business-only summary:
    - Scope: outbound headers on the MCP Client editor plus environment
      templating so auth reaches the remote MCP server
    - Headers table on the MCP Client draft (parity with HTTP Headers)
    - `{{ var }}` resolution from the active environment for headers
      (and URL on connect / send)
    - Resolved headers must actually be sent on outbound MCP calls
    - Also closes the HTTP method **MCP** send-time header gap until
      MCP-TM-6 retires that path
    - Depends on shipped
      [PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166)
      (MCP-TM-2 draft shell)
    - Parent research:
      `ai-tasks/PYPOST-1164/10-requirements.md` (FR-2.5)
    - Architecture pointer for Step 2 (later-step input only):
      `ai-tasks/PYPOST-1164/20-architecture.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1167/20-architecture.md`
  - Headers UI on MCP Client tab chrome; presenter owns resolve +
    `execute_outbound`; `MCPClientService` unchanged (PYPOST-1173)
  - FR-4 = regression on existing method-MCP tests; do not re-wire
    `_execute_mcp` or dirty `mcp_server.py` bind-wait
  - `tabs_presenter.py` stays ≤ 785 (771 now): duck-typed env fan-out only
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_mcp_client_tab.py::test_mcp_client_tab_has_headers_table`
        — red: `findChild` is `None` for
        `pypost_mcp_client_headers_table` (missing Headers table, not
        fixture/import breakage). Existing draft-shell and Connect INFO
        tests stay green.
  - [x] `tests/test_mcp_client_presenter.py::test_execute_outbound_forwards_resolved_url_and_headers`
        — red: `AttributeError: 'McpClientPresenter' object has no
        attribute 'execute_outbound'`
  - [x] `tests/test_mcp_client_presenter.py::test_execute_outbound_forwards_empty_headers`
        — same missing `execute_outbound` (empty `headers={}` contract)
  - [x] PYPOST-1173 method-MCP header tests stay green:
        `test_execute_mcp_forwards_resolved_headers_to_mcp_client`,
        `test_execute_mcp_forwards_empty_headers_to_mcp_client`,
        `test_run_passes_headers_to_create_mcp_http_client`
- [x] **STEP 4: Development**
  - [x] `McpClientConnection.headers`; `MCP_CLIENT_HEADERS_TABLE`;
        `McpClientHeadersTable` on MCP Client chrome (not `tabs_presenter.py`)
  - [x] URL `VariableAwareLineEdit`; env snapshot via
        `set_variables` / `set_hidden_keys` on URL + headers table
  - [x] `McpClientPresenter.execute_outbound` / `resolve_outbound_fields`
        using `TemplateService.render_string` and
        `MCPClientService.run(..., headers=)` (lazy client import)
  - [x] `TabsPresenter` factory env kwargs + duck-typed env fan-out;
        `tabs_presenter.py` **779 / 785**
  - [x] Regenerated `ai-tasks/PYPOST-376/baseline-metrics.md` (771 → 779)
  - [x] Step 3 tests green; PYPOST-1173 method-MCP header tests green
  - [x] Did not edit `pypost/core/qt/mcp_server.py` (inbound bind-wait
        stays out of this story)
  - Note: `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises`
        can segfault under parallel `make test` (Qt `apply_theme` vs
        uvicorn import). Isolated file run passes. Flaky / environment
        race; not a headers-table assertion failure. File separately if
        still red at gate.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1167/40-code-cleanup.md`
  - Hoisted URL/headers widget imports; dropped Step 3 test fallbacks
  - `make lint` + targeted presenter/tab/tabs + PYPOST-1173 method-MCP tests
  - Did not edit `pypost/core/qt/mcp_server.py`
  - `tabs_presenter.py` still **779 / 785**
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1167/50-observability.md`
  - DEBUG `mcp_client_outbound_fields_resolved` —
    `connection_id` + `header_count` only (no secret values)
  - Reused `mcp_operation_start header_count` (PYPOST-1173)
  - Connect INFO unchanged (`connection_id` only; no `headers`)
  - Test: `test_resolve_outbound_fields_logs_header_count_not_values`

- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1167/60-tech-debt.md`
  - No AC-breaking debt; Connect still local (MCP-TM-3)
  - `tabs_presenter.py` **779 / 785** (tight; PYPOST-1184)
  - Follow-ups: already-linked 1169 / 1170 / 1184 only; no new Jira
- [x] **STEP 8: Dev Docs**
  - `doc/dev/mcp_client_draft_tab.md` — Headers table + `execute_outbound`
    templating (living MCP Client tab doc)
  - Cross-refs: `doc/dev/ui_identity.md`, `logging.md`,
    `presenter_architecture.md`, `mcp_integration.md`,
    `variable_propagation.md`, `template_service.md`,
    `template_expression_functions.md`, `README.md`,
    `new_tab_protocol_picker.md`
  - Did not rewrite `doc/user/` (PYPOST-1168)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1167/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1167/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_mcp_client_tab.py` (`test_mcp_client_tab_has_headers_table`)
- `tests/test_mcp_client_presenter.py`
  (`test_execute_outbound_forwards_resolved_url_and_headers`,
  `test_execute_outbound_forwards_empty_headers`)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1167/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1167/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1167/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_client_draft_tab.md`
- `doc/dev/ui_identity.md`
- `doc/dev/logging.md`
- `doc/dev/presenter_architecture.md`
- `doc/dev/mcp_integration.md`
- `doc/dev/variable_propagation.md`
- `doc/dev/template_service.md`
- `doc/dev/template_expression_functions.md`
- `doc/dev/README.md`
- `doc/dev/new_tab_protocol_picker.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
