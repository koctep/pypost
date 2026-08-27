# PYPOST-1192: Technical Debt Analysis

## Shortcuts Taken

1. **Direct-child kill only (no process-group teardown)**: Timeout uses
   `subprocess.run(..., timeout=worker_timeout)`. On `TimeoutExpired`, Python
   kills and waits for the **direct** worker process. Architecture explicitly
   deferred `start_new_session` + `killpg` / process-group orphan cleanup.
   Typical worker shape is one pytest Python process, so this meets the
   product bound; grandchildren (or pytest-spawned helpers) can outlive the
   killed parent and briefly orphan.

2. **Dual default: script 30s vs Makefile 120s**: Product default remains
   `DEFAULT_WORKER_TIMEOUT = 30.0` (CLI/env fallthrough). Suite operators via
   `make test` / `make test-cov` get `WORKER_TIMEOUT ?= 120` and
   `--worker-timeout $(WORKER_TIMEOUT)` so legitimate slow files (e.g. makefile
   smoke ~64–87s) are not false-TIMED_OUT. Architecture originally called Make
   wiring optional; Step 4 added it as an operational necessity. Operators who
   invoke the script without Make still hit 30s — easy to surprise if docs are
   skimmed.

3. **Hung-worker test mocks `TimeoutExpired`**:
   `test_hung_worker_under_timeout_yields_timed_out` patches `subprocess.run`
   to raise `TimeoutExpired` under a 1s config rather than waiting on a real
   sleep+kill path. Keeps CI bounded; does not exercise OS-level kill or
   orphan grandchildren.

4. **`parallel_test_run_started` omits `worker_timeout`**: Run-start INFO logs
   workers, coverage, report path, targets, and pytest arg count, but not the
   configured per-worker bound. Operators infer the bound from docs, Make env,
   or the WARNING `worker_timeout timeout_seconds=…` only after a timeout.
   Observability Step 6 recorded this as optional enrichment, not DoD.

5. **Runner contract docs deferred to Step 8**: `doc/dev/parallel_test_runner.md`
   is not yet updated for `--worker-timeout` / `WORKER_TIMEOUT` / `TIMED_OUT`
   (planned in architecture Step 8). Until then, dual-default behavior is only
   documented in Makefile comments and this debt file.

## Code Quality Issues

1. **Process-group orphans on timeout**: No `start_new_session=True` on worker
   spawn and no `os.killpg` on timeout. If evidence of lingering orphans
   appears in CI (zombie helpers, locked ports, coverage file writers), harden
   teardown to process-group kill.

2. **Default asymmetry is easy to misread**: Script/CLI product default is 30;
   Make suite default is 120. Both are intentional, but naming (`WORKER_TIMEOUT`
   meaning different effective values depending on entrypoint) increases
   operator confusion until Step 8 docs spell out both paths.

3. **Coverage combine/report/html subprocesses remain unbounded**:
   `CoverageManager.combine_and_report` still calls `subprocess.run` without
   `timeout=` (pre-existing from PYPOST-1149). Out of PYPOST-1192 scope (worker
   wait only), but a hung `coverage combine` can still stall `make test-cov`
   after all workers finish.

4. **Hand-rolled `CLIParser` still owns `--worker-timeout`**: Same fragile
   manual loop as PYPOST-1149; invalid/zero CLI values fall through to env/
   default (consistent with `get_worker_timeout` guards) but parser debt stays
   under PYPOST-1153.

5. **`scripts/` outside `make lint` flake8 scope**: Pre-existing; timeout path
   was reviewed manually in Step 5. Expanding flake8 to `scripts/` remains a
   repo-wide follow-up, not this ticket.

## Missing Tests

Timeout-marker review for **this task's** tests: **no blocker** —
`tests/test_run_parallel_tests.py` has module `pytestmark = pytest.mark.timeout(60)`;
fixture-generated hang files use `pytestmark = pytest.mark.timeout(10)`.

1. **No unit tests for `get_worker_timeout` precedence**: CLI → env → 30, and
   invalid/empty/zero env fallthrough, are untested in isolation.

2. **No Makefile contract assertion for `--worker-timeout` /
   `WORKER_TIMEOUT`**: `tests/test_makefile.py` does not lock the Make recipe
   wiring added in Iteration 2 (related to PYPOST-1153 makefile contract debt).

