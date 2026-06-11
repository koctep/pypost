# PYPOST-416 — Architecture

## Approach

Add one unittest method alongside existing stale-path tests in `tests/test_worker_race.py`.

## Test Design

| Test | Purpose |
|------|---------|
| `test_stale_worker_cleared_allows_new_worker` (PYPOST-415) | Behavioral: stale ref cleared, new worker created |
| `test_stale_worker_cleared_emits_debug_log` (new) | Observability: DEBUG log on stale guard |

## Setup (shared pattern)

1. Create `TabsPresenter` with one tab and `RequestData(method="GET", url="http://x")`.
2. Assign a mock worker with `isRunning() -> False` to `tab.worker`.
3. Emit `send_requested` on the tab editor.

## Log capture

Use `unittest.TestCase.assertLogs("pypost.ui.presenters.tabs_presenter", level=logging.DEBUG)`
matching `tests/test_env_presenter.py` convention.

Filter records for `stale_worker_cleared` and assert method/URL appear in the message.

## Files

| File | Change |
|------|--------|
| `tests/test_worker_race.py` | Add test + `import logging` |
