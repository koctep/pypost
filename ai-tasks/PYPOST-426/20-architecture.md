# PYPOST-426: Architecture

## Scope

Single-signature change in `pypost/ui/main_window.py`. No call-site or runtime behavior changes.

## Design

| Component | Change |
|-----------|--------|
| `MainWindow.apply_settings` | `settings` → `settings: AppSettings` |
| Imports | `from pypost.models.settings import AppSettings` |

## Consistency

```text
TabsPresenter.apply_settings(self, settings: AppSettings) -> None
EnvPresenter.apply_settings(self, settings: AppSettings) -> None
MainWindow.apply_settings(self, settings: AppSettings) -> None   # after fix
```

## Call sites (unchanged)

- `__init__`: `self.apply_settings(self.settings)`
- `open_settings`: `self.apply_settings(self.settings)`
- `showEvent` deferred: `QTimer.singleShot(0, lambda: self.apply_settings(self.settings))`

All pass `AppSettings` instances from `StateManager` or `SettingsDialog`.

## Tests

No new tests required — typing-only change. Regression suite:
`tests/test_apply_settings_font.py`, presenter `apply_settings` tests.
