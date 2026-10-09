# PYPOST-1264: Observability Implementation

## Logging Implementation

### Scope and Gap Analysis

The teardown lifecycle is in `pypost/ui/presenters/collection_import_actions.py`
(`teardown`, `_wait_idle_until`, `_on_worker_finished`) and
`pypost/ui/presenters/collections_presenter.py` (`teardown`). Logger:
`pypost.ui.presenters.collection_import_actions`. All event names are unchanged.

Logs that existed before this step, and what they told an operator:

| Level | Event (fields) | Diagnostic value |
| --- | --- | --- |
| INFO | `collections_presenter_teardown_started timeout_ms=` | Resolved budget (Step 4 logs the resolved value, not `None`) |
| INFO | `collections_presenter_teardown_completed clean=` | Presenter outcome |
| INFO | `collection_import_teardown_started timeout_ms=` | Resolved budget of the shared deadline |
| WARNING | `collection_import_worker_interrupting` | P0/P2 cooperative interruption requested |
| INFO | `collection_import_wait_idle_started` | P1 entered |
| WARNING | `collection_import_wait_idle_timeout elapsed_ms=` | P1 used the budget; elapsed since deadline start |
| INFO | `collection_import_wait_idle_completed elapsed_ms=` | P1 finished in time |
| WARNING | `collection_import_worker_interrupt_timeout` | P2 final join timed out (**no fields**) |
| INFO | `collection_import_worker_interrupted` | P2 worker stopped |
| DEBUG | `collection_import_worker_reaped` | File worker released |
| WARNING | `collection_library_import_worker_timeout` | P3 library join timed out (**no fields**) |
| INFO | `collection_import_teardown_completed clean=` | Final outcome (**no duration**) |
| WARNING | `collection_import_worker_finish_wait_timeout wait_ms=` | Post-`finished` join (not on the deadline) |

Gaps caused by the new shared deadline:

1. **Which phase used the budget.** P2 now waits `min(final_join_ms, remaining)` and P3 waits
   `remaining`. Both can be `0` (a probe) when P1 used the whole budget. Before this step, a
   P2/P3 timeout line looked the same whether the worker got 100 ms, 4000 ms, or no time at all.
   An operator could not tell "this worker is stuck" from "an earlier phase used the budget".
2. **Whether teardown stayed within the budget.** No line gave the total teardown duration.
   `wait_idle_*` `elapsed_ms` only covers P1. The DoD 3 contract (wall time about
   `budget + 50 ms`) could not be checked from production logs.

### Added Logs

Fields were only appended. Event names and levels are unchanged. All new values are scalar
integers taken from the `ImportTeardownDeadline` that the phases already share. `elapsed_ms`
is counted from the start of teardown.

- **WARNING**: `collection_import_actions.py` `teardown` P2 —
  `collection_import_worker_interrupt_timeout wait_ms=%d elapsed_ms=%d`. `wait_ms` is the
  join bound P2 actually got (`0` means the budget was already used up).
- **WARNING**: `collection_import_actions.py` `teardown` P3 —
  `collection_library_import_worker_timeout wait_ms=%d elapsed_ms=%d`. `wait_ms` is the
  remaining budget given to the library join.
- **INFO**: `collection_import_actions.py` `teardown` P4 —
  `collection_import_teardown_completed clean=%s elapsed_ms=%d timeout_ms=%d`. This gives the
  total teardown duration next to the budget in one line, so an overrun past
  `timeout_ms + budget_tolerance_ms` can be seen without matching it to the started line.
- **EMERG / ALERT / CRIT / ERR / NOTICE / DEBUG**: none added. A teardown timeout is a
  recoverable degraded outcome (the worker is released or abandoned cooperatively), so
  WARNING is the right level. It was already used and is kept.

Considered and not added:

- `remaining_ms`: it equals `timeout_ms - elapsed_ms`, so it adds nothing.
- `budget_ms` as a new field name: the budget is already logged as `timeout_ms` on the started
  line. The completed line uses the same name to stay consistent.
- Fields on `collection_import_worker_finish_wait_timeout`: this join is not on the deadline
  (Risk 3), and it already logs `wait_ms`.
- Presenter lines: they already log the resolved budget and the outcome. Duration is on the
  actions completed line.

### Log Structure

