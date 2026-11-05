# PYPOST-1321: Technical Debt Analysis

Scope analysed: working-tree changes for registering collections as a main-window
shutdown owner (`pypost/ui/main_window_lifecycle.py`,
`pypost/ui/presenters/collections_presenter.py`,
`pypost/ui/presenters/collections_presenter_lifecycle.py` (new),
`pypost/ui/presenters/collection_import_actions.py`, `pypost/core/lifecycle.py`,
`pypost/core/metrics_registry.py`, Step 3/4/6 tests, and prior-step artifacts).

**Timeout markers (do-testing BLOCKER check): no blocker.** Touched and new test modules
declare explicit timeouts (`tests/test_main_window_collections_shutdown_repro.py`
`pytestmark = timeout(30)`; `tests/test_lifecycle_observability.py` `timeout(60)`;
existing collection-import / composition harness modules retain their module marks).

## Shortcuts Taken

1. **Lazy lifecycle fields via `getattr` / `setattr`.**
   `collections_presenter_lifecycle.ensure_lifecycle_state` installs `_teardown_lock`,
   `_teardown_started`, and `_teardown_result` on first use instead of growing
   `CollectionsPresenter.__init__`. This keeps the presenter at 534 LOC (≤535 baseline
   cap from PYPOST-376 / Step 4 Iteration 4) and matches the mypy-safe pattern used by
   `main_window_lifecycle`. Peer owners (`tabs`, `env`) declare fields on the instance;
   collections is the odd one out. Acceptable for this task; promote to real attributes
   when the LOC budget allows. See follow-up 1.

2. **Dual teardown log lines retained.**
   Each collections teardown emits both peer-shaped `lifecycle_teardown_*` (with
   `teardown_id`) and legacy `collections_presenter_teardown_*` (no correlation id).
   Step 6 documents preferring the lifecycle lines for cross-owner correlation. The
   duplicate keeps PYPOST-1264 greps green but adds noise. See follow-up 2.

