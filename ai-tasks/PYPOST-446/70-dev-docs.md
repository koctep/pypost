# PYPOST-446 — Developer Documentation

> Team Lead: team_lead
> Date: 2026-05-04
> Sprint: 168

---

## 1. What Changed and Why

Before this ticket, hidden-variable values (secrets, tokens, passwords marked as `hidden` in
the Environment editor) were written to request history in plain text. The rendered URL,
headers, and body were stored as-is before any masking was applied, creating a risk of secret
leakage in the persisted `history.json` file and in debug/operational logs.

PYPOST-446 adds a `SensitiveDataMaskingPolicy` that intercepts request data before any
history entry is created, replaces values derived from hidden keys with `***`, and ensures
that `HistoryManager` only ever receives sanitized content.

---

## 2. New Module: `SensitiveDataMaskingPolicy`

`pypost/core/sensitive_data_masking_policy.py`

```python
policy = SensitiveDataMaskingPolicy(template_service)
masked = policy.build_history_safe_fields(
    request=request_data,
    variables=variables,
    hidden_keys={"api_key", "token"},
)
# masked.url, masked.headers, masked.body — safe to persist
```

**Masking rule**: a copy of the variables map is made; each hidden key's value is replaced
with `***` before Jinja2 rendering. The secret never appears in the rendered output.

The frozen `MaskedRequestData` dataclass is returned. It holds the three sanitized fields and
nothing else — no execution metadata, no reference to the original `RequestData`.

---

## 3. Integration in `RequestService`

`RequestService` now always owns a `_masking_policy`. When no `TemplateService` is injected
it creates a fallback `TemplateService()` internally (used only for masking/history — the
public `_template_service` attribute remains `None`).

History recording now unconditionally calls `build_history_safe_fields` instead of calling
`_template_service.render_string` directly. The previous `else` branch that stored raw
templates is removed.

---

## 4. Propagation Chain

```
TabsPresenter._current_hidden_keys
  → RequestWorker(hidden_keys=...)
    → RequestService.execute(hidden_keys=...)
      → SensitiveDataMaskingPolicy.build_history_safe_fields(hidden_keys=...)
        → HistoryEntry (url / headers / body are guaranteed-safe)
          → HistoryManager.append → history.json
```

`TabsPresenter` already held `_current_hidden_keys`; this ticket wires it through to
`RequestWorker` (new `hidden_keys` parameter) and on to `RequestService.execute`.

---

## 5. Metrics

| Metric | Labels | Meaning |
|---|---|---|
| `hidden_value_masks_applied_total` | `surface` | Incremented when `hidden_key_count > 0` at history write time |

`surface="history"` is the only value used today. The label is kept for future surfaces
(e.g. log output, export).

---

## 6. File Locations

| File | Role |
|------|------|
| `pypost/core/sensitive_data_masking_policy.py` | Policy implementation |
| `pypost/core/request_service.py` | Integration point; `execute()` and `__init__` |
| `pypost/core/worker.py` | `hidden_keys` parameter added |
| `pypost/ui/presenters/tabs_presenter.py` | Passes `_current_hidden_keys` to worker |
| `pypost/core/metrics.py` | `track_hidden_value_mask_applied` counter |
| `tests/test_sensitive_data_masking_policy.py` | Policy unit tests |
| `tests/test_request_service.py` | History masking integration tests |
| `tests/test_history_masking_e2e.py` | End-to-end execute → persist → reload → HistoryPanel (PYPOST-462) |
| `tests/test_history_masking_metrics.py` | Prometheus scrape tests for masking metric counter (PYPOST-464) |
| `tests/test_worker.py` | `hidden_keys` forwarding tests |
| `tests/test_tabs_presenter.py` | Presenter wiring tests |
| `doc/dev/sensitive_data_masking_policy.md` | Long-form dev reference |

---

## 7. Testing

Unit and service-level integration:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_sensitive_data_masking_policy.py \
  tests/test_request_service.py -v
```

Key test cases in `TestRequestServiceHistory`:

- `test_history_masks_hidden_variable_values` — hidden key value replaced with `***`
- `test_history_masking_metric_recorded_when_hidden_keys_present` — metric counter fires
- `test_history_stores_raw_template_when_no_template_service` — URL rendered even without
  injected `TemplateService`
- `test_history_records_resolved_url` — non-hidden variables still render normally

End-to-end acceptance (PYPOST-462):

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest \
  tests/test_history_masking_e2e.py -v
```

Metric counter scrape tests (PYPOST-464):

```bash
.venv/bin/python -m pytest tests/test_history_masking_metrics.py -v
```

`test_hidden_values_stay_masked_after_history_reload_in_panel` verifies execute → persist →
reload → HistoryPanel display; see `doc/dev/sensitive_data_masking_policy.md` for scope detail.

PYPOST-464 tests scrape a real `MetricsManager` registry and assert
`hidden_value_masks_applied_total` is absent for empty/`None` `hidden_keys` and equals `1.0`
when hidden keys are present.

---

## 8. Related Tickets

| Ticket | Description |
|--------|-------------|
| PYPOST-437 | Introduced `hidden_keys` on `Environment`; display-level masking |
| PYPOST-462 | End-to-end integration test for mask → persist → reload → display cycle (done) |
| PYPOST-463 | Follow-up: refactor history-recording block in `RequestService.execute` |
| PYPOST-464 | Explicit metric scrape tests for empty vs non-empty `hidden_keys` (done) |
