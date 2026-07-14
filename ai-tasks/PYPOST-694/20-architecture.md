# PYPOST-694: Inject HistoryManager from composition root

## Research

### Current state (pre-change)

```75:75:pypost/ui/main_window.py
        self.history_manager = HistoryManager()
```

`HistoryManager` was passed to `TabsPresenter` → `RequestWorker` → `RequestService` but
constructed inside `MainWindow`, outside `main.py` and the `testability.md` injection table.

### Target wiring

```text
main.py
  history_manager = HistoryManager()
  MainWindow(..., history_manager=history_manager)
    → TabsPresenter(history_manager=...)
      → RequestWorker → RequestService
    → HistoryPanel(history_manager=...)
```

### Option analysis

| Option | Verdict |
| --- | --- |
| Required param on `MainWindow` | Rejected — breaks many tests without injection |
| Optional param + fallback `HistoryManager()` | **Selected** — matches `ConfigManager` pattern |
| Factory in `main.py` only, remove fallback | Rejected — tests need lightweight substitute |

## Implementation Plan

1. Import and construct `HistoryManager` in `main.py` after `AlertManager`.
2. Add `history_manager: HistoryManager | None = None` to `MainWindow.__init__`.
3. Inject when provided; else construct locally (test fallback).
4. Log `history_manager_created` in `main.py`; DEBUG `history_manager_source` in `MainWindow`.
5. Update `testability.md` and `architecture.md`.
6. Replace `patch("pypost.ui.main_window.HistoryManager")` with `history_manager=MagicMock()`
   in MainWindow test helpers; assert retention in `test_constructor_stores_injected_dependencies`.

## Affected files

| File | Change |
| --- | --- |
| `pypost/main.py` | Create and inject `HistoryManager` |
| `pypost/ui/main_window.py` | Optional injection param |
| `doc/dev/testability.md` | Composition-root + MainWindow tables |
| `doc/dev/architecture.md` | Partial composition-root note |
| `tests/test_main_window*.py`, `tests/test_apply_settings_font.py`, settings e2e helpers | Inject mock |
