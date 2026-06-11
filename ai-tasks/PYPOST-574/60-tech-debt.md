# PYPOST-574: Technical Debt Analysis

## Implementation

- C1–C5 `caplog` contract in `.cursor/lsr/do-testing.md`
- Retrofit: `test_worker_wraps_unexpected_exception_logs_error` in `tests/test_worker.py`
- Cross-reference in `doc/dev/testing.md` § Error-path test logging

## Follow-up

Medium-risk tests in PYPOST-568 audit may receive caplog in future PRs; not blocking.

## Blocker Review

**Verdict: SAFE TO CLOSE**
