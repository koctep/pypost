# PYPOST-1186: Technical Debt Analysis

PYPOST-1186 extracts one shared empty-row Key/Value editor
(`EmptyRowKeyValueTable` in
`pypost/ui/widgets/empty_row_key_value_table.py`) used by HTTP
`KeyValueTable`, `WebSocketKeyValueTable`, and `McpClientHeadersTable`,
with explicit `strip_keys` policy and FR-5 MCP decoupling from
`request_editor`.

There is **no AC-breaking debt** in this task’s change. Remaining items
are intentional product divergences preserved by policy, optional coverage
outside FR-1–FR-6, and sibling work already ticketed elsewhere. None block
Step 8.

Jira keys below that already exist are cited for context. **New follow-up
issues are not created in this step** (Phase D / orchestrator). Unticketed
items say `Jira: none`. Already-linked keys used here:
[PYPOST-1184](https://pypost.atlassian.net/browse/PYPOST-1184),
[PYPOST-1187](https://pypost.atlassian.net/browse/PYPOST-1187),
[PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167).

## Shortcuts Taken

1. **`strip_keys` policy instead of unifying collect semantics.** HTTP
   keeps raw keys (`strip_keys=False`); WS and MCP strip and drop
   whitespace-only keys (`True`). Requirements and architecture forbid
   inventing a global strip product rule in this debt.

2. **Shared `set_data` always `blockSignals`.** HTTP previously did not
   block; unified path follows Qt guidance and seeds an empty trailing
   row. Accepted as an internal safety improvement with FR-2 parity via
   tests (no `block_signals_on_set` flag needed).

3. **`set_read_only` on the shared class, unused by HTTP/MCP.** WebSocket
   still locks while connected; HTTP/MCP do not gain a new product lock
   feature (FR-6).

4. **Thin named wrappers keep call-site names.** No mass rename of
   `KeyValueTable` / `WebSocketKeyValueTable` / `McpClientHeadersTable`.

5. **No Ctrl+H / Collections / live Connect work.** Explicitly out of
   scope (sibling MCP-TM / presenter debt).

## Code Quality Issues

Implementation matches architecture: neutral shared module; wrappers
encode policy; MCP imports shared module only.

Noted for later cleanup, not for drive-by refactor in this ticket:

| Issue | Location | Notes |
| --- | --- | --- |
| HTTP vs WS/MCP strip divergence | `EmptyRowKeyValueTable._strip_keys` | Intentional product contract; unify only with a later product decision |
| `tabs_presenter.py` LOC headroom | presenter factory | Unrelated; already ticketed [PYPOST-1184](https://pypost.atlassian.net/browse/PYPOST-1184) |
| Optional GUI hover proofs on headers tables | env hover | Out of scope; [PYPOST-1187](https://pypost.atlassian.net/browse/PYPOST-1187) |
| Wrapper style `Optional[QWidget]` vs `QWidget \| None` | `connection_editor.py` | Pre-existing WS module style; not required for AC |

Hardcoded column labels **Key** / **Value** match existing surfaces; they
are not magic-value debt.

## Missing Tests

**Timeout markers: no BLOCKER.** Module declares
`pytestmark = pytest.mark.timeout(30)`. All cases in
`tests/test_empty_row_key_value_table.py` inherit it.

In-scope AC coverage is present:

- Shared module exports `EmptyRowKeyValueTable`
- HTTP / WS / MCP share ancestry
- FR-5: MCP headers/tab do not import `request_editor`; headers imports
  shared module
- HTTP unstripped key collect; WS/MCP strip + omit whitespace-only
- WS `set_read_only` toggles edit triggers
- Trailing empty-row growth on last-row Key edit
- Existing `tests/test_mcp_client_tab.py` headers UX kept green

Gaps that remain (none are AC breaks):

- **No dedicated HTTP Params/Headers GUI regression beyond strip/policy
  cases** — existing request-editor paths and Step 3 HTTP collect cover
  FR-2; full RequestWidget e2e was not required.
- **No `qtbot` mouse edit of trailing row** — suite uses `setItem` to
  fire `itemChanged` (same pattern as MCP headers tests).
- **No proof that HTTP `blockSignals` change alters user-visible cells**
  beyond populate/read-back — intentional; architecture preferred one
  path.

## Performance Concerns

None. Shared table is the same O(rows) get/set as the three prior copies;
`blockSignals` during populate avoids recursive row growth.

## Follow-up Tasks

No new Jira Debt issues required from this analysis for AC closure.

- **NON-BLOCKER — intentional product divergence:** unify HTTP vs WS/MCP
  key strip only if product later decides one collect rule —
  `Jira: none` (do not invent a ticket unless product asks).
- **NON-BLOCKER — already ticketed:** tabs_presenter insert-before-plus /
  LOC — [PYPOST-1184](https://pypost.atlassian.net/browse/PYPOST-1184).
- **NON-BLOCKER — already ticketed:** optional GUI hover proofs —
  [PYPOST-1187](https://pypost.atlassian.net/browse/PYPOST-1187).
- **NON-BLOCKER — intentional non-goal:** Ctrl+H for MCP Headers;
  Collections persist of MCP headers; live Connect wiring — owned by
  sibling MCP-TM work / prior debt notes.
- Pre-existing suite flakes unrelated to this extract: none observed in
  targeted runs for this task; no `NON-BLOCKER — pre-existing` node ids.

## Blocker close-check (execution self-review)

| Item | Classification | Rationale |
| ---- | -------------- | --------- |
| Timeout markers on new suite | NON-BLOCKER (satisfied) | Module `timeout(30)` present |
| FR-1 shared editor | NON-BLOCKER (satisfied) | Ancestry tests green |
| FR-5 MCP decoupling | NON-BLOCKER (satisfied) | Import graph asserts green |
| FR-2/3/4 strip / lock / empty-row | NON-BLOCKER (satisfied) | Dedicated cases green |
| Remaining strip divergence | NON-BLOCKER | Explicit requirements preserve-it |
| PYPOST-1184 / 1187 siblings | NON-BLOCKER | Out of scope; already ticketed |

**Verdict: SAFE TO CLOSE** — no AC blockers; proceed to Step 8.
