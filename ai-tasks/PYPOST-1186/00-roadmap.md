# Roadmap: PYPOST-1186

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1186/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1186/20-architecture.md`
  - Shared `EmptyRowKeyValueTable` in neutral `pypost/ui/widgets/empty_row_key_value_table.py`
  - Policies: `strip_keys` (HTTP False / WS+MCP True); `set_read_only` for WS; `blockSignals` on `set_data`
  - MCP must not import `request_editor`; thin wrappers keep call-site names
  - Step 3 red: shared type + FR-5 import decoupling + strip / `set_read_only` / empty-row cases
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_empty_row_key_value_table.py` — RED on missing shared module /
    ancestry / MCP→shared import; FR-5 + strip + `set_read_only` lock current
    contracts (pass today)
- [x] **STEP 4: Development**
  - [x] Added `pypost/ui/widgets/empty_row_key_value_table.py`
        (`EmptyRowKeyValueTable`: `strip_keys`, `blockSignals` `set_data`,
        `set_read_only`, trailing empty-row growth)
  - [x] Thin wrappers: `KeyValueTable` (`strip_keys=False`),
        `WebSocketKeyValueTable` / `McpClientHeadersTable` (`strip_keys=True`);
        MCP imports shared module only (no `request_editor`)
  - [x] Step 3 suite green:
        `make test PYTEST_ARGS='tests/test_empty_row_key_value_table.py'`;
        `make lint` clean; MCP/WS related table tests green
  - Full suite earlier: 285 passed / 0 failed / 1 skipped
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1186/40-code-cleanup.md`
  - `make lint` clean; `make analyze` N/A (no target)
  - Stale Step 3 “RED repro” docstring updated in
    `tests/test_empty_row_key_value_table.py`
  - Targeted tests green:
    `tests/test_empty_row_key_value_table.py`,
    `tests/test_mcp_client_tab.py`
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1186/50-observability.md`
  - Verdict: N/A — no new logs/metrics on shared Key/Value widget
    (header secrets must not be logged)
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1186/60-tech-debt.md`
  - Blocker close-check: **SAFE TO CLOSE** (no AC blockers)
- [x] **STEP 8: Dev Docs**
  - `doc/dev/empty_row_key_value_table.md` (new)
  - Updated `doc/dev/mcp_client_draft_tab.md`, `doc/dev/README.md`,
    `doc/dev/websocket_environments_templating_and_masking.md`
  - `make lint` + targeted `make test` green
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1186/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1186/20-architecture.md` (written; awaiting acceptance gate)

### STEP 3: Failing Repro

- `tests/test_empty_row_key_value_table.py` — shared type ancestry, FR-5 no
  mcp→request_editor import, strip / set_read_only / empty-row policies (RED
  until Step 4 extract)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1186/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1186/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1186/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
