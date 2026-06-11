# PYPOST-442: Architecture — max_retries non-negative validation

## Summary

Add a Pydantic field constraint on `RetryPolicy.max_retries` so invalid values are rejected
at model boundary. No changes to `RequestService`, worker, or settings UI.

## Design

### Single change point

| File | Change |
| ---- | ------ |
| `pypost/models/retry.py` | `max_retries: int = Field(default=0, ge=0)` |

`Field` is already imported in `retry.py` for `retryable_status_codes`. Reuse the same
pattern as other bounded fields in the codebase (Pydantic v2).

### Validation propagation

- **Direct construction:** `RetryPolicy(max_retries=-1)` → `ValidationError`.
- **Nested models:** `RequestData.retry_policy: Optional[RetryPolicy]` — Pydantic validates
  nested policy on `RequestData` construction.
- **Deserialization:** `RetryPolicy(**data)` / `RequestData(**data)` with negative
  `max_retries` → `ValidationError`.
- **Settings UI:** `QSpinBox.setRange(0, 10)` already prevents negative input; no UI change
  required.

### Retry loop (unchanged)

`RequestService._execute_http_with_retry` continues to use `range(max_retries + 1)`. With
`ge=0`, the defensive post-loop `retry_loop_invariant_failed` path should not be reachable
via invalid policy alone.

## Tests

| Test | Location | Asserts |
| ---- | -------- | ------- |
| `test_max_retries_rejects_negative` | `tests/test_retry.py` | AC-1 |
| `test_max_retries_accepts_zero` | `tests/test_retry.py` | AC-2 (zero) |
| `test_max_retries_accepts_positive` | `tests/test_retry.py` | AC-2 (positive) |
| `test_request_data_rejects_negative_max_retries` | `tests/test_retry.py` | AC-3 |

Extend existing `TestRetryPolicyModel` class; import `ValidationError` from `pydantic`.

## Files not modified

- `pypost/core/request_service.py` — no loop changes
- `pypost/ui/dialogs/settings_dialog.py` — spin-box already 0–10
- `pypost/models/models.py` — nested validation automatic

## Traceability

| Requirement | Implementation |
| ----------- | -------------- |
| FR-1, FR-4 | `Field(default=0, ge=0)` |
| FR-2 | Pydantic `ge=0` on field |
| FR-3 | Nested `RequestData.retry_policy` validation |
| AC-1–AC-4 | Unit tests in `TestRetryPolicyModel` |
