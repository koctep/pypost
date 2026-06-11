# PYPOST-310: Observability

## Logging and metrics

No production logging or metrics changes. Makefile test failures surface through pytest output
and CI `make test` exit codes — same observability path as PYPOST-307.

## Diagnostics

When execution tests fail, subprocess `stderr` is included in assertion messages via
`_run_make` result objects.
