# PYPOST-670: Observability

No new application metrics or log statements. CI gate behavior from PYPOST-572.

## Verifier stdout (`verify_test_log_guardrails.py`)

Prints to stdout:

- `ERROR count: N (max allowed: M)` — total vs baseline + margin.
- On count exceed: `FAIL: ERROR count N exceeds baseline + margin (M)`.
- On unlisted lines: `FAIL: K unlisted ERROR line(s):` plus per-line detail:
  `line L: [tag] logger: message snippet` (tag from `classify_group`).
- On success: `PASS: all ERROR lines match allowlist and count within margin`.

Exit code 1 when count exceeds max or any unlisted ERROR; 0 otherwise.

## CI failure signals

| Condition | Effect |
| --- | --- |
| Unlisted ERROR in capture | Test job fails at verifier step |
| ERROR count > 77 (72 + 5) | Test job fails at verifier step |
