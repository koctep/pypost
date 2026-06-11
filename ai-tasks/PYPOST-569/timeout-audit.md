# Timeout budget audit (PYPOST-569)

Baseline capture:

```bash
QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest tests/ \
  --durations=30 --durations-min=10 -q 2>&1 | tee ai-tasks/PYPOST-569/durations.txt
```

Supplementary full-duration capture (`--durations=0 --durations-min=1`) lives in
`durations-full.txt` for sub-10s analysis.

## Summary

- Tests with duration ≥ 10s: **0**
- Tests with utilization ≥ 80% of declared timeout: **0**
- Suite outcome (full capture): **937 passed**, 39 subtests passed, ~48s total

## High-utilization tests (≥ 80% of timeout marker)

_No passing tests consumed ≥ 80% of their declared timeout budget._

## Slowest passing tests (top 20)

| Rank | Test | Duration (s) | Timeout (s) | Utilization |
| ---: | --- | ---: | ---: | ---: |

## Makefile tests (sandbox note)

An initial sandboxed run reported ~17s durations for `tests/test_makefile.py` targets because `make install` retried PyPI without network (9 failures). Re-run with normal network/socket access shows ~4.6s peaks and all green.

## Recommendations

- No immediate timeout tightening required for high-utilization offenders.
- Makefile integration tests dominate wall time (~2.5–4.6s) but sit at <4% of their 120s module timeout — generous but not masking hangs.
- `test_request_service` retry-policy cases (~1–3s) are well within 60s module timeout.
- Re-run this audit after adding integration/e2e tests or when CI duration grows; flag threshold remains >80% utilization per Jira acceptance.
