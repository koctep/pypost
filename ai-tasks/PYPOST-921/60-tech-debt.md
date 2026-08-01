# PYPOST-921: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: golden e2e creates a request via plus-tab when no blank
request tab remains, then completes Send → response settle. `PLUS_TAB_BUTTON`
is stamped on the embedded `+` control; unit test locks the id. Items below
are non-blocking.
**Do not create Jira tickets in this step** — list unticketed follow-ups
only (orchestrator skips Phase D ticket creation this run).

## Shortcuts Taken

- **No-blank precondition uses test-only strip.** Product `restore_tabs` still
  opens a blank tab; the scenario removes `RequestTab` pages via `removeTab` +
  `deleteLater` rather than changing restore. Matches architecture.
- **Settle waits root at current tab.** Shared helper uses
  `wait_for_text(tab, …)` instead of window-scoped `session.wait_for_text` so
  orphan role ids cannot poison settle. Actions already used
  `in_current_tab=True`.
- **`PLUS_TAB_BUTTON` stays out of `KEY_WIDGET_IDS`.** Same chrome policy as
  `PLUS_TAB_PLACEHOLDER`. Spot-check KEY catalog unchanged; header unit test
  covers the button id.
- **Full `make check` not re-run.** Step 5 validated lint + scoped golden /
  header tests (4 passed).

## Code Quality Issues

- None that block close. Implementation matches architecture:
  catalog constant; `set_widget_id` in `ensure_plus_tab`; golden composition
  via `ui_click(PLUS_TAB_BUTTON)`.

| Architecture | Implementation | Assessment |
| --- | --- | --- |
| `PLUS_TAB_BUTTON` constant | Present | Match |
| Stamp in `ensure_plus_tab` | After `QPushButton("+")` create | Match |
| Out of `KEY_WIDGET_IDS` | Not added | Match |
| Strip + plus + Send settle | Golden test | Match |
| Leave blank-restore golden | Unchanged happy path | Match |

## Missing Tests

- Fallback plus chrome (`tabBarClicked` without button) not composed in golden
  — unit tests already cover it; agent path is the primary button id.
- Ctrl+N shortcut create not covered in golden (out of scope per requirements).

## Performance Concerns

None. One extra agent e2e scenario; same Send settle budget as existing golden.

## Follow-up Tasks

| ID | Priority | Summary | Notes | Jira |
| --- | --- | --- | --- | --- |
| TD-1 | Low | Optional `AgentAppSession.wait_for_text(..., in_current_tab=)` | Session API still window-rooted; helper works around via free function | Already [PYPOST-949](https://pypost.atlassian.net/browse/PYPOST-949) |
| TD-2 | Low | Document `removeTab` orphan hazard for agent authors | Partially covered in golden docs; could live in ui_actions tip | [PYPOST-951](https://pypost.atlassian.net/browse/PYPOST-951) |

No blockers relative to acceptance criteria.
