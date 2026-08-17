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

PyPost uses three intentional patterns for failure paths. Pick one based on whether the user
must act, whether the failure is user-initiated, and whether the code path is an optional
probe. Full naming rules for log lines are in [logging.md](logging.md).

### Layer rules

| Layer | Responsibility |
| --- | --- |
| `models/` | Raise typed errors (`ExecutionError`, `EnvironmentEncryptionError`, …); no logging |
| `core/` | Catch, log, return safe defaults or propagate; **never** show Qt dialogs |
| `core/qt/` | Workers emit failure signals; log on worker-side errors |
| `ui/` | Presenters choose log-only vs log+dialog; call `collection_item_dialogs` helpers |

**No bare `except:`** anywhere in `pypost/`. Prefer typed exceptions over `except Exception`;
when a last-resort catch is required (desktop resilience), use `logger.exception` and document
why (see `deserialize_environment_records` in `storage.py`).

### Pattern 1 — Log-only

**When:** Background or automatic work failed, but the app can continue with a safe default and
the user does not need a blocking modal.

**Do:**

- Log at `error` or `warning` with a stable event name and `key=value` context (see
  [logging.md](logging.md)).
- Apply a degraded but usable UI state (empty list, skip metric, status-bar hint).
- Do **not** open `QMessageBox`.

**Examples:**

| Module | Behavior |
| --- | --- |
| `EnvPresenter._on_storage_load_failed` | `storage_load_failed` log → empty environment list |
| `CollectionsAsyncLoader` | `collection_storage_async_load_failed` log → presenter handles empty state |
| `TabsPresenter._handle_copy_curl_request` | `copy_curl_failed` log → status bar message (non-modal) |
| `storage.py` corrupt file read | `logger.warning` → skip file, continue loading others |

Persistence file-level vs per-record behavior is documented in
[environment_encryption_at_rest.md](environment_encryption_at_rest.md).

### Pattern 2 — Log + dialog

**When:** The user initiated an action (save, rename, send, delete) and must know it failed, or
must confirm a destructive step.

**Do:**

1. Log the failure (`logger.error` with context, or `logger.exception` for unexpected errors).
2. Show a dialog via a helper in `pypost/ui/collection_item_dialogs.py` — do not call
   `QMessageBox` directly in presenters except for flows not yet migrated (tracked in tech debt).
3. Keep dialog **titles and bodies** in helpers or `environment_messages.py`; presenters pass
   domain facts only.

**Examples:**

| Module | Log event | Dialog helper |
| --- | --- | --- |
| `CollectionTreeActions` rename/delete | `collection_item_rename_failed`, … | `show_rename_failure`, `show_delete_failure` |
| `EnvPresenter._on_storage_save_failed` | `storage_save_failed` | `show_env_save_failed` |
| `TabsPresenterWorker._on_request_error` | `request_error` | `show_request_error`, `show_request_failed_error` |
| `McpControlsPresenter` MCP start | `mcp_server_start_failed_ui` | `show_mcp_server_start_failed` |

Helper catalog: [collection_tree_actions.md](collection_tree_actions.md#collection_item_dialogs).
Structured HTTP/MCP failures use `ExecutionError` / `ErrorCategory` from `models/errors.py` —
see [request_execution.md](request_execution.md).

**Cancelled requests** are not errors: log at `info` (`request_cancelled`) and return without a
dialog.

### Pattern 3 — Silent pass

**When:** Failure is expected on an optional probe, cleanup path, or parse fallback; surfacing
an error would be noise.

**Do:**

- Use a **narrow** exception type (`json.JSONDecodeError`, `ImportError`, `OSError` on close).
- Prefer `pass` or return `None` / default; optional `logger.debug` when diagnostics help.
- Add a one-line comment if the intent is non-obvious.

**Examples:**

| Module | Reason |
| --- | --- |
| `RequestService._execute_mcp` | Body may not be JSON; non-dict body falls through to `list_tools` |
| `AlertManager.close` | Handler `close()` may raise `OSError` during teardown |
| `key_sources/keyring.py` | Keyring unavailable or lookup failed → try next source |
| `bind_address_validation.py` | Optional address probe |

Do **not** use silent pass for persistence, encryption, or user data mutations — those belong in
log-only or log+dialog.

### Decision checklist

1. Did the user click something that should succeed or fail visibly? → **Log + dialog**
2. Is this background load/save/sync where a modal would interrupt workflow? → **Log-only**
   (+ safe default UI)
3. Is this probing optional input shape or tearing down resources? → **Silent pass**
   (typed catch, no user message)
4. Can you catch a **specific** exception instead of `Exception`? → Do so (R-P2-004)

### Inventory (2026-06-12 audit)

- **~29 `except Exception`** — mostly storage, alerts, I/O; narrowing tracked in
  [PYPOST-733](https://pypost.atlassian.net/browse/PYPOST-733) and R-P2-004
- **PYPOST-733** narrowed persistence handlers in `storage.py` and `alert_manager.py`; one
  intentional last-resort `except Exception` remains in `deserialize_environment_records`
- **~37 modules** log errors; **~20 QMessageBox** call sites centralized in
  `collection_item_dialogs.py` (PYPOST-539)

Convention documented in **PYPOST-739** (R-P3-003).

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
