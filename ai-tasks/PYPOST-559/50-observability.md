# PYPOST-559: Observability

## Assessment

Makefile install smoke is a CI/regression test with no production runtime path. No application
logging or metrics are required.

## CI visibility

- Main `test` job continues to write junit/coverage summaries (slow tests excluded).
- `make-install-smoke` job runs pytest with `-v --tb=short`; failures surface as a separate
  check in GitHub Actions.

## Local visibility

- `make test-slow` prints pytest verbose output for the slow install case.
- On failure, `_run_make` surfaces `make` stderr in the assertion message.
