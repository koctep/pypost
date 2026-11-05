# PYPOST-1301: Technical Debt Analysis

Scope: WebSocket export-safe disposal on tab close and app exit —
`tabs_presenter_ws_export_teardown.py`, close/lifecycle wiring,
`WebSocketStreamView.abandon_export_for_shutdown`, and
`tests/test_pypost_1301_*.py`.

No item below is a **BLOCKER**. New/changed test modules declare
`pytestmark = pytest.mark.timeout(30)`. The do-testing timeout rule is met.

## Summary Table

| ID | Priority | Item | Follow-up | Jira |
| --- | --- | --- | --- | --- |
| TD-1 | Low | `wait_ms=100` literal duplicates `_WORKER_FINISH_WAIT_MS` | yes | [PYPOST-1476](https://pypost.atlassian.net/browse/PYPOST-1476) |
| TD-2 | Low | Deferred set via lazy `getattr` on presenter | no | accepted by design |
| TD-3 | Low | Duplicated blocked-export test helpers (1301/1286) | no | already [PYPOST-1304][] |
| TD-4 | Low | No dedicated `close_tabs_for_websocket_ids` busy-export test | yes | [PYPOST-1477](https://pypost.atlassian.net/browse/PYPOST-1477) |
| TD-5 | Low | Orphan finalize retry unbounded (mirrors 1286 TD-8) | no | accepted by design |
| TD-6 | Low | Nested `QEventLoop` on close/teardown (1286 TD-9) | no | accepted by design |
| TD-7 | Low | Deferred hidden page vs re-open same profile UX | no | accepted (arch risk 2) |
| TD-8 | Low | Exit budget may starve WS phase (`remaining_ms=0`) | no | accepted (arch risk 6) |
| TD-9 | Low | `stream_view.py` size (~1170 lines) after abandon API | no | monitor only |

## Shortcuts Taken

- **TD-2 (Low): presenter-private deferred set created on first use.**
  `ensure_deferred_set` uses `getattr(presenter, "_ws_export_deferred_pages", None)`
  instead of initializing the set in `TabsPresenter.__init__`. Avoids touching the
  large presenter constructor for a rarely hit edge path. Typed access would be
  cleaner; behavior is correct.
- **TD-1 (Low): hardcoded `wait_ms = 100` when `timeout_ms is None`.**
  Matches `cleanup()` / `_WORKER_FINISH_WAIT_MS` but is a duplicated literal in the
  helper so logs stay consistent without importing a private stream_view constant.
  Follow-up: export a shared named constant or pass `wait_ms` from `cleanup()`.
- **TD-7 / TD-8**: documented architecture risks accepted for this task — deferred
  pages are treated as disposed UI; fair-share exit budget may abandon immediately
  when request/MCP phases consume the share.

## Code Quality Issues

- **TD-5 / TD-6**: orphan finalize uses the same unbounded 10 ms join-retry pattern
  as view-owned finalize; `wait_for_export` still nests a `QEventLoop`. Both were
  accepted in PYPOST-1286 and remain bounded by process lifetime / exit budget.
- **TD-9**: `stream_view.py` grew with abandon + orphan helpers. No size-gate breach
  observed for this file; split only if a future size baseline flags it.

## Missing Tests

- **TD-4 (Low)**: busy-export coverage goes through `TabsPresenter.close_tab` →
  `close_workspace_tab`. `close_tabs_for_websocket_ids` uses the same helper but has
  no busy-export regression of its own. Session-teardown-before-dispose was added
  for that path; a thin busy-export assertion would lock it.
- **TD-3**: Event-blocked worker helpers remain duplicated across 1286/1301 modules;
  already ticketed as [PYPOST-1304][].

## Performance Concerns

- Tab close may spin a nested event loop for up to 100 ms while export is busy;
  exit uses remaining monotonic budget. No unbounded waits on production paths.
- Orphan workers hold a module-level set until `finished` + join; expected to be
  empty shortly after abandon. No measurable UI cost when idle.

## Follow-up Tasks

1. **TD-1 (Low)**: share `_WORKER_FINISH_WAIT_MS` (or equivalent) with the dispose
   helper so log `wait_ms` cannot drift from the actual cleanup budget.
   Jira: [PYPOST-1476](https://pypost.atlassian.net/browse/PYPOST-1476)
2. **TD-4 (Low)**: add a busy-export assertion on
   `close_tabs_for_websocket_ids` (or parametrize the existing close repro).
   Jira: [PYPOST-1477](https://pypost.atlassian.net/browse/PYPOST-1477)
3. **Already filed — do not re-file**: [PYPOST-1304][] (shared worker-hold test
   helpers).

No full-suite `make test` failures were introduced by this task's scoped runs
(`test_pypost_1301_*`, `test_pypost_1286_*`). Pre-existing suite failures from
PYPOST-1286 triage ([PYPOST-1298][], [PYPOST-1299][]) remain **NON-BLOCKER —
pre-existing** and were not re-run or re-filed here.

## Decision

**SAFE TO PROCEED** to Step 8. No BLOCKER debt. PYPOST-1286 TD-1 (this ticket) is
addressed on production close and exit paths.

[PYPOST-1304]: https://pypost.atlassian.net/browse/PYPOST-1304
[PYPOST-1298]: https://pypost.atlassian.net/browse/PYPOST-1298
[PYPOST-1299]: https://pypost.atlassian.net/browse/PYPOST-1299
