# PYPOST-720: Raise coverage for metrics_server and script_executor

## Goals

Raise test coverage to ≥90% for `pypost/core/metrics_server.py` (was ~50%) and
`pypost/core/script_executor.py` (was ~40%) using fast, isolated unit tests.

## Definition of Done

- `metrics_server.py` coverage ≥ 90%.
- `script_executor.py` coverage ≥ 90%.
- Full test suite passes.

## Task Description

Both modules had insufficient coverage at the time of the audit. `script_executor.py`
had zero dedicated tests. `metrics_server.py` had integration tests but many lifecycle
branches (pending failure, generic exception, unexpected exit, restart) were untested.
