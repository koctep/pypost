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
| 1 | `tests/test_makefile.py::TestTargetExecution::test_test_succeeds_after_install` | 4.62 | 120 | 3.9% |
| 2 | `tests/test_makefile.py::TestTargetExecution::test_lint_succeeds_after_install` | 4.42 | 120 | 3.7% |
| 3 | `tests/test_makefile.py::TestTargetExecution::test_install_succeeds_with_empty_requirements` | 4.14 | 120 | 3.4% |
| 4 | `tests/test_request_service.py::TestRequestServiceRetryPolicyResolution::test_app_default_used_when_no_per_request_policy` | 3.10 | 60 | 5.2% |
| 5 | `tests/test_makefile.py::TestTargetExecution::test_test_fails_without_pytest_in_bare_venv` | 2.89 | 120 | 2.4% |
| 6 | `tests/test_makefile.py::TestDependencyChain::test_install_depends_on_venv_test` | 2.84 | 120 | 2.4% |
| 7 | `tests/test_makefile.py::TestMarkerLifecycle::test_venv_is_idempotent` | 2.71 | 120 | 2.3% |
| 8 | `tests/test_makefile.py::TestExitBehavior::test_lint_fails_without_flake8_in_bare_venv` | 2.61 | 120 | 2.2% |
| 9 | `tests/test_makefile.py::TestDependencyChain::test_venv_test_depends_on_marker` | 2.59 | 120 | 2.2% |
| 10 | `tests/test_makefile.py::TestMarkerLifecycle::test_venv_creates_version_marker` | 2.59 | 120 | 2.2% |
| 11 | `tests/test_makefile.py::TestMarkerLifecycle::test_clean_removes_venv_and_marker` | 2.58 | 120 | 2.2% |
| 12 | `tests/test_makefile.py::TestDependencyChain::test_runtime_targets_depend_on_marker_only[test]` | 2.52 | 120 | 2.1% |
| 13 | `tests/test_makefile.py::TestDependencyChain::test_runtime_targets_depend_on_marker_only[lint]` | 2.51 | 120 | 2.1% |
| 14 | `tests/test_makefile.py::TestDependencyChain::test_runtime_targets_depend_on_marker_only[run]` | 2.50 | 120 | 2.1% |
| 15 | `tests/test_request_service.py::TestRequestServiceRetryPolicyResolution::test_per_request_policy_wins_over_app_default` | 1.04 | 60 | 1.7% |

## Makefile tests (sandbox note)

An initial sandboxed run reported ~17s durations for `tests/test_makefile.py` targets because `make install` retried PyPI without network (9 failures). Re-run with normal network/socket access shows ~4.6s peaks and all green.

## Recommendations

- No immediate timeout tightening required for high-utilization offenders.
- Makefile integration tests dominate wall time (~2.5–4.6s) but sit at <4% of their 120s module timeout — generous but not masking hangs.
- `test_request_service` retry-policy cases (~1–3s) are well within 60s module timeout.
- Re-run this audit after adding integration/e2e tests or when CI duration grows; flag threshold remains >80% utilization per Jira acceptance.
