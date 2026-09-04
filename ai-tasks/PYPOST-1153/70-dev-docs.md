# PYPOST-1153: Developer Documentation

## Documentation path

- `doc/dev/parallel_test_runner.md`

The existing guide was preserved and extended with the concise `PYPOST-1153 maintainability
contracts` section.

## Scope

The section documents the final maintainability behavior for the Make entry points, ordered
pytest argument replay, target discovery, worker and timeout validation, aggregate coverage, and
structured diagnostics. This correction changes documentation only.

## Contract summary

- `make test` and `make test-cov` fail closed when the runner is missing and clean only root
  `.coverage.*` fragments on the rejected path.
- Pytest argv is replayed losslessly, including the `--` sentinel and post-sentinel tokens.
  Node-id targets resolve their backing file for discovery while the full node id is replayed to
  pytest.
- Worker counts are positive. Per-file timeouts are positive finite values or explicit `none`;
  invalid values, missing targets, unmatched targets, and empty discovery fail before dispatch.
- Coverage collection is isolated per worker and decisions are aggregate-only. Source, report,
  and threshold precedence is documented for `--cov=SOURCE`, `--cov-report=SPEC`, and
  `--cov-fail-under=N`, with project settings and aggregate defaults used when omitted. Runner
  fragments are cleaned before and after aggregation.
- Lifecycle, timeout, and coverage diagnostics use scalar, redacted fields correlated by
  `run_id`; raw argv, node ids, test output, and environment contents are not logged.
- PYPOST-1261 and PYPOST-1262 remain existing, non-blocking baseline issues with no duplicate
  PYPOST-1153 tickets.

## Examples

```bash
make test WORKERS=2 WORKER_TIMEOUT=120 \
  PYTEST_ARGS='tests/test_parallel_runner_followups_repro.py -q'
make test-cov WORKERS=2 WORKER_TIMEOUT=120 \
  PYTEST_ARGS='tests/test_parallel_runner_followups_repro.py -q'
```

These examples provide explicit positive worker counts and bounded per-file timeouts while
keeping the target selection narrow.

## Validation evidence

- `make lint` — passed.
- `make verify-ai-tasks` — passed.
- Only `doc/dev/parallel_test_runner.md` and
  `ai-tasks/PYPOST-1153/70-dev-docs.md` were changed for this correction.