- Structured logs: yes (`event key=value` scalars, `%`-style lazy formatting)
- Includes context: yes (phase wait bound, elapsed since deadline start, budget, outcome)
- Log levels: DEBUG, INFO, WARNING (unchanged per event)
- No collection content, paths, or other large structures are logged by these events.

## Metrics Implementation (if applicable)

### Performance Metrics

- **Response time**: no new metric. Teardown duration is logged as `elapsed_ms` on
  `collection_import_teardown_completed`. Teardown runs once per window or presenter shutdown,
  so a log field is enough and a metrics series is not needed.
- **Throughput**: N/A
- **Error rate**: N/A. Unclean teardowns are visible as `clean=False` plus WARNING lines.

### Business Metrics

- None. The existing import `track_*` metrics are unaffected.

### System Health Metrics

- **Resource usage**: N/A
- **Component status**: teardown cleanliness (`clean=`) on the existing completed lines.

## Monitoring Integration

- [ ] Prometheus metrics (not used by this desktop app)
- [ ] Grafana dashboards (N/A)
- [ ] Alerting rules (N/A)
- [ ] Log aggregation (ELK, Loki, etc.) (N/A; the `key=value` format can be grepped or parsed)

## Validation Results

- [x] Logs are correctly formatted: new caplog tests in
  `tests/test_collection_import_teardown_policy.py` check exact messages with an injected fake
  clock and policy (explicit `pytest.mark.timeout(30)` on the module):
  - `test_teardown_timeout_logs_report_phase_waits_and_elapsed`: budget 200 and final join 30
    → `..._interrupt_timeout wait_ms=30 elapsed_ms=30`,
    `..._library_import_worker_timeout wait_ms=170 elapsed_ms=200`,
    `..._teardown_completed clean=False elapsed_ms=200 timeout_ms=200`; both timeouts at
    WARNING.
  - `test_exhausted_budget_logs_zero_wait_probes`: P1 uses the 100 ms budget, so both later
    timeouts log `wait_ms=0`, and the completed line ends with `timeout_ms=100`.
- [x] Existing substring assertions still match (`teardown_completed clean=True/False`,
  `_interrupt_timeout`, `_wait_idle_timeout elapsed_ms=`, `teardown_started timeout_ms=5000`).
  The reviewed repro test `tests/test_collection_import_teardown_budget_repro.py` was not
  modified.
- [x] Logging works in error scenarios (timeout / unclean paths covered above)
- [x] Large data structures are not logged
- [ ] Metrics are available for monitoring (N/A, no metrics added)

Commands:

- `make test WORKERS=1 PYTEST_ARGS='tests/test_collection_import_teardown_policy.py
  tests/test_collection_import_teardown_budget_repro.py tests/test_collection_import_teardown_repro.py
  tests/test_collection_import_cancellation_repro.py tests/test_collections_import_ui_repro.py
  tests/test_collections_presenter.py tests/test_collection_import_lifecycle_policy.py'`
  → 6/7 files passed. `tests/test_collection_import_teardown_repro.py` was killed by the
  runner's 120 s worker timeout in
  `test_unexpected_reader_exception_requires_teardown_and_reaps_worker`. This is the
  pre-existing flaky deadlock triaged in Step 4: it happens before any teardown code runs, so
  the changed log lines are not on that path. A rerun of that file alone also timed out once.
  Then three reruns with `-o faulthandler_timeout=50` → 3/3 passed.
- `make lint` → OK (flake8 `pypost/`; Markdown lint OK, 16 files; relative link check OK,
  18 files).
- `make typecheck` → mypy baseline OK (181 known errors; no new errors).
- `make verify-ai-tasks` → artifacts baseline OK (395 completed tasks; 2 grandfathered legacy
  gaps).

## Notes

- `doc/dev/collection_import.md` still lists the old field sets for
  `collection_import_teardown_completed`, `collection_import_worker_interrupt_timeout`
  (still described as "100ms"), and `collection_library_import_worker_timeout`. Step 8 should
  update them.
- Operator reading guide: a P2/P3 timeout with `wait_ms=0` means an earlier phase (usually P1
  `wait_idle_timeout`) used the budget. A timeout with `wait_ms>0` means that worker did not
  stop within the time it was given. A completed line with `elapsed_ms` well above
  `timeout_ms + 50` points to slow work outside the waits (event processing, logging handlers).
