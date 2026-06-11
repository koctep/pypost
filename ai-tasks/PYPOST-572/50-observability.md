# PYPOST-572: Observability

No new application metrics or log statements.

## CI gate output

`verify_test_log_guardrails.py` prints to stdout:

- Total ERROR count vs max allowed (baseline + margin).
- List of unlisted ERROR lines with logger, message snippet, and PYPOST-567-style tag from
  `classify_group`.
- `PASS` or `FAIL` summary line.

## Failure signals

| Condition | CI effect |
| --- | --- |
| Unlisted ERROR during test run | Test job fails at verifier step |
| ERROR count > 77 | Test job fails at verifier step |
