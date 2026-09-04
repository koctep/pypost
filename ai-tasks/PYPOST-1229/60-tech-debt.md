# PYPOST-1229: Technical Debt Analysis

## Shortcuts Taken

- Cancellation is layered onto the existing `on_progress(done, total)` callback rather than
  introducing a cancellation token through the parser API. This keeps the core parser Qt-free and
  follows the approved architecture, but a reader that does not accept `on_progress` remains
  uninterruptible until it returns.
- The worker uses an internal `CollectionImportCancelled` exception to unwind the parser callback
  into `QThread.run()`. This is a deliberate, local control-flow mechanism; it avoids exposing Qt
  or worker concerns from `pypost/core/collection_import.py`, but couples cancellation handling to
  exception unwinding.
- The regression suite uses a deterministic slow injected reader and exercises the presenter's
  private `_start_parse()` seam. This gives stable coverage of the worker lifecycle, but it does
  not yet prove cancellation against a real JSON/YAML file or through a user-facing close event.

No unrelated production code, dependency, or public user workflow was changed. No forcible thread
termination was introduced.

## Code Quality Issues

- `ReadImportFile` remains `Callable[..., ...]`, and `_callable_accepts_progress()` infers support
  through `inspect.signature()`. The new cancellation guarantee therefore depends on a dynamic
  convention rather than a typed cancellation-aware reader protocol. This is an explicit
  limitation of the approved design, not an architecture deviation.
- `CollectionImportActions.teardown()` has an interruption request before `wait_idle()` and a
  second guarded request before the final short join. The duplicate paths protect races between
  queued Qt signals and worker cleanup, but make the lifecycle harder to reason about.
- The final publication boundary now checks interruption after the reader returns and immediately
  before `parse_completed.emit()`. A deterministic regression holds the reader after its final
  progress callback, requests interruption, and verifies that no result reaches the presenter.
- The approved architecture is otherwise followed: interruption is checked before parsing and at
  the existing per-record progress checkpoint; cancellation has a dedicated signal and terminal
  presenter handler; and the parser remains Qt-free.

## Missing Tests

- Add a real-file test using `load_collection_import_candidates()` with a temporary JSON/YAML
  collection list. Request interruption from the progress boundary and assert exactly one
  `parse_cancelled`, no `parse_completed`, and no `parse_failed` signal.
- Add coverage for interruption requested before `worker.start()`. The pre-run check exists, but
  this branch is currently untested.
- The final-checkpoint publication race is covered by
  `tests/test_collection_import_cancellation_repro.py::test_final_publication_guard_discards_result_after_last_checkpoint`.
- Add an explicit test for the supported legacy reader without `on_progress`, documenting that it
  can only be cancelled before parsing starts or after the reader returns. This will make the
  current best-effort contract visible to future maintainers.
- The new cancellation module has `pytestmark = pytest.mark.timeout(30)`, and all internal event
  loop and thread waits pass finite timeouts. No timeout-marker blocker was found.

## Performance Concerns

- `load_collection_import_candidates()` reads the entire file and performs JSON/YAML decoding in
  `_read_records()` before entering the per-record loop. A very large or slow-to-read file cannot
  observe interruption during that read/decode phase, so cancellation latency is not bounded by
  the new per-record checkpoint for the whole parse.
- The per-record interruption check is small and the progress signal already existed, so no
  material steady-state overhead was identified. A single expensive record can still exceed the
  presenter's short join budget, as expected for cooperative cancellation.
- `wait_idle(timeout_ms=5000)` and `_WORKER_FINISH_WAIT_MS = 100` remain fixed lifecycle budgets.
  They pre-date this task and were explicitly out of scope, but an uninterruptible reader or a
  long single record can still leave teardown returning unclean after those bounds.

## Follow-up Tasks

