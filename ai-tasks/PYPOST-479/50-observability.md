# PYPOST-479: Observability

## Policy Review

| Question | Answer | Evidence |
| --- | --- | --- |
| Should per-attempt DEBUG remain? | No | Removed in PYPOST-473 |
| Should logging be failure-only? | Yes | `EnvPresenter._is_valid_variable_name` |
| Should logging be configurable? | No | Metrics suffice for success path |
| Are metrics unchanged? | Yes | `track_variable_validation*` intact |

## Logging (current, from PYPOST-473)

| Event | Level | Emitted? |
| --- | --- | --- |
| Validation success | DEBUG | No |
| Validation failure | DEBUG | Yes (`variable_name_validation_attempt`) |
| Variable set success | INFO | Yes (unchanged) |

## Metrics (unchanged)

- `gui_variable_validation_total{result="valid|invalid"}`
- `gui_variable_validation_failures_total{reason="..."}`

## Conclusion

Observability policy is complete. This ticket adds no new instrumentation.
