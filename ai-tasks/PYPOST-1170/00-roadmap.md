# Roadmap: PYPOST-1170

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1170/00-roadmap.md`
  - `ai-tasks/PYPOST-1170/10-requirements.md`
  - Implementation language recorded: Python
  - Business-only summary:
    - Scope: after tools are listed, the user selects a remote tool,
      fills arguments from the advertised input schema (or JSON
      fallback), invokes `call_tool`, and inspects a structured result
      with timing
    - Depends on shipped
      [PYPOST-1169](https://pypost.atlassian.net/browse/PYPOST-1169)
      (MCP-TM-3: live Connect / `list_tools` / tool browser)
    - Connect, discovery, headers, picker, draft restore, and HTTP
      method **MCP** stay as shipped; migration is MCP-TM-6
    - Architecture pointer for Step 2 (later-step input only):
      `ai-tasks/PYPOST-1164/20-architecture.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1170/20-architecture.md`
  - Invoke on existing tab: GUI resolve + reused
    `McpClientOutboundWorker` `call_tool` (no held SDK session)
  - Schema classifier: simple form vs JSON vs no-arg; result pane +
    elapsed; failed invoke stays CONNECTED
  - `tabs_presenter.py` untouched (779/785); invoke UI in presenter +
    widgets
  - Step 3 failing-repro plan in Implementation Plan (Primary A/B/C)
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_mcp_client_tab.py` — Primary A/B/C GUI:
    `test_invoke_call_tool_displays_structured_result`,
    `test_invoke_error_keeps_connected_and_tools`,
    `test_nested_schema_json_fallback_invokes_object_arguments`,
    `test_empty_required_form_field_does_not_call_tool`
  - `tests/test_mcp_client_arg_schema.py` — Qt-free classifier
    (simple_form / json_only / no_args)
  - Mock `MCPClientService.run` only; no live MCP. Red today:
    missing Invoke/form/JSON/result chrome and missing
    `pypost.core.mcp_client_arg_schema`
- [x] **STEP 4: Development**
  - [x] Qt-free `pypost.core.mcp_client_arg_schema` (simple_form / json_only / no_args)
  - [x] Catalog keeps `inputSchema`; browser selection + UserRole name
  - [x] Invoke column: form, JSON fallback, Invoke, result pane + elapsed
  - [x] GUI `resolve_outbound_fields` then `McpClientOutboundWorker`
    `operation=call_tool` `kind=invoke` (no `tabs_presenter.py` edits)
  - [x] Failed invoke stays CONNECTED and keeps tools; validation blocks `run`
  - [x] Outbound `mcp_client_call_tool_total`; Step 3 tests green
  - [x] `sanitize_text` on invoke result `content` / `structuredContent` (FR-3.6 / NFR-4)

- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1170/40-code-cleanup.md`
  - `make lint` passed; `make analyze` is not a Makefile target
  - Dropped Step 3 widget-id `getattr` fallbacks; classifier tests use
    `ArgSchemaKind` directly
  - `tabs_presenter.py` unchanged (779 / 785)
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1170/50-observability.md`
  - Invoke logs: initiated / succeeded / failed / ignored (reason tokens)
  - No URL, headers, arguments, tool names, or secrets in logs
  - `mcp_client_call_tool_total{result}` on worker settle only
  - `tabs_presenter.py` unchanged (779 / 785)
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1170/60-tech-debt.md`
  - No AC-breaking debt; one-shot `run("call_tool")` (no held
    `ClientSession`) matches architecture
  - Linked existing keys:
    [PYPOST-1184](https://pypost.atlassian.net/browse/PYPOST-1184),
    [PYPOST-1186](https://pypost.atlassian.net/browse/PYPOST-1186),
    [PYPOST-1168](https://pypost.atlassian.net/browse/PYPOST-1168)
  - No new Jira issues created in this step
- [x] **STEP 8: Dev Docs**
  - `doc/dev/mcp_client_draft_tab.md` — invoke: schema form, JSON
    fallback, result pane + timing, failed invoke stays CONNECTED,
    sanitized results, `call_tool` metrics/logs
  - `doc/dev/README.md`, `doc/dev/logging.md`,
    `doc/dev/ui_identity.md`, `doc/dev/mcp_integration.md`,
    `doc/prometheus_monitoring.md`, `doc/dev/new_tab_protocol_picker.md`
  - `doc/user/` not rewritten (MCP-TM-8 / PYPOST-1168)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1170/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1170/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_mcp_client_tab.py`
- `tests/test_mcp_client_arg_schema.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1170/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1170/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1170/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_client_draft_tab.md`
- `doc/dev/README.md`
- `doc/dev/logging.md`
- `doc/dev/ui_identity.md`
- `doc/dev/mcp_integration.md`
- `doc/dev/new_tab_protocol_picker.md`
- `doc/prometheus_monitoring.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and
  commit hash are reported in chat only, never written to this file.
