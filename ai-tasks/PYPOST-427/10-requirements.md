# PYPOST-427: main.py creates ConfigManager before knowing it will be consumed

Related debt: [PYPOST-404](https://pypost.atlassian.net/browse/PYPOST-404) TD-3

## Goals

Preserve maintainability of the desktop startup path so future refactors do not accidentally
reintroduce duplicate `settings.json` loads or misread why `ConfigManager` is constructed early
in `main.py`.

## Programming Language

Python 3.10+ (PySide6).

## User Stories

- As a **maintainer**, I want the composition-root role of `ConfigManager` in `main.py` documented
  so I understand why settings are loaded before `MainWindow` is created.
- As a **reviewer**, I want architecture notes to state the single-load guarantee so refactors
  preserve one shared `AppSettings` instance across startup services and the UI.

## Definition of Done

- [x] Developer documentation explains why `main.py` creates `ConfigManager` and calls
  `load_config()` before `MainWindow`.
- [x] Documentation states that the same `ConfigManager` instance is injected into `MainWindow`.
- [x] `main.py` includes a brief inline comment at the composition root (no behavior change).
- [x] No duplicate `ConfigManager` instantiation introduced; reorder only if trivial and clearer.
- [x] Existing tests pass.

## Task Description

PYPOST-404 review (TD-3) flagged that `main.py` creates `ConfigManager()` early to obtain
`AppSettings` for `MetricsManager` and injects the manager into `MainWindow`. The flow is
correct; the risk is reader confusion if `MetricsManager` ever stops needing pre-loaded settings.
Document the intentional composition-root pattern rather than restructuring startup unless a
trivial reorder improves clarity without behavior change.

## Q&A

- **Reorder startup wiring?**
  Current order is required: `MetricsManager.start_server` and `AlertManager` need `AppSettings`
  before `MainWindow`. No reorder needed.
- **New tests?**
  Documentation-only; existing startup and persistence tests cover behavior.
