# PYPOST-473: Architecture

## Current State

`EnvPresenter._is_valid_variable_name` wraps `validate_variable_name`, records Prometheus
metrics, and logs every attempt at DEBUG (valid and invalid).

## Decision

**Failure-only DEBUG logging** — remove the success-path DEBUG line; keep the existing
invalid-path log. No new configuration surface.

Rationale:

- Success volume is high relative to failures; metrics already count `result=valid`.
- Failure logs carry actionable `error=` context; success logs duplicated metric signal.
- A debug toggle adds settings/UI complexity without clear benefit over metrics.

## Change Surface

| Component | Change |
| --- | --- |
| `env_presenter.py` | Delete one `logger.debug` call on valid branch |
| `test_env_presenter.py` | Assert no DEBUG on valid; DEBUG on invalid |
| `doc/dev/variable_validation.md` | Update observability section |

## Unchanged

- `validate_variable_name` — pure, no I/O
- `track_variable_validation` / `track_variable_validation_failure` — same call sites
- INFO log on `variable_set_in_env` — unchanged
