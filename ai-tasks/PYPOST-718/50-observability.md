# PYPOST-718: Observability

## Scope

Test-only task. No new logging or metrics in production code.

## Existing Observability Under Test

None. This task only modifies the integration test suite to correctly propagate the active
Python interpreter to `make` commands. No production code or observability signals are
affected.

## Notes

The changes ensure that integration tests reliably run against the correct Python version,
preventing false-positive test failures caused by mismatching system default python3 versions.
