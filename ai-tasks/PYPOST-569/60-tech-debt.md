# Tech debt — PYPOST-569

## Blockers

None. Audit complete; no tests exceed 80% timeout utilization.

## Follow-ups (non-blocking)

| Item | Priority | Jira |
| --- | --- | --- |
| Optional CI job: `--durations=10 --durations-min=5` on verbose runs | Low | — | [PYPOST-667](https://pypost.atlassian.net/browse/PYPOST-667) |
| Monitor `test_makefile.py` (~4.6s peak); consider 45s marker after stable week | Low | — | [PYPOST-668](https://pypost.atlassian.net/browse/PYPOST-668) |
| Re-run `scripts/parse_timeout_audit.py` when adding e2e/integration tests | Low | — | [PYPOST-669](https://pypost.atlassian.net/browse/PYPOST-669) |
