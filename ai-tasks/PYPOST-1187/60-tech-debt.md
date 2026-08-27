# PYPOST-1187: Technical Debt Analysis

PYPOST-1187 closes verification debt from
[PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167) item 5:
hermetic GUI proofs that editing the MCP Client Headers table feeds
`execute_outbound` → `run(..., headers=)`, and that hidden-key hover on
`pypost_mcp_client_headers_table` shows `********`. Production was a
**no-op**. There is **no AC-breaking debt** in this task’s change. Remaining
items are intentional hermetic shortcuts and coverage gaps outside this
debt’s DoD. None block Step 8.

## Shortcuts Taken

1. **Injected `MagicMock` mcp_client instead of a live server.** Same
   pattern as existing live Connect / list_tools tests. CI never opens
   sockets; `execute_outbound` calls the mock’s `run` only.

2. **Production chrome left untouched.** Step 3 proofs were green on first
   run against current table → `_sync_fields_from_tab` → resolve wiring and
   VariableAware hover masking; Step 4 did not edit MCP Client production
   modules. No production “crutch” — only additive tests.

3. **Hover via `_resolve_cell_hover` instead of mouse/`QToolTip`.** Matches
   WebSocket env-masking suite; avoids flaky geometry hit-testing while
   still asserting the masking contract on the MCP Headers table.

4. **Sync `execute_outbound` instead of Connect worker.** Debt text names
   `execute_outbound`; sync path isolates header sync without worker timing.
   Connect already has a seeded-headers forward test.

## Code Quality Issues

No naming, layering, or architecture-deviation issues that require a
PYPOST-1187 follow-up fix. New tests reuse `_build_draft_tab`,
`MCP_CLIENT_HEADERS_TABLE`, and `QTableWidgetItem` patterns from the empty-row
Headers test.

Noted for later cleanup, not for drive-by refactor in this ticket:

| Issue | Location | Notes |
| --- | --- | --- |
| Overlap with presenter `execute_outbound` tests | `test_mcp_client_presenter.py` vs new GUI test | Presenter tests seed connection headers without a tab; GUI test proves widget → sync. Keep both. |
| Overlap with Connect seeded-headers test | `test_connect_forwards_resolved_url_and_headers` | Seeds ctor headers; does not type into the table. New test closes that gap. |
| Private `_resolve_cell_hover` in tests | WS + MCP GUI suites | Same private helper used by WS masking tests; public tooltip API is mouse-driven. Acceptable until a public resolve helper exists. |

Hardcoded `_MCP_URL` and module `timeout(30)` match the rest of the suite;
they are not magic-value debt for this ticket.

## Missing Tests

**Timeout markers: no BLOCKER.** Module declares
`pytestmark = pytest.mark.timeout(30)`. New tests inherit it.

In-scope AC coverage is present:

- `test_headers_table_edit_execute_outbound_forwards_widget_headers` —
  edit table → `execute_outbound` → resolved `headers=`
- `test_mcp_client_headers_table_hover_masks_hidden_keys` — hover
  `********` / no secret leak
- Explicit module timeout; no network
- Production unchanged; existing MCP Client suite kept green

Gaps that remain (none are AC breaks for this debt item):

- **No live network Headers → Connect e2e** — intentional; hermetic
  isolation is the durable CI contract.
- **No mouseMove / `QToolTip.showText` proof on MCP Headers** — contract
  covered via `_resolve_cell_hover`; geometry is a non-goal.
- **No missing-placeholder (`{{ missing }}`) case** — HTTP parity; out of
  scope (called out in PYPOST-1167 debt).
- **No proof that Connect worker path re-reads mid-flight table edits** —
  sync `execute_outbound` is the named contract; Connect already seeds
  headers at construction in a separate test.

## Performance Concerns

None for this change set. Two additional GUI tests construct a draft tab
and call sync `execute_outbound` or hover resolve (no worker wait). Full-file
suite remains on the order of a few seconds.

## Follow-up Tasks

1. **NON-BLOCKER — intentional hermetic scope**
   - Live server e2e for Headers-gated Connect remains out of CI unit suite;
     owned by broader MCP Client live/e2e stories if needed.
   - Verdict: **NON-BLOCKER**.
   - Jira: none (no new ticket required)

2. **NON-BLOCKER — optional public hover-resolve helper**
   - Tests (WS + MCP) call `_resolve_cell_hover`. A public method would
     harden the contract without exposing private API in tests.
   - Verdict: **NON-BLOCKER**.
   - Jira: none (ticket later if suites keep growing private-API asserts)

No AC-breaking or timeout-marker blockers. **SAFE TO CLOSE** after
orchestrator review of Steps 1–8.