3. **Application shutdown `5000` literals left unnamed.**
   Requirements DoD 8 / architecture allowed skipping PYPOST-1325; collections receives
   a fair share from the existing allocator once listed. Naming debt stays on
   [PYPOST-1325](https://pypost.atlassian.net/browse/PYPOST-1325).

4. **In-flight app-close repros use a composition harness owner, not a live presenter.**
   `tests/test_main_window_collections_shutdown_repro.py` drives
   `main_window_lifecycle.teardown` with `_CollectionsImportOwner` wrapping real
   `CollectionImportActions` + spy workers. That proves owner order, fair share, and
   import teardown under budget, but does not exercise
   `CollectionsPresenter.begin_teardown` / panel close through the composition root.
   Idle idempotency and observability cover the real presenter path separately. See
   follow-up 3.

## Code Quality Issues

1. **`CollectionsPresenter` remains one LOC from the baseline cap (534 / 535).**
   Lifecycle extraction avoided a breach, but any further method on the presenter will
   force another extract or a baseline bump. Follow-up 1.

2. **Lazy attribute access is noisier than typed instance fields.**
   `getattr`/`setattr` for lifecycle state works and satisfies mypy, but it is easier to
   misuse than `presenter._teardown_lock` as used by `tabs_presenter_lifecycle`. Same
   item as Shortcut 1.

3. **Admission fence is production-complete, thinly tested at the actions surface.**
   `CollectionImportActions.begin_teardown` / `_teardown_started` gates file and library
   entry points (including when idle). Composition tests assert early `begin_teardown`
   call counts; there is no dedicated unit that starts an import after fence while idle
   and asserts rejection. Follow-up 3.

4. **Library-worker join-only limitation unchanged.**
   Non-interruptible `LibraryOperationWorker` can consume the collections share and
   report `incomplete`. Accepted by design; tracked as
   [PYPOST-1324](https://pypost.atlassian.net/browse/PYPOST-1324).

5. **Nested uncapped `worker_finish_join_ms` overrun (PYPOST-1264 Risk 3) unchanged.**
   Still can slightly overrun the collections share; documented tolerance; test gap on
   [PYPOST-1322](https://pypost.atlassian.net/browse/PYPOST-1322).

## Missing Tests

1. **Dedicated idle admission-fence rejection after `begin_teardown`.**
   No focused assert that file/library import entry points no-op with reason=`teardown`
   when fenced while `IDLE`. Covered only indirectly via owner `begin_calls`.

2. **End-to-end composition with a real `CollectionsPresenter` during in-flight import.**
   Harness doubles cover budget/order; presenter + panel close under main-window teardown
   with a live worker is not one integrated test. Low priority given split coverage.

3. **Otherwise covered for this task:** owner order and fair share; file and library
   in-flight under budget; bool→`TeardownResult` callers; idle idempotent owner set;
   correlated lifecycle logs/metrics and `_LIFECYCLE_OWNERS` allowlist;
   main-window `owner_count=5`.

## Performance Concerns

1. **Worst-case collections share still dominated by the library worker** (PYPOST-1324).
   With five owners and overall budget `B`, collections at index 3 gets
   `min(B * 2/5, remaining)`; a stuck library join can use that entire grant. Close
   remains bounded by the overall deadline.

2. **Teardown holds `_teardown_lock` for the full import wait.**
   Same shape as peer lifecycle helpers; correct for idempotency, but means a second
   teardown call blocks until the first finishes rather than returning the cached result
   mid-wait. Acceptable for single-threaded GUI shutdown. No new ticket.

3. **Idle collections teardown remains effectively free** — no new concern introduced.

## Follow-up Tasks

New / residual items from this task (do **not** invent Jira keys here; file later via
tech-debt-jira-sync / jira-create-issue):

1. **Promote collections lifecycle fields off lazy `getattr`/`setattr` (or further extract
   presenter surface)** so `CollectionsPresenter` is not stuck at 534/535 and matches peer
   owners' typed lifecycle state. Priority: **Low**.
   Jira: [PYPOST-1471](https://pypost.atlassian.net/browse/PYPOST-1471)

2. **Thin or retire legacy `collections_presenter_teardown_*` log lines** once operators
   and tests rely on `lifecycle_teardown_*` + `teardown_id`. Priority: **Lowest**.
   Jira: [PYPOST-1472](https://pypost.atlassian.net/browse/PYPOST-1472)

3. **Add a focused admission-fence unit test** (idle `begin_teardown` then import entry
   rejects) and optionally one composition path with a real `CollectionsPresenter` during
   an in-flight worker. Priority: **Low**.
   Jira: [PYPOST-1473](https://pypost.atlassian.net/browse/PYPOST-1473)

Already-ticketed residual (pointers only; not re-filed):

4. **Name the application shutdown `5000` budget** —
   [PYPOST-1325](https://pypost.atlassian.net/browse/PYPOST-1325). Priority: **Low**.
5. **Make `LibraryOperationWorker` interruptible** —
   [PYPOST-1324](https://pypost.atlassian.net/browse/PYPOST-1324). Priority: **Medium**.
6. **Test nested worker-finish join overrun** —
   [PYPOST-1322](https://pypost.atlassian.net/browse/PYPOST-1322). Priority: **Lowest**.

### Pre-existing suite failures (Step 5 / Step 7 re-check)

Reproduced under this working tree with
`make test WORKERS=1 PYTEST_ARGS='…'` (same five node ids). Unrelated to collections
owner registration (`collections_presenter_lifecycle` is under an already-packaged
`presenters` package). Verdict for all: **`NON-BLOCKER — pre-existing`**. Jira keys are
**not invented here**; link known tickets only where already filed.

| Node id | Failure excerpt (one line) | Notes |
| --- | --- | --- |
| `tests/test_bundled_examples_packaging.py::test_explicit_packages_cover_application_tree_and_examples` | package set differs: missing `pypost.ui.{models,views,workers}` in setuptools packages | [PYPOST-1474](https://pypost.atlassian.net/browse/PYPOST-1474) |
| `tests/test_makefile_install_seed_contract.py::test_committed_seed_covers_independent_source_inventory` | incomplete committed install seed: `pypost/ui/{models,views,workers}/__init__.py` | Same cluster [PYPOST-1474](https://pypost.atlassian.net/browse/PYPOST-1474) |
| `tests/test_pypost_1077_verification_artifacts.py::test_dialog_audit_report_has_full_discovery_and_coherent_aggregates` | `import_collection_variables_dialog.py: recorded LOC 1300 != discovered LOC 731` | [PYPOST-1475](https://pypost.atlassian.net/browse/PYPOST-1475); related [PYPOST-1448](https://pypost.atlassian.net/browse/PYPOST-1448) |
| `tests/test_pypost_1287_failing_repro.py::test_live_report_inventory_loc_matches_discovery` | recorded `{…: 1300}` != discovered `{…: 731}` for same dialog module | Same cluster [PYPOST-1475](https://pypost.atlassian.net/browse/PYPOST-1475) |
| `tests/test_lockfile_verification.py::test_repro_check_lock_dev_detects_no_drift` | `make check-lock-dev` exit 2 — `requirements-dev.txt` stale vs `.in` | Already filed: [PYPOST-1397](https://pypost.atlassian.net/browse/PYPOST-1397) |

Filed in Phase D: packaging/seed [PYPOST-1474](https://pypost.atlassian.net/browse/PYPOST-1474);
dialog LOC [PYPOST-1475](https://pypost.atlassian.net/browse/PYPOST-1475); follow-ups 1–3
[PYPOST-1471](https://pypost.atlassian.net/browse/PYPOST-1471)–[PYPOST-1473](https://pypost.atlassian.net/browse/PYPOST-1473).
