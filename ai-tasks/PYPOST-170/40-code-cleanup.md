# PYPOST-170: Code Cleanup

## Checklist

- [x] Module docstring references PYPOST-170.
- [x] `_scrape` helper mirrors `tests/test_metrics_manager.py` pattern.
- [x] Explicit `pytest.mark.timeout(60)` at module scope (GUI tier).
- [x] `QTest.qWaitForWindowExposed` before mouse click.
- [x] No unused imports; LF endings; lines ≤ 100 characters.

## Files Touched

- `tests/test_request_editor_gui_metrics.py`
