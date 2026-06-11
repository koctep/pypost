# PYPOST-417 — Observability

## Assessment

No new logs or metrics required. Existing `worker_stop_requested` and `worker_run_completed
stopped=` debug logs already correlate stop requests with completion.

## Documentation as observability

The class docstring and dev docs make the permanent stop flag discoverable during code review
and onboarding, reducing silent misuse risk.
