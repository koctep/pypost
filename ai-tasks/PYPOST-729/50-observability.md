# PYPOST-729: Observability

## Changes

No runtime behaviour changed. All four fixes are static analysis / style corrections:

- No new log statements needed.
- No new metrics needed.
- `make lint` exit code is now 0 — this is the observable outcome.

## CI Impact

`make lint` can now be added to the CI pipeline without causing false failures (see
PYPOST-736 which tracks actually wiring lint into CI).
