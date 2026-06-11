# CI guardrails proposal (PYPOST-571)

Proposal to prevent silent false positives after PYPOST-567/568/569/570 analysis.

## Problem statement

Green pytest runs can emit 72+ ERROR lines. Developers and CI log review cannot distinguish
expected error-path tests from regressions.

## Recommended approach (phased)

### Phase 1 — Post-run log gate (low effort, high value)

Add `scripts/check_test_log_noise.py`:

1. Run after `make test > tests.txt 2>&1` in CI.
2. Parse ERROR lines (reuse `parse_test_log_inventory.py`).
3. Match message prefixes against **allowlist** derived from PYPOST-567 inventory
   **expected** groups.
4. Fail if unknown ERROR count > 0 or total ERROR count exceeds baseline + margin (e.g. +5).

Allowlist file: `tests/fixtures/expected_test_error_prefixes.txt` (one prefix per line).

**Effort:** ~0.5 day. **Rejected alternative:** fail on any ERROR — too noisy without
allowlist migration period.

### Phase 2 — caplog contract on error-path tests (medium effort)

For tests in PYPOST-568 audit (worker, tabs_presenter):

```python
def test_worker_wraps_unexpected_exception(..., caplog):
    with caplog.at_level(logging.ERROR, logger="pypost.core.worker"):
        worker.run()
    assert len(received) == 1
    assert any("unexpected error" in r.message for r in caplog.records)
```

**Effort:** ~1 day. Ensures log emission is explicit assertion, not accidental side effect.

### Phase 3 — Duration budget warning (optional)

In CI verbose mode, flag tests where `duration > 0.8 * timeout_marker` (none today per
PYPOST-569). Informational only — no fail.

### Rejected options

| Option | Reason rejected |
| --- | --- |
| Strict `pytest-warnings` as errors | WARNING lines are often intentional product logs |
| Global `log_cli = false` | Hurts local debugging |
| pytest plugin fork | Maintenance burden vs scripts |

## Implementation follow-ups (create when implementing)

1. `scripts/check_test_log_noise.py` + allowlist file
2. Wire into Makefile `test-ci` target
3. caplog migration for 14 ERROR-path tests (PYPOST-568 list)

## Verdict

**SAFE TO CLOSE** — analysis-only deliverable; implementation is separate sprint work.
