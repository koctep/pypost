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
| `make lint` | **PASS** (flake8 clean) |
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

Historical failures (2026-06-12 audit) — **all remediated in PYPOST-729**:

| File | Issue | Status |
| --- | --- | --- |
| `encryption_migration.py` | Unused variable `error_prefix` (F841) | **Done** — [PYPOST-737](https://pypost.atlassian.net/browse/PYPOST-737) |
| `qt/encryption_migration_worker.py` | Unused import `MigrationReport` (F401) | **Done** — [PYPOST-737](https://pypost.atlassian.net/browse/PYPOST-737) |
| `mixins.py` | Trailing blank line at EOF (W391) | **Done** — [PYPOST-729](https://pypost.atlassian.net/browse/PYPOST-729) |
| `request_editor.py` | Line too long (E501) | **Done** — [PYPOST-729](https://pypost.atlassian.net/browse/PYPOST-729) |

CI installs flake8; wiring `make lint` into the workflow is tracked in
[PYPOST-736](https://pypost.atlassian.net/browse/PYPOST-736).

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
| `request_service._execute_http_with_retry` | 145 | HTTP retry loop |

`metrics_registry._init_metrics` was split into domain helpers (`_init_gui_metrics`,
`_init_http_metrics`, `_init_mcp_metrics`, `_init_encryption_metrics`) in PYPOST-746.

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

## Related Audits

Sibling Code Audit summaries — hub:
[documentation_audit.md § Code Audit Hub](documentation_audit.md#code-audit-hub).

- [Architecture and Package Boundary Audit (PYPOST-684)](architecture_audit.md)
- [Security and Secrets Handling Audit (PYPOST-685)](security_audit.md)
- [Test Coverage and Quality Audit (PYPOST-686)](test_audit.md)
- [Observability and Logging Audit (PYPOST-688)](observability_audit.md)
- [Performance and Scalability Audit (PYPOST-689)](performance_audit.md)
- [Documentation and ADR Alignment Audit (PYPOST-690)](documentation_audit.md)
- [Dependencies and Supply Chain Audit (PYPOST-691)](dependencies_audit.md)
