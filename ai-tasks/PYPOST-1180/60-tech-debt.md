# PYPOST-1180: Technical Debt Analysis

PYPOST-1180 closes verification debt from
[PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157) follow-up 7:
hermetic proofs that `NewTabProtocolPicker.prompt` maps HTTP confirm,
WebSocket confirm, and dismiss to `TabProtocol.HTTP`, `TabProtocol.WEBSOCKET`,
and `None`. Production was a **no-op**. There is **no AC-breaking debt** in
this task’s change. Remaining items are intentional hermetic shortcuts,
minor defensive-path gaps, and pre-existing suite noise already ticketed
elsewhere. None block Step 8.

## Shortcuts Taken

1. **Instance `menu.exec` mock instead of a live popup.** Same pattern as the
   existing MCP Client mapping test and as required by FR-4 / architecture
   R-2. `_install_fake_exec` wraps `build_menu` so the concrete menu gets a
   non-blocking `exec` that returns `actions()[i]` or `None`. CI still does
   not exercise real Enter / Esc / click-away against a blocking
   `QMenu.exec()`. That remains an intentional non-goal (same as
   PYPOST-1157 shortcut #1).

2. **Production mapping left untouched.** Step 3 proofs were green on first
   run against current `prompt()`; Step 4 did not edit
   `pypost/ui/widgets/new_tab_protocol_picker.py`. No production “crutch”
   was introduced — only additive tests.

3. **Outcome selection by action index.** HTTP / WebSocket / MCP proofs use
   `menu.actions()[0|1|2]`. That couples mapping tests to menu order, which
   construction tests already lock. Acceptable and matches the architecture
   outcome matrix; do not invent a parallel label-based lookup unless the
   menu grows further.

4. **Presenter / plus-tab / golden paths unchanged.** Injected-picker stubs
   still prove routing *given* a protocol. This ticket only locks the
   production picker mapper; end-to-end live popup + presenter remains out
   of scope.

## Code Quality Issues

No naming, layering, or architecture-deviation issues that require a
PYPOST-1180 follow-up fix. The shared `_install_fake_exec` helper matches
architecture’s optional test-local helper and removes duplicated
mock-`exec` wiring across HTTP / WebSocket / dismiss / MCP cases.

Noted for later cleanup, not for drive-by refactor in this ticket:

| Issue | Location | Notes |
| --- | --- | --- |
| Overlapping construction asserts | `test_build_menu_http_request_is_first_default` vs `test_build_menu_includes_mcp_client_as_third_item` | Both assert full label order and HTTP as `activeAction`. Pre-existing from PYPOST-1165; MCP test adds `actions()[2].data()`. Merge only if a later picker story retouches construction. |
| Defensive `prompt()` branches unasserted | `new_tab_protocol_picker.py` `data is None` / `ValueError` → `None` | Production defensive paths; not FR-1..3. Low risk while all menu actions set `TabProtocol` data. |
| `_anchor_point` / `anchor=` unused in unit proofs | `prompt()` positioning | Positioning does not affect mapping; hermetic tests call `prompt()` with defaults. Live plus-button anchor remains integration territory. |

Hardcoded labels and action indices match NFR / architecture; they are not
magic-value debt.

## Missing Tests

**Timeout markers: no BLOCKER.** Module declares
`pytestmark = pytest.mark.timeout(60)`. All six tests in
`tests/test_new_tab_protocol_picker.py` inherit it (construction + HTTP /
WebSocket / dismiss / MCP mapping).

In-scope AC coverage is present:

- `test_prompt_maps_http_request_action` → `TabProtocol.HTTP`
- `test_prompt_maps_websocket_action` → `TabProtocol.WEBSOCKET`
- `test_prompt_dismiss_returns_none` → `None`
- Existing MCP mapping and construction tests kept green
- No live blocking `QMenu.exec()` in CI

Gaps that remain (none are AC breaks for this debt item):

- **No live keyboard/mouse `exec()` test** — intentional hermetic shortcut;
  same non-goal as PYPOST-1157 / `doc/dev/new_tab_protocol_picker.md`.
- **No unit proof for `chosen.data() is None` or invalid `TabProtocol(data)`**
  — defensive branches only; FR-1..3 do not require them.
- **No unit proof for `_anchor_point` / explicit `anchor=`** — positioning,
  not outcome mapping.
- **Presenter still uses injected stubs for routing** — by design; does not
  substitute for (or replace) these mapper proofs.

This ticket **closes** PYPOST-1157 follow-up 7 (HTTP / WebSocket / dismiss
`prompt()` mapping). MCP Client product work remains
[PYPOST-1165](https://pypost.atlassian.net/browse/PYPOST-1165) (mapping
already covered here and left intact).

## Performance Concerns

None for production (no production code changed).

Suite-side: three additive hermetic tests plus a shared mock helper add
negligible wall time under module `timeout(60)`. No new Qt modal waits,
network, or I/O.

## Follow-up Tasks

Phase D of the orchestrator creates Jira issues. Step 7 does not. Items
without a key stay unticketed for Phase D.

1. **NON-BLOCKER — intentional hermetic gap (observation only)**
   - Live `QMenu.exec()` / keyboard default / Esc dismiss against a real
     popup remains untested in CI. Reaffirmed by this task; do not add a
     blocking popup to the suite.
   - No new ticket unless product later requires interactive GUI coverage
     outside unit CI.

2. **NON-BLOCKER — optional defensive-path coverage**
   - Assert `prompt()` returns `None` when mocked `exec` yields an action
     with `data() is None`, and/or when `data()` is not a valid
     `TabProtocol` value (`ValueError` path).
   - Unticketed; only worth filing if a picker story starts adding actions
     without `setData` or non-enum payloads.

3. **NON-BLOCKER — construction test overlap**
   - Consider folding duplicate label/active-action asserts in the two
     `build_menu` tests when next touching that module.
   - Observation only; no new ticket.

4. **NON-BLOCKER — pre-existing / sibling suite debt (out of scope)**
   - Flaky WS UI lifecycle:
     [PYPOST-1181](https://pypost.atlassian.net/browse/PYPOST-1181)
   - Collections import UI hang:
     [PYPOST-1182](https://pypost.atlassian.net/browse/PYPOST-1182)
   - Requirements explicitly excluded these from PYPOST-1180.

5. **NON-BLOCKER — epic siblings (context only, not incomplete 1180 work)**
   - Blank WS draft editor:
     [PYPOST-1158](https://pypost.atlassian.net/browse/PYPOST-1158)
   - Close-last-tab picker reuse:
     [PYPOST-1159](https://pypost.atlassian.net/browse/PYPOST-1159)
   - User-doc rewrite:
     [PYPOST-1163](https://pypost.atlassian.net/browse/PYPOST-1163)