1. Define and adopt a typed cancellation-aware `ReadImportFile` protocol. Require production and
   test readers to accept a cancellation/checkpoint callback, remove the implicit guarantee gap
   created by the `inspect.signature()` fallback, and add contract tests for supported reader
   shapes. Jira: [PYPOST-1266](https://pypost.atlassian.net/browse/PYPOST-1266)
2. Make file loading/decoding cancellation-aware for large imports, either by introducing a
   streaming parser or bounded decode checkpoints. Add a large-file latency test that measures
   cancellation from request to worker stop and records the accepted bound. Jira:
   [PYPOST-1267](https://pypost.atlassian.net/browse/PYPOST-1267)
3. Extend the cancellation tests with real JSON/YAML input, pre-start interruption, exact signal
   counts, and the legacy-reader contract described above. Keep module/class/function timeout
   markers explicit and keep every internal wait bounded. Jira:
   [PYPOST-1265](https://pypost.atlassian.net/browse/PYPOST-1265)
4. Consolidate teardown interruption and join policy, including the inherited 5000 ms default and
   100 ms worker-finish join, behind one named lifecycle policy. Revisit whether the budgets should
   be configurable only after measuring real import and teardown latency. Jira:
   [PYPOST-1264](https://pypost.atlassian.net/browse/PYPOST-1264)
5. **NON-BLOCKER — pre-existing — PYPOST-1261:** resolve the malformed nested-expression,
   frozen SOLID snapshot failures. Reproduction command: `make test`. Base-commit evidence:
   these failures reproduced before PYPOST-1229 changes at
   `bd764bb7044fa127f3e7af8411998613cf665158`; the current full run also reproduced them. Exact
   node IDs:

   - `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::test_malformed_nested_expressions`
   - `tests/test_function_expression_resolver.py::TestFunctionExpressionResolver::test_standalone_malformed_closing_paren`
   - `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`
   - `tests/test_template_service.py::TestTemplateServiceValidationOutcomes::test_validate_malformed_nested_alignment`
   - `tests/test_template_service.py::TestTemplateServiceObservability::test_render_malformed_nested_validation_failure_tracks_validation_metrics_on_hover`

   The resolver/template nodes expect `invalid_argument` but receive `invalid_arity`; the SOLID
   node compares the frozen snapshot's 241 lines with the current 260-line measurement. These
   failures are already tracked by PYPOST-1261; no duplicate issue was created.

   PYPOST-1261 also owns the Qt process-level failures observed in full runs. The exact runner
   node identifiers are:

   - `tests/test_env_dialog.py::<module>`
   - `tests/test_environment_list_widget.py::<module>`

   At the task base commit `bd764bb7044fa127f3e7af8411998613cf665158`, the accepted Step 5
   baseline comparison recorded that the focused baseline environment run passed, while the
   baseline full run reproduced the `tests/test_env_dialog.py::<module>` crash. A later task run
   observed `tests/test_environment_list_widget.py::<module>` exiting `-11` after its tests
   reported passed. These are process-level SIGSEGV identifiers, and no duplicate issue was
   created.

6. **NON-BLOCKER — pre-existing — PYPOST-1262:** investigate nested-Make load sensitivity.
   Reproduction command: `make test`. At the task base commit
   `bd764bb7044fa127f3e7af8411998613cf665158`, prior full-suite load runs timed out at these
   exact nodes:

   - `tests/test_makefile_lifecycle.py::TestVenvExtraStampIdempotency::test_venv_test_installs_when_stamp_stale`
   - `tests/test_makefile_targets.py::TestTargetExecution::test_test_succeeds_from_bare_venv_via_venv_test`

   The current `make test WORKER_TIMEOUT=120` run passed both nested-Make files, so this row
   records a previously observed, non-deterministic baseline concern rather than a current task
   failure. These nested-Make timeouts are already tracked by PYPOST-1262; no duplicate issue was
   created.

The prior Step 7 blocker is resolved: the final publication guard and deterministic presenter-path
race coverage are now in place. The cancellation limitations above are residual best-effort risks
within the accepted architecture and should be addressed by future scoped work.

## Documentation Applicability

No user-facing documentation update is applicable. Developer-facing testing or implementation
documentation belongs to Step 8 and was not changed in this Step 7-only execution.

## Validation

- `make test PYTEST_ARGS='tests/test_collection_import_cancellation_repro.py' WORKERS=1
  WORKER_TIMEOUT=60` — PASS (1 file, 4 tests, including final publication-boundary race).
- `make test PYTEST_ARGS='tests/test_collection_import_cancellation_repro.py
  tests/test_collection_import_progress.py tests/test_collection_import_teardown_repro.py
  tests/test_collections_import_ui.py' WORKERS=1 WORKER_TIMEOUT=120` — PASS (4 files).
- `make lint` — PASS.
- `make typecheck` — PASS (repository baseline: 180 known errors).
- `make verify-ai-tasks` — PASS after this artifact was created (`354 completed tasks; 2
  grandfathered legacy gaps`).
- `make test WORKER_TIMEOUT=120` — NON-BLOCKER pre-existing failures above; 328 passed, 6 skipped,
  3 failed files, 171.09 seconds.
