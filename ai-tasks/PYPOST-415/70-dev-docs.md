# PYPOST-415: Dev Docs

## Updates

| File | Change |
|------|--------|
| `doc/dev/request_execution.md` | Tab worker lifecycle section (`_clear_tab_worker`, stale guard) |

## Content Added

- `TabsPresenter._clear_tab_worker` as sole authority for `tab.worker = None`.
- `_reset_tab_ui_state` limited to Send button restore.
- Explanation of Qt queued-signal gap and why stale guard remains in `_handle_send_request`.

## Verification

Documentation aligns with `tabs_presenter.py` and `tests/test_worker_race.py`.
