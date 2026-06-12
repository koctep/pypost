# PYPOST-427: Dev Docs

## Updated

| File | Change |
| --- | --- |
| `doc/dev/testability.md` | `ConfigManager` / `AppSettings` / `AlertManager` in composition-root table; new ConfigManager lifecycle section |
| `doc/dev/architecture.md` | New "Composition root (`main.py`)" section with startup flow |
| `pypost/main.py` | Inline composition-root comment (cross-reference for readers in IDE) |

## Rationale

Closes PYPOST-404 TD-3: future refactors should preserve single `settings.json` load and
understand why `ConfigManager` precedes `MainWindow` construction.
