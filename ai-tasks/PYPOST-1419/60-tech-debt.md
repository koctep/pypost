# PYPOST-1419: Technical Debt Analysis

## Shortcuts Taken

1. **Underscore facade layer retained for FR6 continuity**:
   - `tests/makefile_test_helpers.py` still exports `_venv_ready`, `_build_skeleton`,
     `_get_shared_base_venv`, and `_materialize_prewarmed_venv` as thin delegates to the
     process-default `SharedVenvManager`.
   - Required so fixtures and `scripts/run_parallel_tests.py` keep importing the historical
     helper names. Callers still see underscore “private” APIs that are effectively public.

2. **Lazy module-default manager singleton (by convention)**:
   - `_shared_venv_manager` / `_get_shared_venv_manager()` replace the old `_SHARED_BASE_VENV`
     path cache. Readiness SoT is now `manager._resolved_base`, but a module-level instance
     cache remains for process-wide fixture sharing.
   - Late-bind shims (`_module_preparation_runner`, `_module_flock`, `_ModuleClock`,
     `_module_tempdir`) exist solely so readiness tests can monkeypatch the helpers module.

3. **External `cp -a` materialization retained**:
   - `SharedVenvManager.materialize` still shells out via the injectable preparation runner
     rather than native in-process copy/symlink (tracked as PYPOST-1420).

4. **Silent skeleton → base fallback**:
   - `source = skeleton if self.is_ready(skeleton) else base` still falls back to a full base
     copy when the skeleton is missing or incomplete, without a distinct “template damaged”
     error (deeper readiness is PYPOST-1421).

5. **POSIX venv layout + static `pyvenv.cfg` fallback**:
   - `bin/python`, `lib/python{ver}/site-packages`, and `home = /usr/bin` when `pyvenv.cfg`
     is absent remain hardcoded Unix assumptions carried forward from PYPOST-1413.

6. **Hardcoded bootstrap package pins in `ensure_ready`**:
   - Shared-base install still pins `pytest>=8,<9` and `flake8>=7,<8` inline rather than
     reading a lock/requirements fragment owned by the manager.

## Code Quality Issues

1. **Facade + late-bind shim surface area**:
   - Encapsulation moved lifecycle bodies into `SharedVenvManager`, but the helpers module still
     carries four facades plus four late-bind collaborators. Future cleanup should shrink this
     to a single documented default-manager accessor (or inject the manager into fixtures).

2. **`fcntl.flock` typing escape hatch**:
   - `_default_flock` / `_module_flock` use `# type: ignore[arg-type]` because the file object
     typing does not satisfy the stubs. A narrow typed wrapper would remove the ignore.

3. **Fragile subprocess diagnostic extraction**:
   - Bootstrap failures still use `getattr(error, "stderr", None) or getattr(error, "output", None)`
     across `SubprocessError` / `OSError` shapes. A small helper that normalizes
     `TimeoutExpired` / `CalledProcessError` streams would be clearer.

4. **Non-atomic `.skeleton` publication window**:
   - `build_skeleton` still `rmtree`s the destination before `Path.replace`, leaving a brief
     missing-skeleton window on filesystems where non-empty directory replace is not atomic
     (same residual as PYPOST-1413).

5. **`is_ready` remains marker + interpreter only**:
   - Does not validate `_prewarmed_base.pth` existence or that the pointed site-packages path
     is readable (PYPOST-1421).

## Missing Tests

1. **Corrupted / unreachable `_prewarmed_base.pth` recovery** — not covered at manager or
   readiness suite level (pairs with PYPOST-1421).
2. **Facade deprecation / direct-manager consumer migration** — no test asserts that external
   callers can depend solely on `SharedVenvManager` without underscore helpers.
3. **Windows / non-POSIX layout** — no coverage for `Scripts/` / `Lib/` layouts.
4. **Extreme concurrency (>4 workers under I/O throttle)** — still owned by PYPOST-1422;
   this task only kept the existing 4-worker load-budget case green.
5. **Timeout markers**: `tests/test_shared_venv_manager.py` and
   `tests/test_makefile_shared_readiness.py` declare explicit `pytestmark` /
   `@pytest.mark.timeout` — **no BLOCKER** for missing timeouts in this change set.

## Performance Concerns

1. **`cp -a` fork/exec per workspace** — residual ~10–20ms overhead vs native materialization
   (PYPOST-1420).
2. **Shared site-packages via `.pth`** — concurrent worker imports still hit one shared base
   tree; extreme NFS read spikes remain a residual risk (PYPOST-1422).
3. **`site` module `.pth` parse on every workspace Python start** — nominal (<1ms) per process.

## Follow-up Tasks

