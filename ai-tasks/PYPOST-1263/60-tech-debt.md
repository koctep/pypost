# PYPOST-1263: Technical Debt Analysis

## Shortcuts Taken

No shortcuts were taken within the ticket scope. The large-dataset benchmark now gates on
current-thread CPU time (`time.thread_time()`) with the original strict `< 100.0` ms budget.
Wall time (`time.perf_counter()`) is reported only as failure context. The workload (500
incoming collections, 2,500 requests, 25 conflicts) and the functional assertions are
unchanged. No retries, skips, xfails, or larger budgets were added (AC-6).

Accepted trade-offs, as recorded in `20-architecture.md`:

- **CPU budget is not a wall-latency guarantee** (NON-BLOCKER, by design). The test no longer
  shows that the planner responds within 100ms of wall time on a loaded host. That was never
  something a shared CI runner could guarantee. Wall time is still printed when the test fails.
- **Synchronous-planner assumption** (NON-BLOCKER). `thread_time()` only counts work done on
  the calling thread. If `plan_collection_import` later moves work to another thread or adds
  blocking I/O, the gate will under-count that work. This assumption is written down in
  `20-architecture.md`. It needs no action now.

## Code Quality Issues

- **Missing return annotation** (NON-BLOCKER, Low).
  `tests/test_collection_import_profile.py::test_plan_collection_import_large_dataset_performance`
  is declared without `-> None`. The other two tests in the module also lack it, so this is
  existing module style, not something this change introduced. Fix it in a future edit of the
  module, not as a separate ticket.
- **Import grouping in the clock module** (NON-BLOCKER, Lowest).
  `tests/test_collection_import_profile_clock.py` puts `import tests.test_collection_import_profile as profile`
  after the `from pypost...` imports in one block. Both are first-party imports and
  `make lint` does not check test files. Cosmetic only. Left as is.
- **Meta-test coupled to private benchmark-module names** (NON-BLOCKER, Low). The clock tests
  monkeypatch the module-level `time`, `plan_collection_import`, `_make_sample_collections`,
  and `find_collection_conflicts` names of the profile module. This was chosen on purpose so
  that the real benchmark function is exercised (see the `20-architecture.md` Q&A). The cost:
  renaming those helpers, or changing the benchmark to `from time import ...`, breaks the
  meta-tests loudly (they fail, they do not pass silently). Acceptable. No follow-up.

## Missing Tests

No missing tests in this ticket's scope. The four deterministic clock scenarios
(`external-descheduling`, `excess-planner-work`, `strict-cpu-boundary`,
`synthetic-low-wall-high-cpu`) cover the gating policy, the strict boundary, the CPU-attributed
failure message, and placement of the measurement interval. The real-clock benchmark still runs
the real planner.

**Timeout markers (BLOCKER check): pass.** `tests/test_collection_import_profile.py` declares
`pytestmark = pytest.mark.timeout(60)`. `tests/test_collection_import_profile_clock.py`
declares `pytestmark = pytest.mark.timeout(10)`. No test added or edited by this change lacks an
explicit timeout.

## Performance Concerns

- **The same flaky wall-clock pattern remains in the same module** (NON-BLOCKER, out of scope
  per `10-requirements.md`). These tests still gate on `time.perf_counter()` deltas and can
  fail under parallel CPU contention for the same reason PYPOST-1263 did:
  - `tests/test_collection_import_profile.py::test_plan_collection_import_conflict_matrix_profile`
    has a 50ms wall budget around `plan_collection_import`. This is the tightest threshold in
    the module and the most likely to flake next.
  - `tests/test_collection_import_profile.py::test_apply_imported_collections_performance` has
    a 500ms wall budget around `apply_imported_collections`. It has more headroom, and the
    apply path touches persistence on a fake manager, so a CPU-time gate needs checking before
    it is applied here.
- **Tight wall-clock thresholds elsewhere in the suite** (NON-BLOCKER, out of scope). These
  showed up in a search for `perf_counter`/`monotonic` thresholds. They measure Qt event-loop
  latency, where wall time is the real metric, so the CPU-time approach does not carry over
  directly:
  - `tests/test_pypost_1242_failing_repro.py::test_high_frequency_variable_update_burst`: 50ms
    peak latency.
  - `tests/test_pypost_1242_failing_repro.py::test_rapid_environment_switching_burst_stress`:
    5ms average latency.
  - `tests/test_websocket_echo_server.py::test_offscreen_responsiveness_under_load`: 50ms max
    event-loop tick.

  Hang guards with generous bounds (`elapsed_s < 2.0` around a 300ms `process_until`, and the
  1000ms cancellation stop in `test_collection_import_decode_cancellation.py`) are deadline
  checks, not micro-benchmarks. They were excluded as a different, lower-risk pattern.
  `test_environment_save_selective_reencrypt_benchmark.py::test_selective_second_save_faster_than_full_reencrypt`
  uses a relative speedup ratio, which partly cancels out contention. It was also excluded.
- **Residual CPU-time sensitivity** (NON-BLOCKER, accepted). Thread CPU time still changes with
  cache misses, SMT sibling contention, and CPU frequency scaling under load. It does not include
  descheduling, which caused the reported failure. The Jira evidence shows about 49ms wall time in
  isolation. Thread CPU cannot exceed that figure, so the headroom against the 100ms budget
  is at least 2x. No action unless a CPU-gated failure is seen.
- **`thread_time` portability** (no debt). `time.thread_time()` exists on all platforms
  supported by `requires-python = ">=3.11"`, and CI runs on `ubuntu-latest`. No platform gating
  is needed.

## Follow-up Tasks

1. **Priority: Medium.** Apply a contention-resistant gate (current-thread CPU budget plus wall
   diagnostic, as in PYPOST-1263) to
   `tests/test_collection_import_profile.py::test_plan_collection_import_conflict_matrix_profile`
   (50ms wall) and
   `tests/test_collection_import_profile.py::test_apply_imported_collections_performance`
   (500ms wall). For the apply test, first confirm the measured work is synchronous and
   CPU-bound. Jira: [PYPOST-1318](https://pypost.atlassian.net/browse/PYPOST-1318)
2. **Priority: Low.** Review the Qt event-loop latency thresholds for flakiness under parallel
   load:
   `tests/test_pypost_1242_failing_repro.py::test_high_frequency_variable_update_burst`,
   `tests/test_pypost_1242_failing_repro.py::test_rapid_environment_switching_burst_stress`,
   `tests/test_websocket_echo_server.py::test_offscreen_responsiveness_under_load`. Wall
   latency is the real metric here, so this needs its own design (for example, an
   attribution-aware or relative bound), not a switch to CPU time.
   Jira: [PYPOST-1317](https://pypost.atlassian.net/browse/PYPOST-1317)
3. **Priority: Lowest.** Optional runtime telemetry: add CPU and wall planning duration fields
   to the production `collection_import_plan_created` INFO log in
   `pypost/core/collection_import.py`. This changes production code, which is outside
   PYPOST-1263 (AC-8). Only worth doing if someone needs planner latency in the field.
   Jira: [PYPOST-1319](https://pypost.atlassian.net/browse/PYPOST-1319)

No pre-existing test failures were seen during this step. Step 7 ran no test targets. The
targeted runs from Steps 4 and 5 were green.
