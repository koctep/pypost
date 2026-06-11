# PYPOST-307: Observability

## Scope

Makefile automation tests are build/CI infrastructure. They do not run in the PyPost
application process and do not emit application logs or Prometheus metrics.

## Diagnostics

- Failed subprocess invocations surface through pytest assertion messages (`stderr` included
  on non-zero `make` exits).
- Timeouts are bounded by `pytestmark = pytest.mark.timeout(120)` and an internal
  `subprocess` timeout of 110 seconds per `make` call.

## Deferred

- Structured logging inside Make targets remains out of scope ([PYPOST-305](https://pypost.atlassian.net/browse/PYPOST-305)).
