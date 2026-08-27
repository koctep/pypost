# PYPOST-1185: Technical Debt Analysis

PYPOST-1185 closes verification debt from
[PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166) follow-up 7:
hermetic proofs that clicking **Connect** / **Disconnect** updates the
connection-state badge without a live MCP server. Production was a
**no-op**. There is **no AC-breaking debt** in this task’s change. Remaining
items are intentional hermetic shortcuts and coverage gaps outside FR-1–FR-5.
None block Step 8.

## Shortcuts Taken

1. **Injected `MagicMock` mcp_client instead of a live server.** Same pattern
   as existing live Connect / list_tools tests in
   `tests/test_mcp_client_tab.py`. CI never opens sockets; FR-2 / FR-2.3
   are satisfied by isolation, not by asserting `run` is never called.

2. **Production chrome left untouched.** Step 3 proofs were green on first
   run against current button → presenter → badge wiring; Step 4 did not
   edit `mcp_client_tab.py`, `connection_bar.py`, or
   `mcp_client_presenter.py`. No production “crutch” was introduced — only
   additive tests.

3. **`QPushButton.click()` instead of `qtbot.mouseClick`.** Matches suite
   style and pytest-qt guidance for normal interactions; does not exercise
   low-level mouse hit-testing geometry.

4. **Badge-focused asserts only.** Tests do not re-prove tool listing,
   invoke, headers, or metrics (NFR-4). Disconnect proof still requires a
   successful hermetic Connect first so the Disconnect control is enabled.

## Code Quality Issues

No naming, layering, or architecture-deviation issues that require a
PYPOST-1185 follow-up fix. New helpers `_click_disconnect` and
`_is_disconnected_badge` mirror existing `_click_connect` /
`_is_connected_badge` patterns.

Noted for later cleanup, not for drive-by refactor in this ticket:

| Issue | Location | Notes |
| --- | --- | --- |
| Overlap with list_tools Connect asserts | `test_connect_lists_tools_in_browser` vs `test_click_connect_updates_badge_to_connected_hermetic` | Both `_click_connect` and assert Connected; chrome test is narrower (badge + hermetic `run`). Keep both: tools test optimizes for browser content; chrome test is the FR-1 signal that cannot hide behind tools asserts. |
| `_is_disconnected_badge` vs `_is_failed_or_disconnected_badge` | helpers in `test_mcp_client_tab.py` | Failed and disconnected both count as “not connected” elsewhere; Disconnect FR-3 uses the stricter disconnected/idle helper. Clear enough; merge only if a later story retouches badge helpers. |

Hardcoded URL `_MCP_URL` and settle timeout `_CONNECT_SETTLE_S` match the
rest of the suite; they are not magic-value debt for this ticket.

## Missing Tests

**Timeout markers: no BLOCKER.** Module declares
`pytestmark = pytest.mark.timeout(30)`. New tests inherit it; Disconnect
settlement uses bounded `wait_until(..., timeout=_CONNECT_SETTLE_S)`.

In-scope AC coverage is present:

- `test_click_connect_updates_badge_to_connected_hermetic` → FR-1 / FR-2
- `test_click_disconnect_returns_badge_to_disconnected` → FR-3
- Explicit module timeout → FR-4
- Production unchanged → FR-5
- Existing MCP Client suite kept green

Gaps that remain (none are AC breaks for this debt item):

- **No live network Connect / Disconnect e2e** — intentional; hermetic
  isolation is the durable CI contract.
- **No proof of CONNECTING in-flight or connect-error badge copy via
  button path beyond existing error tests** — owned by sibling / prior
  stories; out of scope per requirements.
- **No `qtbot.mouseClick` / keyboard activation of Connect/Disconnect** —
  widget `.click()` is the suite standard; geometry hit-testing is a
  non-goal.
- **Presenter-direct logging tests still bypass buttons** — by design;
  this ticket adds control-click proof rather than replacing logging
  coverage.

## Performance Concerns

None for this change set. Two additional GUI tests reuse the existing
worker + `wait_until` settle pattern (~seconds bounded). Full-file
`tests/test_mcp_client_tab.py` remained ~2s wall-clock under `make test`.

## Follow-up Tasks

No new Jira Debt issues required from this analysis.

- **NON-BLOCKER — intentional non-goal:** live MCP server Connect/Disconnect
  e2e in CI — rejected by FR-2; keep hermetic injection.
- **NON-BLOCKER — optional later:** if badge helper vocabulary grows further
  (Failed vs Disconnected vs Idle), consider a single table-driven badge
  classifier used by both chrome and error tests — only when a story
  retouches those helpers.
- Pre-existing suite flakes unrelated to this chrome path: none observed
  in the targeted / full-file runs for this task; no
  `NON-BLOCKER — pre-existing` node ids to file from Step 4–7.
