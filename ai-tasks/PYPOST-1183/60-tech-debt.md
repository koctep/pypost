# PYPOST-1183: Technical Debt Analysis

PYPOST-1183 closes verification debt from
[PYPOST-1165](https://pypost.atlassian.net/browse/PYPOST-1165) follow-up 2:
hermetic presenter proofs that blank MCP Client open sets strip title
**New MCP Client** and widget id `pypost_mcp_client_tab_page`, that closing
the last HTTP tab while an MCP Client stub remains does not auto-open HTTP,
and that the suite `_request_tab_count` helper matches production
`(RequestTab, WebSocketTab, McpClientTab)`. Production was a **no-op**.
There is **no AC-breaking debt** in this task’s change. Remaining items are
intentional hermetic shortcuts, optional coverage left unadded, and
pre-existing / sibling suite debt already ticketed elsewhere. None block
Step 8.

Jira keys below that already exist are cited for context. **New follow-up
issues are not created in this step** (Phase D / orchestrator). Unticketed
items say `Jira: none`.

## Shortcuts Taken

1. **Direct `open_blank_tab(MCP_CLIENT)` instead of live picker confirm.**
   Title and identity proofs call the presenter API with
   `TabProtocol.MCP_CLIENT` (source `"shortcut"`). Same hermetic style as
   existing MCP routing tests. CI still does not exercise a live
   `QMenu.exec()` → blank MCP open path for those asserts. Intentional
   non-goal (NFR-3 / architecture R-3).

2. **Production left untouched.** Step 3 proofs were green on first run
   against shipped PYPOST-1165 title / id / count; Step 4 did not edit
   `pypost/`. No production “crutch” was introduced — only additive tests
   and a suite-helper widen.

3. **Optional FR-5 construction-only tests not added.** Existing
   `tests/test_mcp_client_tab.py` identity coverage was judged adequate
   (roadmap / architecture). Presenter path now locks title and id after
   blank open; constructor-only duplication was skipped on purpose.

4. **Sibling HTTP-only count helper left alone.**
   `tests/test_delete_open_tabs_integration.py` still counts `RequestTab`
   only. Architecture R-4 / requirements out of scope: that file covers
   the delete-open-tabs HTTP path, not FR-4 workspace emptiness for MCP.

## Code Quality Issues

No naming, layering, or architecture-deviation issues that require a
PYPOST-1183 follow-up fix. The module helper now mirrors production; the
four new proofs sit on existing
`TestHandleNewTabProtocolPicker` /
`TestCloseLastTabProtocolPicker` classes with module `timeout(60)`.

Noted for later cleanup, not for drive-by refactor in this ticket:

| Issue | Location | Notes |
| --- | --- | --- |
| Dual `objectName` asserts | `test_open_blank_tab_mcp_client_sets_widget_id` | Asserts both `MCP_CLIENT_TAB_PAGE` and the literal `"pypost_mcp_client_tab_page"`. Intentional drift guard (cleanup Step 5); leave as-is. |
| `_editor_tabs` omits MCP | `TestHandleNewTabProtocolPicker._editor_tabs` | Still `(RequestTab, WebSocketTab)` only. Helper name means “editor” tabs for picker-order tests, not non-empty count. Do not widen unless an MCP case starts using it for emptiness. |
| Delete-open-tabs helper still HTTP-only | `tests/test_delete_open_tabs_integration.py` `_request_tab_count` | Pre-existing; out of scope for FR-4. Widen only if a later story exercises MCP/WS in that integration file. |
| Pre-existing flake8 style in file | `tests/test_tabs_presenter.py` | E302/E304/W391 blank-line noise; not introduced by this delta; `make lint` does not gate `tests/`. |

Hardcoded title **New MCP Client** and id `pypost_mcp_client_tab_page`
match the PYPOST-1165 contract / NFR; they are not magic-value debt.

## Missing Tests

**Timeout markers: no BLOCKER.** Module declares
`pytestmark = pytest.mark.timeout(60)`. All new PYPOST-1183 methods in
`tests/test_tabs_presenter.py` inherit it.

In-scope AC coverage is present:

- `test_open_blank_tab_mcp_client_sets_title_new_mcp_client` → strip
  **New MCP Client**
- `test_open_blank_tab_mcp_client_sets_widget_id` →
  `objectName == MCP_CLIENT_TAB_PAGE` (+ literal)
- `test_request_tab_count_helper_counts_mcp_client` → helper aligns with
  production and stays ≥ 1 after last-HTTP close with MCP remaining
- `test_close_last_http_with_mcp_remaining_does_not_auto_open_http` → no
  `handle_new_tab` / no new blank HTTP; MCP remains
- Existing PYPOST-1165 picker / routing / metrics coverage kept green

Gaps that remain (none are AC breaks for this debt item):

- **No `accessibleIdentifier` assert** — `set_widget_id` mirrors
  `objectName` and `accessibleIdentifier`; proofs only lock
  `objectName`. Low risk while both are set together; optional add-on.
- **No picker-confirm → title/id path** — proofs use direct
  `open_blank_tab`; injected-picker routing tests already prove type.
  Combining picker confirm with title/id is optional hardening.
- **No sole-MCP last-tab close proof** — closing the only MCP tab (empty
  strip → `handle_new_tab("last_tab")`) is PYPOST-1159 product policy,
  not FR-3. FR-3 is last-HTTP-with-MCP-remaining only.
- **No WebSocket + MCP remaining close matrix** — FR-3 requires HTTP +
  MCP; WS + MCP remaining is unproven but same production count tuple.
- **Optional FR-5 construction tests not added** — intentional; existing
  `test_mcp_client_tab.py` coverage remains.
- **Delete-open-tabs helper still HTTP-only** — out of scope (see
  Shortcuts / Code Quality).

This ticket **closes** PYPOST-1165 follow-up 2 (title / identity /
last-HTTP-close-with-MCP / suite helper alignment).

## Performance Concerns

None for production (no production code changed).

Suite-side: four additive hermetic tests plus a one-line helper widen add
negligible wall time under module `timeout(60)`. No new Qt modal waits,
network, MCP SDK, or I/O.

## Follow-up Tasks

Phase D of the orchestrator creates Jira issues. Step 7 does not. Items
without a key stay unticketed for Phase D.

1. **NON-BLOCKER — intentional hermetic gap (observation only)**
   - Live `QMenu.exec()` → blank MCP open is not required for title/id
     proofs; direct `open_blank_tab` + injected picker routing remain the
     CI pattern.
   - No new ticket unless product later requires interactive GUI coverage
     outside unit CI.
   - Jira: none

2. **NON-BLOCKER — optional hardening**
   - Assert `accessibleIdentifier` (or both mirrors from `set_widget_id`)
     after blank MCP open; and/or assert title/id after injected picker
     confirm of MCP Client.
   - Unticketed; only worth filing if tooling starts relying on
     `accessibleIdentifier` without `objectName`.
   - Jira: none

3. **NON-BLOCKER — sibling suite helper drift**
   - Widen `tests/test_delete_open_tabs_integration.py` `_request_tab_count`
     to match production if that integration path starts covering
     WebSocket / MCP Client tabs.
   - Observation only until a story needs MCP/WS there.
   - Jira: none

4. **NON-BLOCKER — epic siblings (context only, not incomplete 1183 work)**
   - MCP Client draft shell:
     [PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166)
   - Close-last-tab / empty-workspace picker reuse:
     [PYPOST-1159](https://pypost.atlassian.net/browse/PYPOST-1159)
   - User-doc rewrite:
     [PYPOST-1168](https://pypost.atlassian.net/browse/PYPOST-1168)
   - Session persist / restore of MCP tabs — intentional omission until
     PYPOST-1166.

5. **NON-BLOCKER — pre-existing / sibling suite debt (out of scope)**
   - Flaky agent dialog settle / segfault cluster:
     [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115)
   - Requirements explicitly excluded sibling suite flakes from
     PYPOST-1183. No new pre-existing failures were observed on the
     focused or full `tests/test_tabs_presenter.py` runs for this task.
