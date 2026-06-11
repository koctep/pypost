# PYPOST-365: Architecture — GUI test patterns and ResponseView search tests

## Current State

PyPost GUI tests use **PySide6** with a headless platform, not the `pytest-qt` package:

| Layer | Mechanism |
| --- | --- |
| Platform | `QT_QPA_PLATFORM=offscreen` in `tests/conftest.py` (before Qt imports) and `Makefile` `test` target |
| Application | Module-scoped `qapp` fixture: `QApplication.instance() or QApplication([])` |
| Timeouts | Module `pytestmark = pytest.mark.timeout(60)` (or 120 for e2e) |
| Assertions | Direct widget property/method calls; `unittest.mock` for dialogs and metrics |

Representative modules: `tests/test_env_dialog.py`, `tests/test_settings_dialog.py`,
`tests/test_settings_encryption_migration_ui.py`, `tests/test_new_variable_flow_integration.py`.

## Planned Changes

### 1. Shared `qapp` fixture (`tests/conftest.py`)

Add module-scoped `qapp` so new GUI tests do not duplicate the fixture. Existing modules keep
local fixtures (pytest resolves the closest fixture; no mass migration).

### 2. ResponseView search tests (`tests/test_response_view_search.py`)

| Scenario | Method / trigger | Expected |
| --- | --- | --- |
| Typed search | `_on_search_text_changed` after `setText` | `1 of N` counter |
| No matches | query not in body | `No matches` |
| Find next | `_find_next` | counter increments |
| Find previous | `_find_previous` | counter decrements |
| Match case | `search_case_cb` toggled | count changes |
| Metrics | `metrics=MagicMock()` | `track_gui_response_search_action` called |
| New response | `display_response` | search input and status cleared |

Tests instantiate `ResponseView` directly (widget-level), matching `test_new_variable_flow_integration.py`.

### 3. Developer documentation

- New `doc/dev/gui_testing.md` — patterns, fixture, timeouts, focused commands.
- Update `doc/dev/testing.md` — link and short GUI subsection.

## Out of Scope

- `qtbot` / `pytest-qt` signals API.
- Xvfb in CI (offscreen is sufficient on Linux/macOS CI runners).

## Risks

| Risk | Mitigation |
| --- | --- |
| Qt event loop timing | Call handler methods directly; avoid unbounded `processEvents` loops |
| Flaky match index | Use deterministic plain text bodies; assert label strings |
