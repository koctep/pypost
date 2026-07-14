# Code Quality and Maintainability Audit

This document summarizes the PyPost code quality and maintainability audit (PYPOST-687). It
complements [solid_audit.md](solid_audit.md) (SOLID and regression caps) and cross-references
[test_audit.md](test_audit.md) (suite health).

## Audit Report

Full report:
[ai-tasks/PYPOST-687/30-audit-report.md](../../ai-tasks/PYPOST-687/30-audit-report.md)

**Date:** 2026-06-12 | **Scope:** Lint, complexity, duplication, naming, error handling, SOLID
alignment, dead code

## Executive Summary

| Metric | Value |
| --- | --- |
| `pypost/` modules | 141 |
| `pypost/` LOC | ~16,425 |
| `make lint` | **FAIL** (4 flake8 violations) |
| SOLID cap check | **FAIL** (3 violations) |
| Functions ≥80 LOC | 12 |
| `except Exception` in `pypost/` | 29 |

Since PYPOST-40, **MainWindow shrank from 1,040 to 383 LOC** and presenters own most orchestration.
MetricsManager and `template_service` globals were replaced with injection. **Regressions:** caps
exceeded on `main_window` and `template_service`; lint no longer clean.

## Lint Hygiene

```bash
make lint   # flake8 on pypost/ only
```

Current failures (2026-06-12):

| File | Issue |
| --- | --- |
| `encryption_migration.py` | Unused variable `error_prefix` |
| `encryption_migration_worker.py` | Unused import `MigrationReport` |
| `mixins.py` | Trailing blank line at EOF |
| `request_editor.py` | Line too long (104 > 100) |

CI installs flake8 but **does not run** `make lint` today.

## SOLID Regression Caps

```bash
.venv/bin/python scripts/audit_baseline_metrics.py --check
pytest tests/test_solid_audit_baseline.py -v
```

| Module | LOC | Cap | Status |
| --- | ---: | ---: | --- |
| `main_window.py` | 383 | 300 | **FAIL** |
| `MainWindow` class | 343 | 260 | **FAIL** |
| `template_service.py` | 204 | 200 | **FAIL** |
| `tabs_presenter.py` | 715 | 785 | OK (9% headroom) |
| `metrics.py` | 161 | 165 | OK (2% headroom) |

See [solid_audit.md](solid_audit.md) for cap refresh procedure.

## Complexity Hotspots

| File / function | LOC | Notes |
| --- | ---: | --- |
| `tabs_presenter.py` | 715 | Tab/send/save orchestration |
| `encryption_migration.py` | 656 | Migration orchestration |
| `_rewrite_environments` | 225 | Single longest function |
| `metrics_registry._init_metrics` | 196 | Monolithic metric registration |
| `request_service._execute_http_with_retry` | 145 | HTTP retry loop |

`settings_dialog.py` improved from 423 to **188 LOC** via settings section widgets (PYPOST-374
follow-up).

## Error Handling

- **No bare `except:`** in `pypost/` — good
- **29 `except Exception`** — mostly storage, alerts, I/O; prefer typed catches +
  `logger.exception`
- **PYPOST-733** narrowed persistence-layer handlers in `storage.py` and `alert_manager.py`;
  one intentional last-resort `except Exception` remains in `deserialize_environment_records`
- User dialogs centralized in `collection_item_dialogs.py`

## PYPOST-40 Alignment

| Theme | Status |
| --- | --- |
| MainWindow decomposition | Done — but cap exceeded |
| Metrics / template injection | Resolved |
| RequestService injection | Partial — documented in [testability.md](testability.md) |
| Fold scanner duplication | Open — JSON/XML/YAML parallel `_scan_regions` |

## Follow-up Work

Prioritized remediation (2 P1, 7 P2, 4 P3) is listed in
[ai-tasks/PYPOST-687/60-tech-debt.md](../../ai-tasks/PYPOST-687/60-tech-debt.md). Jira tickets
are created by the sprint orchestrator.
