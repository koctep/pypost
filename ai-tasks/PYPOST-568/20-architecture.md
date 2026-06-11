# PYPOST-568: Architecture

## Approach

Offline audit: join PYPOST-567 `inventory.csv` ERROR rows (focus modules) with test source
and production log call sites. No new scripts — manual classification with reproducible
criteria documented in the audit report.

## Data flow

```
inventory.csv (ERROR rows)
        │
        ▼
Filter by test file (4 modules)
        │
        ▼
Read test + production logger call
        │
        ▼
error-path-test-audit.md (risk, assertions, mitigation)
```

## Production log sites (focus modules)

| Logger | Message prefix | Source module |
| --- | --- | --- |
| `pypost.core.worker` | `RequestWorker unexpected error` | `pypost/core/worker.py` |
| `pypost.ui.presenters.tabs_presenter` | `request_error` | `pypost/ui/presenters/tabs_presenter.py` |
| `pypost.ui.presenters.collection_tree_actions` | `collection_item_delete_failed` | `pypost/ui/presenters/collection_tree_actions.py` |
| `pypost.core.request_service` | `request_execution_failed` | `pypost/core/request_service.py` |

## Classification criteria

| Risk | Criteria |
| --- | --- |
| **Low** | Test clearly simulates failure path; asserts outcome (signal, metric, dialog, error fields). |
| **Medium** | Intentional failure path; assertions omit log emission; ERROR indistinguishable from regression in raw log. |
| **High** | Weak or missing behavioral assertions; ERROR could mask missing coverage. |

| Assertion strength | Criteria |
| --- | --- |
| **Strong** | Multiple concrete assertions on the failure outcome (category, metrics, mock calls, model state). |
| **Moderate** | Single behavioral assertion or partial field checks. |
| **Weak** | Test passes on log side effect alone or only checks no exception raised. |

## Outputs for downstream tasks

- PYPOST-571: allowlist candidates — all 22 rows rated **low**; tag logger + test node id.
- Optional caplog follow-ups: medium-risk rows if log assertion added later.
