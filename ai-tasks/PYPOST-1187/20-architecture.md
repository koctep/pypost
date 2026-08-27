# PYPOST-1187: Hermetic GUI proof — Headers table → execute_outbound + hidden-key hover

Step 2 artifact for
[PYPOST-1187](https://pypost.atlassian.net/browse/PYPOST-1187). Turns the
approved requirements in [`10-requirements.md`](10-requirements.md) into a
high-level architecture for **hermetic GUI verification** that:

1. Editing the MCP Client Headers table feeds `execute_outbound` →
   `run(..., headers=)`.
2. Hidden-key hover on that table masks secrets as `********`.

Parent / source:
[`ai-tasks/PYPOST-1167/60-tech-debt.md`](../PYPOST-1167/60-tech-debt.md)
item 5. Shared empty-row table extraction:
[PYPOST-1186](https://pypost.atlassian.net/browse/PYPOST-1186)
(`EmptyRowKeyValueTable`; `McpClientHeadersTable` remains the MCP wrapper).

**Scope:** automated regression signal only (FR from requirements). No new
Headers chrome.

**Not this story:** live Connect/invoke polish, Collections, Ctrl+H, user
docs, unrelated suite flakes.

## Research

### R-1 Ticket vs durable contract

| Source | Wording | Architectural reading |
| --- | --- | --- |
| Jira / debt item 5 | GUI test edits Headers then `execute_outbound` asserts `run(..., headers=)` from widget data; optional hover `********` | Verification debt — prove shipped path |
| Existing presenter tests | `McpClientConnection(headers=...)` without a tab | Misses `_sync_fields_from_tab` / live `headers_data()` |
| `test_mcp_client_tab_has_headers_table` | Empty-row UX + `get_data` only | Does not call `execute_outbound` |
| `test_connect_forwards_resolved_url_and_headers` | Headers seeded on draft ctor | Does not type into the table before send |
| WS hover pattern | `_resolve_cell_hover` + assert `********` | Reuse for MCP Headers table |

### R-2 Current codebase (repo facts)

| Area | Current state | Architectural impact |
| --- | --- | --- |
| `McpClientHeadersTable` | Thin `EmptyRowKeyValueTable(strip_keys=True)` | Target via `MCP_CLIENT_HEADERS_TABLE` / `pypost_mcp_client_headers_table` |
| `McpClientTab.headers_data` | `_headers_table.get_data()` | Sync source for presenter |
| `McpClientPresenter._sync_fields_from_tab` | Copies URL + `headers_data()` onto connection when tab is set | Must have `set_tab` / tab constructed so `_tab` is non-None |
| `execute_outbound` | `resolve_outbound_fields` → `_client().run(..., headers=)` | Sync, injectable `mcp_client=` — ideal hermetic seam |
| `VariableAwareTableWidget._resolve_cell_hover` | Uses `_variables` / `_hidden_keys`; masks hidden keys | Call from test like WS suite — no real mouse required |
| `tests/test_mcp_client_tab.py` | `pytestmark = timeout(30)`; `_build_draft_tab`; Headers empty-row test | **Primary change surface** |

### R-3 GUI / hermetic patterns

| Guidance | Adopt |
| --- | --- |
| Edit cells via `QTableWidgetItem` + `setItem` (existing Headers test) | Same for FR-1 |
| Injected `MagicMock` `mcp_client` | No network |
| Bound timeout via module `pytestmark` | Inherit `timeout(30)` |
| Hover: `_resolve_cell_hover(item)` (WS) | Prefer over brittle `QToolTip` mouse simulation |
| do-testing: no `timeout(method="thread")` for GUI | Keep process timeout |

### R-4 Options

| Option | Verdict |
| --- | --- |
| **A — Extend `test_mcp_client_tab.py`** with edit→`execute_outbound` + hover tests | **Chosen.** Suite cohesion, existing helpers |
| B — New module only for this debt | Rejected; thin assertions |
| C — Production refactor of sync path | Out of scope unless red |
| D — Only assert Connect click with typed headers | Weaker than debt wording (`execute_outbound`); Connect uses worker — sync `execute_outbound` is the clear contract under test |

### R-5 Verification-debt red/green reality

Product table → sync → resolve → `run` and hover masking already ship.
Step 3 writes **desired** assertions. Outcomes:

- **Red:** real sync/masking regression → Step 4 restores shipped contract only.
- **Green on first run:** coverage gap closed; Step 4 is harness-only polish
  (FR: no product feature work).

Do not use `xfail` / `skip`. Do not break production on purpose to force red.

## Implementation Plan

### High-level approach

Treat PYPOST-1187 as **test-suite architecture**. Extend
`tests/test_mcp_client_tab.py` with:

1. Type a header row on `pypost_mcp_client_headers_table`, set env vars for
   placeholders, call `tab.presenter.execute_outbound("list_tools")` with
   injected mock client, assert `run` received resolved `headers=`.
2. Populate a cell with `{{secret}}`, set `hidden_keys`, assert
   `_resolve_cell_hover` yields `********` and omits the secret.

Leave production modules untouched unless a proof exposes a defect.

### Suggested implementation order

1. Step 3: add the two GUI tests (reuse `_build_draft_tab`); run targeted
   suite; record red vs green.
2. Step 4: if red, fix only table→sync or hover fan-out; if green, land tests
   as permanent regression signal.
3. Confirm MCP Client coverage stays green via `make test` /
   `PYTEST_ARGS`.

### Mandatory — Failing Repro (next Step 3)

Write automated checks **before** any production change. No live MCP server.

**Sequencing:** this document → Step 3 tests in
`tests/test_mcp_client_tab.py` → run (red only if wiring broken; green closes
coverage) → Step 4 only if production must change.

#### Primary — Headers table → execute_outbound

**Module:** `tests/test_mcp_client_tab.py` (`pytestmark = timeout(30)`,
`qapp`).

| Test (suggested name) | Asserts (desired) |
| --- | --- |
| `test_headers_table_edit_execute_outbound_forwards_widget_headers` | Build tab with `mcp_client=MagicMock`, `env_vars` for token; find Headers table by `MCP_CLIENT_HEADERS_TABLE`; `setItem` Key/Value with placeholder; set URL (table or URL field as needed for a valid run call); call `presenter.execute_outbound("list_tools")`; assert `run` once with resolved `headers=` matching widget data after resolve |

Seed connection `headers={}` so the only source of header data is the
edited table (proves `_sync_fields_from_tab` / `headers_data`).

#### Secondary — hidden-key hover mask

| Test (suggested name) | Asserts (desired) |
| --- | --- |
| `test_mcp_client_headers_table_hover_masks_hidden_keys` | Build tab with `env_vars` + `hidden_keys`; set Headers value cell to `Bearer {{token}}` (or set_data); call `_resolve_cell_hover` on that item; assert `"********" in resolved` and secret value not in resolved |

**Out of Step 3:** Connect worker path, invoke, metrics, Collections, user
docs.

## Architecture

### Recommended approach

**Extend the existing MCP Client tab GUI suite** with hermetic proofs of
widget-backed headers on `execute_outbound` and secret hover masking.
Rely on shipped Presenter + Tab + `VariableAwareTableWidget`; inject a fake
outbound client so CI never opens network.

**Rationale:**

1. Requirements are verification debt, not a new UX story.
2. Widget id, empty-row edit pattern, and `execute_outbound` injection already
   exist; missing piece is the combined assert.
3. Sync `execute_outbound` is simpler and more direct than Connect worker for
   “headers= from widget data.”
4. Hover via `_resolve_cell_hover` matches WS suite and avoids flaky tooltip
   geometry.

### System modules and responsibilities

| Module | Responsibility this story |
| --- | --- |
| `tests/test_mcp_client_tab.py` | **Primary change surface.** Add edit→outbound + hover tests; keep module timeout |
| `pypost/ui/widgets/mcp_client/mcp_client_tab.py` | Unchanged unless sync/fan-out defective |
| `pypost/ui/widgets/mcp_client/headers_table.py` | Unchanged unless get_data / strip_keys defective |
| `pypost/ui/presenters/mcp_client_presenter.py` | Unchanged unless `_sync_fields_from_tab` / `execute_outbound` defective |
| `pypost/ui/widgets/variable_aware_widgets.py` | Unchanged; hover resolution already shared |
| `MCPClientService` / network | Substituted via injected mock |

### Main interfaces / APIs (test harness)

```python
# Edit Headers table then prove execute_outbound reads widget data
tab = _build_draft_tab(mcp_client=mock, env_vars={"token": "secret"}, url=_MCP_URL)
table = tab.findChild(QWidget, MCP_CLIENT_HEADERS_TABLE)
table.setItem(last, 0, QTableWidgetItem("Authorization"))
table.setItem(last, 1, QTableWidgetItem("Bearer {{token}}"))
tab.presenter.execute_outbound("list_tools")
mock.run.assert_called_once_with(
    _MCP_URL, "list_tools", None,
    headers={"Authorization": "Bearer secret"},
)

# Hidden-key hover on same table
resolved = table._resolve_cell_hover(table.item(0, 1))
assert "********" in resolved and "secret" not in resolved
```

### Patterns

- **Dependency injection** for hermetic outbound client.
- **Widget-id discovery** (`findChild` + `MCP_CLIENT_HEADERS_TABLE`).
- **No network** in CI for these checks.

### Explicit non-goals

- Changing Headers UX, Connect/invoke product behavior, or Collections.
- Importing HTTP `RequestEditor` into MCP Client.
- New Prometheus series or log events for this debt.

## Q&A

| Question | Answer |
| --- | --- |
| Why `execute_outbound` not Connect click? | Debt text names `execute_outbound`; sync path isolates header sync without worker timing. Connect already has a seeded-headers test. |
| Why not a new test file? | Suite already owns Headers empty-row + Connect proofs; keep cohesion. |
| Green on first run? | Acceptable for verification debt (same as PYPOST-1185 R-5). |
| Does PYPOST-1186 change the test target? | Still assert MCP table id / wrapper behavior; shared base is an implementation detail. |
