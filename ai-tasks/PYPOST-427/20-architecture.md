# PYPOST-427: Architecture

## Scope

Documentation and a one-line comment in `pypost/main.py`. No runtime or API changes.

## Current startup flow

```text
main()
  ├─ QApplication
  ├─ ConfigManager() + load_config()  → AppSettings (single disk read)
  ├─ MetricsManager.start_server(settings.metrics_*)
  ├─ TemplateService(metrics=...)
  ├─ AlertManager(... from settings ...)
  └─ MainWindow(..., config_manager=config_manager)
        └─ StateManager(config_manager) shares same AppSettings object
```

## Design decisions

| Topic | Decision |
| --- | --- |
| Why ConfigManager is first | `AppSettings` required by metrics server bind and alert wiring before UI |
| Why inject into MainWindow | Single-load guarantee (PYPOST-404 FR-4); avoids second `load_config()` |
| Reorder? | No — dependents already follow settings load |
| Where to document | `doc/dev/testability.md` (composition root table), `doc/dev/architecture.md` (overview), inline comment in `main.py` |

## Artifacts

| File | Change |
| --- | --- |
| `pypost/main.py` | Composition-root comment above `ConfigManager()` |
| `doc/dev/testability.md` | Add `ConfigManager`, `AlertManager` rows; ConfigManager lifecycle subsection |
| `doc/dev/architecture.md` | New "Composition root" section with startup diagram |

## Tests

Regression only — `make test`. No new tests.