3. **No real OS kill / orphan integration test**: Only the mocked
   `TimeoutExpired` path is covered; no test that a sleeping child is actually
   terminated within the bound, or that grandchildren are cleaned up.

4. **No assertion that `parallel_test_run_started` includes (or intentionally
   omits) `worker_timeout`**: Once Step 8/docs or a follow-up adds the field,
   a log-contract test should lock it.

## Performance Concerns

1. **False TIMED_OUT under script default 30**: Invoking
   `scripts/run_parallel_tests.py` without Make/`WORKER_TIMEOUT`/`--worker-timeout`
   will kill legitimate slow files (≥30s). Make path mitigates for the primary
   quality gate; direct script use does not.

2. **Timeout floor vs per-test markers**: Worker wall-clock bound is independent
   of module `pytest.mark.timeout` values. A file with many tests each marked
   ≤60s can still TIMED_OUT at the orchestrator bound if cumulative file time
   exceeds `worker_timeout`. Operators must raise the bound for heavy files —
   documented as intentional in architecture.

3. **Orphan grandchildren after kill**: If present, they can hold ports, Qt
   resources, or write coverage fragments after the orchestrator has moved on,
   causing flaky follow-on files in the same suite. No evidence filed yet;
   listed as escalate-if-seen debt.

## Follow-up Tasks

### Implementation follow-ups (PYPOST-1192 scope debt)

1. Harden worker timeout teardown with process-group kill
   (`start_new_session` + `killpg`) if orphan grandchildren appear in CI.
   Priority: Medium when evidence exists; Low until then.
   Jira: [PYPOST-1197](https://pypost.atlassian.net/browse/PYPOST-1197)
2. Add `worker_timeout=…` to `parallel_test_run_started` structured INFO so
   operators see the bound at run start without waiting for a timeout WARNING.
   Priority: Low (optional observability enrichment).
   Jira: [PYPOST-1198](https://pypost.atlassian.net/browse/PYPOST-1198)
3. Document dual defaults (script 30 vs Make `WORKER_TIMEOUT ?= 120`) in
   `doc/dev/parallel_test_runner.md` — owned by Step 8 of this task.
4. Add unit tests for `get_worker_timeout` precedence and invalid env/CLI
   fallthrough; optionally extend makefile contract tests for
   `--worker-timeout`. Can ride PYPOST-1153 makefile/parser debt or a small
   follow-up Debt issue.
   Jira: [PYPOST-1199](https://pypost.atlassian.net/browse/PYPOST-1199)
5. Consider bounding `CoverageManager` combine/report/html subprocesses
   (pre-existing unbounded waits) — out of this story; track under
   [PYPOST-1153](https://pypost.atlassian.net/browse/PYPOST-1153) if desired.

### Pre-existing / filed suite issues (NON-BLOCKER)

From Step 4 suite triage at base `18a4d9d1` (and related hang). Not caused by
the timeout implementation; timeout correctly surfaces the websocket hang as
`TIMED_OUT`.

| Item | Verdict | Jira |
| --- | --- | --- |
| Collection item delete/rename `_unpack_context` arity (`test_collection_item_strategies`, `test_request_manager_delete`) | NON-BLOCKER — pre-existing at `18a4d9d1` | [PYPOST-1193](https://pypost.atlassian.net/browse/PYPOST-1193) |
| SOLID `FILE_CAPS` drift (`test_audit_module_inventory_within_caps`) | NON-BLOCKER — pre-existing at `18a4d9d1` | [PYPOST-1194](https://pypost.atlassian.net/browse/PYPOST-1194) |
| WebsocketDraftObservability caplog assertions (`test_tabs_presenter`) | NON-BLOCKER — pre-existing at `18a4d9d1` | [PYPOST-1195](https://pypost.atlassian.net/browse/PYPOST-1195) |
| Flaky `test_update_tools_restarts_when_exposed_set_changes` (port-busy under parallel suite) | NON-BLOCKER — flaky; green alone / re-run | [PYPOST-1196](https://pypost.atlassian.net/browse/PYPOST-1196) |
| `test_websocket_client_ui_repro.py` hang (now correctly `TIMED_OUT` under worker timeout) | NON-BLOCKER — pre-existing hang; timeout is intended | [PYPOST-1181](https://pypost.atlassian.net/browse/PYPOST-1181) (commented) |
