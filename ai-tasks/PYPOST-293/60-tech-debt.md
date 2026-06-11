# PYPOST-293: Technical Debt Analysis

## Shortcuts Taken

- **Plus placeholder tab in QTabWidget count**: The trailing `+` tab is a real (empty) tab page in
  `QTabWidget`, increasing raw `count()` by one. Business logic filters via `RequestTab` type or
  `_request_tab_count()` — acceptable trade-off for native tab-bar layout.

## Code Quality Issues

- None introduced. Manual geometry code and `TabBarWithAddButton` were removed.

## Missing Tests

- No headless UI test verifies visual alignment after window resize (plus tab layout is managed by
  Qt; behavior covered indirectly by unit tests).
- No automated test asserts `Ctrl+N` and `+` tab click emit identical metrics (pre-existing gap
  from PYPOST-32 follow-ups).

## Performance Concerns

- None. Removing manual reposition on every `layout_changed` / resize slightly reduces work.

## Resolved Debt (from PYPOST-32)

- Manual `+` button geometry with pixel offsets and fixed size — **resolved** by tab-bar
  `setTabButton` layout.

## Follow-up Tasks

- Optional Qt UI test for plus-tab placement after resize — low priority; native layout should
  handle this.
- Typed new-tab source enum for metrics (`PYPOST-294`) — unchanged scope.

## Verdict

**SAFE TO CLOSE** — no blockers.
