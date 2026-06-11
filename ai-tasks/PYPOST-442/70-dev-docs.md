# PYPOST-442 — Developer Documentation

> Date: 2026-06-11
> Parent: [PYPOST-442](https://pypost.atlassian.net/browse/PYPOST-442)

---

## 1. What Changed and Why

`RetryPolicy.max_retries` previously accepted any integer, including negatives. A negative
value made `range(max_retries + 1)` empty in `RequestService._execute_http_with_retry`,
leading to the defensive `retry_loop_invariant_failed` error path documented in
[PYPOST-421](https://pypost.atlassian.net/browse/PYPOST-421).

PYPOST-442 adds Pydantic validation so invalid retry counts fail at model construction.

---

## 2. Model Constraint

`pypost/models/retry.py`:

```python
class RetryPolicy(BaseModel):
    max_retries: int = Field(default=0, ge=0)
    ...
```

- **`ge=0`:** `max_retries` must be zero or positive.
- **Default `0`:** unchanged sentinel for "no retries".
- **Settings UI:** `SettingsDialog` spin-box remains `0–10`; this constraint hardens
  programmatic and deserialized paths.

---

## 3. Validation Behavior

| Input | Result |
| ----- | ------ |
| `RetryPolicy(max_retries=0)` | OK |
| `RetryPolicy(max_retries=3)` | OK |
| `RetryPolicy(max_retries=-1)` | `pydantic.ValidationError` |
| `RequestData(..., retry_policy=RetryPolicy(max_retries=-1))` | `ValidationError` (nested) |

---

## 4. Tests

`tests/test_retry.py` — class `TestRetryPolicyModel`:

- `test_max_retries_rejects_negative`
- `test_max_retries_accepts_zero`
- `test_max_retries_accepts_positive`
- `test_request_data_rejects_negative_max_retries`

Run:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/test_retry.py::TestRetryPolicyModel -q
```

---

## 5. Troubleshooting

- **`ValidationError` on load for saved request/config:** Check `retry_policy.max_retries`
  in persisted JSON; must be `>= 0`. Correct the file or re-save from Settings (UI enforces
  non-negative values).
- **Unexpected `retry_loop_invariant_failed`:** Should not occur from negative
  `max_retries` after this change. If seen, investigate whether policy was constructed
  without going through Pydantic validation (bypass / manual dict mutation).

---

## 6. Related

- [PYPOST-421](https://pypost.atlassian.net/browse/PYPOST-421) — defensive retry loop path
- [PYPOST-423](https://pypost.atlassian.net/browse/PYPOST-423) — retryable status codes
  validation (same module)
