# PYPOST-599: Code Cleanup

## Actions

- Removed hardcoded shortcut table from `hotkeys_dialog.py`; dialog now calls `collect_hotkey_rows`.
- Centralized registration in new `pypost/ui/hotkeys.py` (~150 LOC).
- Replaced `MainWindow` anonymous `QShortcut` lambdas with named `register_hotkey` calls.
- Removed `MainWindow.keyPressEvent` Ctrl+Return override; send uses `register_hotkey` binding.
- `RequestEditor` uses `QAction.setShortcut` + `addAction` instead of parallel `QShortcut`s.

## Lint / format

| Scope | Result |
| --- | --- |
| `pypost/ui/hotkeys.py` | Clean |
| `pypost/ui/dialogs/hotkeys_dialog.py` | Clean |
| `pypost/ui/main_window.py` | Clean |
| `tests/test_hotkeys.py` | Clean |
| `pypost/ui/widgets/request_editor.py` | Pre-existing E501 line 63 — not introduced here |

- Line length ≤ 100 characters in all new/edited lines.
- UTF-8, LF, final newline on all touched files.

## Test run

```text
10 passed — test_hotkeys (5), test_main_window (5)
64 passed — test_save_flow_integration, test_request_editor_gui_metrics, test_tabs_presenter
```
