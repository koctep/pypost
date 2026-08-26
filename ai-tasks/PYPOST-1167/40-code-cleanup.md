# PYPOST-1167: Code Cleanup Report

## Linter Fixes

No in-scope linter errors or warnings. `make lint` passed (flake8 on `pypost/`
plus documentation checks). `make analyze` is not a Makefile target (`No rule
to make target 'analyze'`). Closest gate is `make lint`.

## Code Formatting

Applied formatting changes:

- [x] Automatic code formatting — no project auto-format Make target; PEP 8
  import order applied by hoisting deferred widget imports to module scope
- [x] Indentation and alignment fixes — none required
- [x] Line length correction — all in-scope production lines are at most 100
  characters (`flake8` `max-line-length = 100`)

## Code Cleanup

Cleanup actions performed:

- Removed unused imports: 1 (`inspect` from
  `tests/test_mcp_client_presenter.py` after dropping Step 3 ctor fallbacks)
- Removed unused variables: 0
- Removed commented-out code: none
- Removed debug prints: none

Other cleanup:

- Hoisted `VariableAwareLineEdit` to module scope in
  `connection_bar.py` (was imported inside `__init__`)
- Hoisted `McpClientHeadersTable` to module scope in `mcp_client_tab.py`
  (was imported inside `_init_ui`)
- Clarified `McpClientHeadersTable.get_data()` by extracting the stripped
  key before writing the dict
- Dropped Step 3 `inspect.signature` / `object.__setattr__` /
  positional-`headers` fallbacks from `tests/test_mcp_client_presenter.py`;
  tests now construct `McpClientConnection(headers=...)` and
  `McpClientPresenter(env_vars=..., mcp_client=...)` directly and assert
  `run(..., headers=)` via `assert_called_once_with`
- Dropped `getattr(widget_ids, "MCP_CLIENT_HEADERS_TABLE", ...)` fallback
  in `tests/test_mcp_client_tab.py`; the test uses the constant

Unrelated dirty files (`mcp_server.py`, `port_allocation.py`, `AGENTS.md`,
PYPOST-1164 artifacts, PYPOST-1176 roadmap) were left untouched.

## Validation Results

Validation results:

- [x] All targeted tests passed (`make test PYTEST_ARGS=` listed below)
- [x] All tests have explicit timeout markers
- [x] No merge conflicts
- [x] Syntax is valid
- [x] Types are correct (if applicable) — no new type issues in in-scope
  files; `make typecheck` was not required for this step

Timeout markers:

- `tests/test_mcp_client_tab.py` — module `pytestmark` `timeout(30)`
- `tests/test_mcp_client_presenter.py` — module `pytestmark` `timeout(10)`
- `tests/test_tabs_presenter.py` — module `pytestmark` `timeout(60)`
- PYPOST-1173 method-MCP tests keep module `pytestmark` `timeout(60)`

Commands:

- `make lint` — passed
- `make analyze` — not available (target missing); closest gate is `make lint`
- Targeted `make test` (3 files passed):
  - `tests/test_mcp_client_tab.py`
  - `tests/test_mcp_client_presenter.py`
  - `tests/test_tabs_presenter.py`
- Targeted `make test` for PYPOST-1173 (node ids are dropped by the
  parallel runner; used `-k` on the two files; both files passed):
  - `tests/test_request_service.py` `-k forwards_resolved_headers or
    forwards_empty_headers`
  - `tests/test_mcp_client_service.py` `-k passes_headers_to_create_mcp`

## Notes

- Scope was limited to PYPOST-1167 outbound-headers files. `mcp_server.py`
  was not edited. PYPOST-1164 artifacts, `port_allocation.py`, and
  `AGENTS.md` were not cleaned.
- `tabs_presenter.py` remains **779 / 785** LOC (factory env kwargs +
  duck-typed env fan-out). Cosmetic wraps of the duck-typed `getattr`
  lines were not applied so the file stays off the PYPOST-376 cap.
- `McpClientPresenter` still logs Connect / Disconnect / teardown INFO
  events from earlier steps; further observability belongs in Step 6.
