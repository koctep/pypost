# PYPOST-1179: Observability

## Baseline-refresh diagnostics

The observable contract for this task is the diagnostic stream produced by
`make typecheck` through `scripts/check_mypy_baseline.py`. Diagnostics are
normalized to `(path, code, message)` keys and compared as a multiset against
`mypy-baseline.json`; source line numbers are display-only. The refresh is
scoped to the `SettingsDialog` paths. Diagnostics from other
paths remain separately visible and are not absorbed into this task.

The completed refresh removes four resolved `SettingsDialog` baseline records
from the accepted baseline. The
deterministic repro in
`tests/test_pypost_1179_mypy_baseline_repro.py` verifies that stale and new
named-path records are reported before refresh, that the scoped diff is empty
after refresh, and that an unrelated model diagnostic remains separately
reported.

## Runtime telemetry applicability

Runtime logging, metrics, and tracing are not applicable. This issue changes
only static typing contracts and the accepted mypy diagnostic baseline; it
does not add a runtime execution path, request handling, or production state
whose health can be meaningfully measured by application telemetry. The
diagnostic output and baseline comparison are the appropriate observability
surface.

## Verification contract

The following Make targets are required and were run for this step:

- `make lint` — static and documentation quality checks pass.
- `make typecheck` — the baseline checker passes with **185 known errors** in
  the checked `pypost/core`, `pypost/models`, and `pypost/ui` scope.
- `make test PYTEST_ARGS='tests/test_pypost_1179_mypy_baseline_repro.py -q' WORKERS=1` —
  deterministic baseline reconciliation controls pass.
- `make verify-ai-tasks` — task artifact integrity checks pass.

No large runtime data structures are logged, and no production telemetry
configuration is changed.
