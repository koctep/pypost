# PYPOST-749 — Observability

## Impact

**Documentation only.** No new log lines, metrics, or alert behavior.

## Deliverable

Reciprocal cross-links connect:

- Observability audit Test and CI Logging table (local vs CI `log_cli`, guardrail baseline)
- Testing doc pytest live logging section (PYPOST-570 policy, overrides, inventory commands)

## Verification

`make check` — no test changes; docs do not affect runtime observability.
