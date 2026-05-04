# Sensitive Data Masking Policy (PYPOST-446)

## Overview

PYPOST-446 introduces a masking policy that ensures hidden-variable values are sanitized before
being written to request history and operational logs. Values derived from hidden environment
variables are replaced with `***` at history-write time so that secrets never enter persisted
storage.

## Architecture

- **Model**: `pypost.core.sensitive_data_masking_policy.SensitiveDataMaskingPolicy`
  - Accepts a `TemplateService`, a `RequestData`, the active variables mapping, and the hidden
    key set.
  - Renders URL, headers, and body; replaces values for hidden keys with `***` before rendering.
  - Returns a frozen `MaskedRequestData` dataclass with sanitized fields.
- **RequestService**: `pypost.core.request_service.RequestService`
  - Always owns a `_masking_policy` (created with an injected or fallback `TemplateService`).
  - Applies policy in the history-recording block before constructing `HistoryEntry`.
  - Emits `hidden_value_masks_applied_total` metric when any hidden keys are present.
- **Worker**: `pypost.core.worker.RequestWorker`
  - Accepts `hidden_keys: set[str] | None` and forwards it to `RequestService.execute`.
- **TabsPresenter**: `pypost.ui.presenters.tabs_presenter.TabsPresenter`
  - Passes `self._current_hidden_keys` when creating `RequestWorker`.
- **Metrics**: `pypost.core.metrics.MetricsManager`
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
- Keys not present in the active variables are left unchanged (no-op, no error).
- The `***` placeholder is a module-level constant (`HIDDEN_PLACEHOLDER`) in
  `sensitive_data_masking_policy.py`.

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
