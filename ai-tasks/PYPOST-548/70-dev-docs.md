# PYPOST-548: Dev Docs Update

## Summary

Verified `doc/dev/testing.md` already describes the per-test timeout policy implemented in this
task. No substantive edits were required — the documentation was ahead of the implementation
(PYPOST-414 era) and is now accurate.

## Files Reviewed

| File | Action |
| ---- | ------ |
| `doc/dev/testing.md` | Verified — matches `Makefile`, `pytest.ini`, `conftest.py` |
| `.cursor/lsr/do-testing.md` | Verified — tier guidance matches rollout (30/60/120s) |

## Implementation Notes (for developers)

### Root cause — `make test` hang

Saving an overwrite that renames a request while a clean sibling tab is open caused
`_on_request_persisted` to sync tab labels **before** evaluating sibling dirtiness. Because tab
and editor share one `RequestData`, the sibling appeared dirty and triggered
`prompt_dirty_sibling_tab_reload` — a modal `QMessageBox.exec()` that blocks forever under
`QT_QPA_PLATFORM=offscreen`.

**Fix:** resolve sibling staleness first; sync labels after the loop
(`pypost/ui/presenters/tabs_presenter.py`).

### Timeout enforcement

- `make venv-test` installs `pytest-timeout`.
- `pytest.ini` registers the `timeout` marker (no global default).
- `tests/conftest.py` fails setup when a test lacks a closest `timeout` marker.
- Every `tests/test_*.py` declares `pytestmark = pytest.mark.timeout(N)`.

Run: `make test` — must always complete with a pass/fail verdict.
