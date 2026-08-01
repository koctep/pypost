# PYPOST-837: Technical Debt Analysis

## Shortcuts Taken

- Text extraction covers common widgets (line/combo/label/button/text edits)
  only — exotic controls without a text API time out with `actual_text=None`
  rather than a dedicated “no text API” exception before waiting.
- Snapshot-predicate waits re-capture the full visible tree each poll; fine for
  agent settle intervals, not optimized for sub-millisecond tight loops.
- Session helpers always root at the main window (same as action helpers);
  multi-tab scoping still requires module-level calls with a tab root.

## Code Quality Issues

- `wait_for_snapshot` embeds a local node-count walker similar to
  `ui_snapshot._count_nodes` (private) — small duplication for diagnostics.
- `tests/helpers/qt_wait` re-exports only `wait_until`; condition helpers are
  agent-package APIs (intentional, but tests that need them import
  `pypost.agent`).

## Missing Tests

- No dedicated main-window test for “dialog appears after click” (golden flow /
  packaging stories can cover product dialogs). Fixture covers delayed create.
- No stress test for very large snapshot trees under rapid polling.

## Performance Concerns

- Polling at 50 ms with full snapshot capture can be relatively expensive if
  callers use long timeouts and heavy trees; document preferring
  `wait_for_widget` / `wait_for_text` when sufficient.

## Follow-up Tasks

Jira: [PYPOST-852](https://pypost.atlassian.net/browse/PYPOST-852)

| ID | Priority | Summary | Notes |
| --- | --- | --- | --- |
| TD-1 | Low | Share snapshot node-count helper between `ui_snapshot` and `ui_wait` | Delivered in [PYPOST-852](https://pypost.atlassian.net/browse/PYPOST-852) |
| TD-2 | Low | Optional “no text API” fast-fail when widget exists but text cannot be read | Delivered in [PYPOST-852](https://pypost.atlassian.net/browse/PYPOST-852) |
| TD-3 | Medium | Product dialog settle coverage in golden flow | Sibling story [PYPOST-919](https://pypost.atlassian.net/browse/PYPOST-919) |
| TD-4 | Low | Document recommend prefer widget/text waits over snapshot polls for hot paths | Delivered in [PYPOST-852](https://pypost.atlassian.net/browse/PYPOST-852) |

No blockers relative to acceptance criteria. Prior lifecycle wait duplication
(with `tests.helpers`) is resolved by production `ui_wait` + thin test re-export.
