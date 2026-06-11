# PYPOST-464: Masking metric counter tests (empty vs non-empty hidden_keys)

## Research

### Production metric wiring (PYPOST-446)

| Component | Responsibility |
| --- | --- |
| `MetricsManager` | Defines `hidden_value_masks_applied_total` with `surface` label |
| `RequestService.execute` | Computes `hidden_key_count = len(hidden_keys or set())`; calls `track_hidden_value_mask_applied("history")` only when count > 0 |
| `MetricsManager.track_hidden_value_mask_applied` | Increments labeled counter in the manager's private registry |

Relevant code path in `pypost/core/request_service.py`:

```python
hidden_key_count = len(hidden_keys or set())
# ... build masked history fields ...
if self._metrics and hidden_key_count > 0:
    self._metrics.track_hidden_value_mask_applied("history")
```

### Existing test coverage (gaps)

| File | What it covers | Gap |
| --- | --- | --- |
| `tests/test_request_service.py` | Mock asserts on `track_hidden_value_mask_applied` | No real Prometheus registry scrape |
| `tests/test_storage_environments.py` | `_scrape_metrics` + `generate_latest` pattern | Different domain (environment encryption metrics) |
| `tests/test_history_masking_e2e.py` | Execute → persist → reload → UI | Does not assert metrics |

PYPOST-464 adds scrape-based counter tests without duplicating the e2e persistence journey.

## Design

### New test module: `tests/test_history_masking_metrics.py`

```
MetricsManager (fresh per test)
  → RequestService(metrics=..., history_manager=MagicMock, template_service=TemplateService)
    → http_client mocked
    → execute(..., hidden_keys=<case>)
      → scrape registry via generate_latest
        → assert metric line absent (empty/None) or equals 1.0 (non-empty)
```

### Test cases

| Test | `hidden_keys` | Expected scrape |
| --- | --- | --- |
| `test_hidden_mask_metric_not_incremented_when_hidden_keys_empty` | `set()` | No `hidden_value_masks_applied_total{surface="history"}` line |
| `test_hidden_mask_metric_not_incremented_when_hidden_keys_none` | `None` | Same absence |
| `test_hidden_mask_metric_incremented_when_hidden_keys_present` | `{HIDDEN_KEY}` | Line with value `1.0` |

### Patterns reused

- `_scrape_metrics`: `generate_latest(metrics.registry).decode("utf-8")` from
  `tests/test_storage_environments.py`.
- Execute setup: mocked HTTP + `TemplateService` from `tests/test_history_masking_e2e.py` and
  `TestRequestServiceHistory`.

### Out of scope

- No production code changes.
- No shared test utility extraction (helpers stay module-local per repo convention).

## Risks

- **Counter isolation:** each test constructs a fresh `MetricsManager` to avoid cross-test registry
  pollution.
- **Zero-value counters:** Prometheus omits un-incremented counters from scrape output; negative
  tests assert absence, not `0.0`.

## Validation plan

```bash
.venv/bin/python -m pytest tests/test_history_masking_metrics.py -v
flake8 --jobs=1 --max-line-length=100 tests/test_history_masking_metrics.py
./scripts/check-line-length.sh tests/test_history_masking_metrics.py
```
