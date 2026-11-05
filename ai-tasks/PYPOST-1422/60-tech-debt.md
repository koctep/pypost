# PYPOST-1422: Technical Debt Analysis

## Shortcuts Taken

1. **Local seed helpers in the stress module**:
   - `_seed_interpreter` / `_seed_ready_skeleton` / `_successful_bootstrap` are
     duplicated from `tests/test_shared_venv_manager.py` rather than extracted to a
     shared test helper package.
   - Acceptable for isolation; extract if a third consumer appears.

2. **No-op `flock` in the stress harness**:
   - Stress uses `flock=lambda *_args, **_kwargs: None` so threads do not block on
     a real lock file while exercising concurrent `materialize` population.
   - Does not cover flock contention at 16 workers; the readiness suite already
     covers lock wait / deadline paths separately.

3. **ThreadPool instead of multiprocessing**:
   - Architecture chose threads so injected `tree_copier` latency applies without
     cross-process patching. Does not stress fork+import of the default manager.

4. **No production code change**:
   - Current in-process materialization already passed 16-worker latency stress.
   - Residual NFS/import contention against a live shared base remains outside
     this deterministic DI scenario.

## Code Quality Issues

1. **Duplicated seed helpers** — see Shortcuts #1.
2. **Architecture constants are module globals** — consistent with
   `test_session_slots_stress.py`; fine for a dedicated stress module.
3. **POSIX interpreter seed script** — same Unix-centric layout assumptions as
   prior shared-venv tickets.

## Missing Tests

1. **Multiprocess extreme concurrency against the real shared base** — 16+ forked
   workers calling `_materialize_prewarmed_venv` under an OS-level I/O throttle.
2. **Flock contention at extreme concurrency** — concurrent `ensure_ready` under
   a real exclusive lock with 16 waiters.
3. **Timeout markers**: module `pytestmark` + function `@pytest.mark.timeout(120)`
   — **no BLOCKER** for missing timeouts.

## Performance Concerns

1. **Stress module wall budget (15s)** is generous relative to 0.05s simulated
   latency × parallel workers; tighten only after measuring CI variance.
2. **Shared site-packages via `.pth`** under live NFS with 16+ workers importing
   simultaneously remains a residual environment risk not fully modeled by
   sleep-injected copytree.

## Follow-up Tasks

1. **Extract shared venv test seed helpers** — move `_seed_ready_skeleton` /
   `_seed_interpreter` to `tests/helpers/` to dedupe manager + extreme suites.
   Jira: [PYPOST-1446](https://pypost.atlassian.net/browse/PYPOST-1446).
2. **Optional multiprocess extreme stress against real shared base** — complement
   the DI ThreadPool case with fork workers + documented skip/env gate if too
   heavy for default `make test`.
   Jira: [PYPOST-1447](https://pypost.atlassian.net/browse/PYPOST-1447).
3. **Facade retirement** — already ticketed as
   [PYPOST-1440](https://pypost.atlassian.net/browse/PYPOST-1440) (do not duplicate).
