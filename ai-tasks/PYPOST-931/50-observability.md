# PYPOST-931: Observability

## Runtime observability

No new Prometheus / OTel metrics. Operator-facing visibility is **CLI output**
from `scripts/refresh_ci_duration_evidence.py` and Makefile targets.

## Maintainer signals

| Signal | Where |
| --- | --- |
| Fresh evidence table | stdout from `make refresh-ci-duration-evidence` |
| Doc procedure drift | `make check-ci-duration-evidence` (exit 1 + stderr) |
| Wiring regression | `tests/test_refresh_ci_duration_evidence.py` |

## Logging

Script uses stderr only on `--check` failures and GitHub API errors. Successful
fetch prints markdown to stdout for paste workflow.

## Verification

- [x] `--check` prints OK when procedure documented
- [x] Unit tests cover format/extract without live network
