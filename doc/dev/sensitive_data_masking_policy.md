# Sensitive Data Masking Policy (PYPOST-446)

## Overview

PYPOST-446 introduces a masking policy that ensures hidden-variable values are sanitized before
being written to request history and operational logs. Values derived from hidden environment
variables are replaced with `***` at history-write time so that secrets never enter persisted
storage.

## Architecture

- **Canonical type**: `pypost.core.request_fields.RequestFields` — frozen dataclass with
  `url`, `headers`, and `body`. Semantic aliases: `ResolvedRequestFields` (transport) and
  `MaskedRequestData` (history-safe output); all names refer to the same class (PYPOST-802).
- **Model**: `pypost.core.sensitive_data_masking_policy.SensitiveDataMaskingPolicy`
  - Accepts a `TemplateService`, a `RequestData`, the active variables mapping, and the hidden
    key set.
  - Renders URL, headers, and body; replaces values for hidden keys with `***` before rendering.
  - Returns a frozen `MaskedRequestData` instance with sanitized fields.
- **RequestService**: `pypost.core.request_service.RequestService`
  - Always owns a `_masking_policy` (created with an injected or fallback `TemplateService`).
  - Applies policy in the history-recording block before constructing `HistoryEntry`.
  - Emits `hidden_value_masks_applied_total` metric when any hidden keys are present.
- **Worker**: `pypost.core.qt.worker.RequestWorker`
  - Accepts `hidden_keys: set[str] | None` and forwards it to `RequestService.execute`.
- **TabsPresenter**: `pypost.ui.presenters.tabs_presenter.TabsPresenter`
  - Passes `self._current_hidden_keys` when creating `RequestWorker`.
- **Metrics**: `pypost.core.qt.metrics.MetricsManager`
  - `hidden_value_masks_applied_total` counter with `surface` label tracks where masking occurs.

## Data Flow

```
TabsPresenter (hidden_keys)
  → RequestWorker (hidden_keys)
    → RequestService.execute (hidden_keys)
      → SensitiveDataMaskingPolicy.build_history_safe_fields
        → HistoryEntry (sanitized url / headers / body)
          → HistoryManager (persisted)
```

## Masking Rules

- A copy of the variables map is made; each hidden key's value is replaced with `***`.
- Rendering happens on the masked copy, so the secret never appears in the rendered output.
- **Heuristic pass (PYPOST-706):** After rendering, URL/body text and all headers are sanitized:
  - Sensitive header names (`Authorization`, `Cookie`, `X-Api-Key`, …) → `***`
  - `Bearer …` tokens, `?token=` / `&api_key=` query params
  - JSON body fields matching credential-like key names
- Shared implementation: `pypost.core.sensitive_text_sanitizer` (also used by MCP responses).

## Invariants

- `RequestService._template_service` remains `None` when no `TemplateService` is injected
  (no silent fallback on the public attribute).
- `RequestService._masking_policy` is always set; it uses a fallback `TemplateService()` when
  none is injected, so URL/headers/body are always rendered before history storage.
- Masking is applied at write time. `HistoryManager` and `HistoryPanel` consume already-safe
  values and contain no masking logic.

## Metrics

| Metric | Labels | Description |
|---|---|---|
| `hidden_value_masks_applied_total` | `surface` | Incremented when hidden keys are present during history write |

## Testing

### Unit and integration tests

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_sensitive_data_masking_policy.py \
  tests/test_request_service.py \
  tests/test_worker.py \
  tests/test_tabs_presenter.py -v
```

Key cases in `TestRequestServiceHistory`:

- `test_history_masks_hidden_variable_values` — hidden key value replaced with `***`
- `test_history_masking_metric_recorded_when_hidden_keys_present` — metric counter fires
- `test_history_stores_raw_template_when_no_template_service` — URL rendered even without
  injected `TemplateService`
- `test_history_records_resolved_url` — non-hidden variables still render normally

### End-to-end acceptance test (PYPOST-462)

`tests/test_history_masking_e2e.py` covers the connected flow that unit tests split across
components: execute request with hidden and non-hidden variables → persist history → reload
from disk (simulated restart) → display entry in `HistoryPanel`.

The test asserts:

- Persisted `HistoryEntry` URL, headers, and body contain `***` for hidden-derived values.
- Non-hidden variable values remain visible after reload.
- History panel list label and detail widgets (URL, headers, body) never contain the secret
  and show the same masked content as persisted storage.

Run the acceptance check alone:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_history_masking_e2e.py -v
```

### Metric counter tests (PYPOST-464)

`tests/test_history_masking_metrics.py` scrapes a real `MetricsManager` registry after
`RequestService.execute` and asserts `hidden_value_masks_applied_total` behavior:

- Counter line is **absent** when `hidden_keys` is empty (`set()`) or `None`.
- Counter equals **`1.0`** for `surface="history"` when `hidden_keys` is non-empty.

Run the metric tests alone:

```bash
.venv/bin/python -m pytest tests/test_history_masking_metrics.py -v
```

Broader history-masking regression:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_sensitive_data_masking_policy.py \
  tests/test_request_service.py \
  tests/test_history_masking_metrics.py \
  tests/test_history_masking_e2e.py -v
```