1. **Native in-process workspace materialization** — already ticketed
   [PYPOST-1420](https://pypost.atlassian.net/browse/PYPOST-1420).
2. **Deep template validation in readiness** — already ticketed
   [PYPOST-1421](https://pypost.atlassian.net/browse/PYPOST-1421).
3. **Extreme concurrency stress for shared venv materialization** — already ticketed
   [PYPOST-1422](https://pypost.atlassian.net/browse/PYPOST-1422).
4. **Retire underscore facades / late-bind shims after consumers import `SharedVenvManager`
   directly** — Jira: [PYPOST-1440](https://pypost.atlassian.net/browse/PYPOST-1440).
   Priority: Low. Scope: migrate `run_parallel_tests` + fixtures; delete redundant wrappers.

5. **`NON-BLOCKER — pre-existing`: lockfile drift in `requirements-dev.txt`**
   - Jira: [PYPOST-1397](https://pypost.atlassian.net/browse/PYPOST-1397)
     (deduped; open To Do — do not recreate)
   - Verdict: **NON-BLOCKER — pre-existing**
   - Node id:
     - `tests/test_lockfile_verification.py::test_repro_check_lock_dev_detects_no_drift`
   - Repro:
     ```bash
     git worktree add /tmp/baseline-PYPOST-1419 3fa5cf6bd68cff8a31e75bb1276cf9b9e017fade
     cd /tmp/baseline-PYPOST-1419
     PATH=/home/src/.venv/bin:$PATH make test WORKERS=1 \
       PYTEST_ARGS='tests/test_lockfile_verification.py -vv --tb=short'
     ```
   - Base commit: `3fa5cf6bd68cff8a31e75bb1276cf9b9e017fade`
   - Failure excerpt:
     ```
     check-lock-dev: requirements-dev.txt is stale relative to requirements-dev.in
       (run 'make lock-dev' and commit)
     make[1]: *** [Makefile:95: check-lock-dev] Error 1
     assert 2 == 0
     ```
   - Suspected cause: committed `requirements-dev.txt` drifted vs `requirements-dev.in` under
     the pinned uv toolchain.
   - Found during: PYPOST-1419 Step 4 review / Step 7 triage.

6. **`NON-BLOCKER — environment-sensitive (not confirmed at clean baseline worktree)`:
   `test_ui_library_manager` worker crash after all assertions pass**
   - Jira: [PYPOST-1441](https://pypost.atlassian.net/browse/PYPOST-1441)
   - Verdict: **NOT confirmed pre-existing at base** — clean worktree at
     `3fa5cf6bd68cff8a31e75bb1276cf9b9e017fade` passed repeatedly
     (`make test WORKERS=1` and default workers; 3/3 stress iters green).
   - Observed during Step 4 `make check` / Step 7 on the **main working tree** via
     `make test` parallel runner: all 14 collected tests PASSED, then worker
     `exit_code=-11` (occasionally `-7`). Direct
     `python -m pytest tests/test_ui_library_manager.py` exits 0 on the same tree but
     prints shiboken atexit noise (`FoldableCodeView` already deleted).
   - No imports of `SharedVenvManager` / `makefile_test_helpers` — not attributable to
     PYPOST-1419 encapsulation code.
   - Node ids (module worker failure after pass; last node before termination):
     - `tests/test_ui_library_manager.py::TestLibraryDialogs::test_library_manager_dialog_integration`
     (and the other 13 nodes in the file all PASSED)
   - Repro (main tree; baseline worktree does **not** reproduce):
     ```bash
     make test WORKERS=1 PYTEST_ARGS='tests/test_ui_library_manager.py'
     ```
   - Failure excerpt:
     ```
     ... test_library_manager_dialog_integration PASSED [100%]
     ERROR test_file_failed ... file=tests/test_ui_library_manager.py exit_code=-11
     Total Files: 1 | Passed: 0 | Failed: 1
     ```
   - Suspected cause: Qt/PySide teardown / shiboken lifetime during worker process exit
     (same class as PYPOST-1315 / PYPOST-1357); root cause not investigated.
   - Found during: PYPOST-1419 Step 4 review / Step 7 triage.

7. **`NON-BLOCKER — environment-sensitive (not confirmed at clean baseline worktree)`:
   `test_delete_open_tabs_integration` worker crash after all assertions pass**
   - Jira: [PYPOST-1442](https://pypost.atlassian.net/browse/PYPOST-1442)
   - Verdict: **NOT confirmed pre-existing at base** — clean baseline worktree passed
     repeatedly; main-tree `make test` fails after 4/4 PASSED with `exit_code=-11` or `-7`.
   - No SharedVenvManager / makefile helper imports.
   - Node ids (module worker failure after pass; last node before termination):
     - `tests/test_delete_open_tabs_integration.py::TestDeleteOpenTabsIntegration::test_request_delete_leaves_unrelated_tabs_open`
     (and the other 3 nodes in the file all PASSED)
   - Repro (main tree; baseline worktree does **not** reproduce):
     ```bash
     make test WORKERS=1 PYTEST_ARGS='tests/test_delete_open_tabs_integration.py'
     ```
   - Failure excerpt:
     ```
     ... test_request_delete_leaves_unrelated_tabs_open PASSED [100%]
     ERROR test_file_failed ... file=tests/test_delete_open_tabs_integration.py exit_code=-11
     Total Files: ... | Passed: 0 | Failed: ...
     ```
   - Suspected cause: Qt/PySide worker teardown (environment-sensitive); root cause not
     investigated.
   - Found during: PYPOST-1419 Step 4 review / Step 7 triage.
