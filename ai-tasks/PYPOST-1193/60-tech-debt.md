# PYPOST-1193: Technical Debt Analysis

Four-line unpack arity fix in `pypost/core/collection_item_strategies.py`
(`manager, _` → `manager, _, _` in `_collection_delete` / `_collection_rename` /
`_request_delete` / `_request_rename`). Restores type-based delete/rename for
`"collection"` and `"request"` without API or dispatch redesign. **No
AC-breaking debt** remains for this ticket.

## Shortcuts Taken

1. **Thin arity alignment instead of attribute-only access.** Architecture
   preferred matching the existing 3-tuple (`manager, _, _`) used by
   websocket/MCP handlers over refactoring handlers to read
   `ctx.request_manager` (and registries) by attribute. Restores contracts with
   minimal blast radius; leaves positional unpack as the shared pattern.

2. **No broader `_unpack_context` redesign.** Dual path (`hasattr(ctx,
   "request_manager")` vs treating `ctx` as the manager) and `ctx: Any` remain
   unchanged. Out of DoD; changing return shape would break websocket/MCP
   handlers that need registry slots.

3. **No new tests.** Step 3 confirmed the five existing named regressions as the
   red suite; Step 4 made them green. No dedicated arity-contract unit test was
   added beyond those nodes.

## Code Quality Issues

| Issue | Location | Notes |
| ----- | -------- | ----- |
| Positional unpack still fragile | All `_unpack_context` call sites | A future 4th context field would reintroduce the same `ValueError` class unless every handler is updated together. Attribute access (or a typed DTO helper) would harden this; deferred per architecture. |
| Repeated ignore placeholders | Four collection/request handlers | `manager, _, _` matches peer style; extracting a `manager_only(ctx)` helper would be cosmetic only. |
| `_unpack_context` takes `Any` | `collection_item_strategies.py` | Pre-existing typing looseness; not introduced by this fix. |

Hardcoded strategy keys (`"collection"`, `"request"`, etc.) are intentional
registry contracts, not magic-value debt.

## Missing Tests

**Timeout markers: no BLOCKER.** Both in-scope modules declare
`pytestmark = pytest.mark.timeout(60)`:

- `tests/test_collection_item_strategies.py`
- `tests/test_request_manager_delete.py`

DoD coverage is present via the five named regressions (strategy delegation,
type-based delete, collection-type rename, empty-name rejection).

Optional gap (none required for AC):

- **No isolated arity-contract test** that asserts every built-in handler unpacks
  the current `_unpack_context` return length. The five named tests already
  fail loudly on mismatch; a static/parametrized guard would only catch drift
  earlier during refactor.

## Performance Concerns

None. Change is four unpack targets; no new I/O, loops, or allocations on the
delete/rename path.

## Follow-up Tasks

1. **Optional — harden context access against arity drift**
   Prefer attribute access (or a small typed helper) over positional unpack in
   built-in handlers so adding registry fields cannot break collection/request
   paths again. Priority: Low (architecture optional debt; not required for
   DoD). Unticketed — create only if maintainers want the hardening.

2. **Sibling Suite Failures Cleanup items (out of scope here)**

   | Item | Verdict | Jira |
   | --- | --- | --- |
   | SOLID `FILE_CAPS` drift (`test_audit_module_inventory_within_caps`) | NON-BLOCKER — pre-existing | [PYPOST-1194](https://pypost.atlassian.net/browse/PYPOST-1194) |
   | WebsocketDraftObservability caplog assertions (`test_tabs_presenter`) | NON-BLOCKER — pre-existing | [PYPOST-1195](https://pypost.atlassian.net/browse/PYPOST-1195) |
   | Flaky `test_update_tools_restarts_when_exposed_set_changes` (port-busy) | NON-BLOCKER — flaky | [PYPOST-1196](https://pypost.atlassian.net/browse/PYPOST-1196) |
   | `test_websocket_client_ui_repro.py` hang / isolation | NON-BLOCKER — pre-existing | [PYPOST-1181](https://pypost.atlassian.net/browse/PYPOST-1181) |

User `doc/` updates: N/A for this production unpack fix (dev docs owned by
Step 8 if needed).
