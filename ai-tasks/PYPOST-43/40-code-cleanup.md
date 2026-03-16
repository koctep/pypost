# PYPOST-43: Code Cleanup Report

## Summary

Decomposition of `MainWindow` (1041 LOC god-object) into three focused presenter classes.
Final state: `MainWindow` ≤ 175 total LOC / 159 non-empty LOC (composition root only).

## Files Changed

### New Files

| File | LOC | Purpose |
|---|---|---|
| `pypost/ui/presenters/__init__.py` | 9 | Re-exports all three presenter classes |
| `pypost/ui/presenters/collections_presenter.py` | 240 | CollectionsPresenter + tree logic |
| `pypost/ui/presenters/tabs_presenter.py` | 310 | TabsPresenter + RequestTab + TabBarWithAddButton |
| `pypost/ui/presenters/env_presenter.py` | 195 | EnvPresenter + env/MCP lifecycle |
| `tests/test_collections_presenter.py` | 165 | 13 unit tests |
| `tests/test_tabs_presenter.py` | 200 | 22 unit tests |
| `tests/test_env_presenter.py` | 195 | 17 unit tests |

### Modified Files

| File | Before | After | Change |
|---|---|---|---|
| `pypost/ui/main_window.py` | 1041 LOC | 175 LOC | -866 LOC (83% reduction) |

## Cleanup Actions Performed

### 1. Separation of Concerns
- Moved all tree-view logic into `CollectionsPresenter`.
- Moved `RequestTab`, `TabBarWithAddButton`, all tab/worker methods into `TabsPresenter`.
- Moved env-selector, MCP lifecycle, variable management into `EnvPresenter`.
- `MainWindow` reduced to: service instantiation, presenter instantiation, layout, signal wiring,
  menu bar, keyboard shortcuts, settings application, and window lifecycle.

### 2. Signal Architecture
Three additional signals were added beyond the architecture spec to close implementation gaps:
- `CollectionsPresenter.request_renamed(str, str)`: enables `TabsPresenter.rename_request_tabs`
  to be called without TabsPresenter needing a reference to CollectionsPresenter.
- `TabsPresenter.request_saved()`: notifies `CollectionsPresenter` to reload the tree after
  a save/save-as operation from within a tab.

### 3. Bug Fix in load_collections
- Removed a redundant `storage.load_collections()` call that preceded `reload_collections()`.
  The `reload_collections()` method already calls storage internally.

### 4. Private API Usage
- `MainWindow.open_settings` calls `self.env._on_env_changed(...)` directly. This is the
  least-invasive approach for the settings-changed flow; a future refactor could expose this
  as a public `EnvPresenter.reload_current_env()` method.

### 5. Script Output Stub
- `TabsPresenter._on_script_output` is a no-op stub. The original `MainWindow` delegated
  script output to an unimplemented downstream handler. Stub preserved for forward
  compatibility with the observability step (STEP 4 of the roadmap).

## Code Quality Checks

- Line length: all lines ≤ 100 characters confirmed.
- Language: Python 3.11+, PySide6 only.
- No new external dependencies introduced.
- No behavior change: all existing 51 unit tests pass.
- New tests: 52 tests covering all three presenters (all pass).

## Definition of Done Checklist

- [x] `pypost/ui/presenters/` exists with `__init__.py`, `collections_presenter.py`,
      `tabs_presenter.py`, `env_presenter.py`.
- [x] `MainWindow` contains no business logic beyond composition and window setup.
- [x] `main_window.py` is ≤ 175 total / 159 non-empty LOC (reduction from 1041).
- [x] All existing unit and integration tests pass (51 tests).
- [x] `tests/test_collections_presenter.py`, `tests/test_tabs_presenter.py`,
      `tests/test_env_presenter.py` exist and pass (52 tests).
- [x] No new lint errors; line length ≤ 100 characters throughout.
- [x] Each presenter can be instantiated in a test with mocked dependencies.
