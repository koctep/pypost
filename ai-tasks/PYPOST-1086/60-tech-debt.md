# PYPOST-1086: Technical Debt Analysis

## Summary

The accepted implementation introduces no blocker and no unticketed follow-up. It replaces the
unsafe `QThread.finished` override with a distinct response signal, narrows every concrete signal
in the reported diagnostic set, validates the two necessary dynamic union boundaries, and restores
an exact 217-record mypy baseline.

## Shortcuts Taken

None.

- No `type: ignore`, broad cast, compatibility shim, skipped test, `xfail`, or new accepted mypy
  error was introduced.
- Runtime container classes in `Signal(...)` declarations are required by PySide rather than a
  substitute for Python type annotations; connected handlers retain more precise annotations.
- Boundary validation rejects impossible payload types instead of coercing or forwarding them.

## Signal Design and Code Quality

The result and lifecycle responsibilities are now separate and explicit:

- `RequestWorker.request_finished(ResponseData)` carries successful response results.
- Inherited zero-argument `QThread.finished()` owns deferred thread-object deletion.
- `request_save_as_completed`, `request_persisted`, import completion, environment variables, and
  hidden-key signals use their concrete runtime classes.

The remaining `object` declarations are intentional union boundaries, not unresolved task debt:

- `EnvPresenter.env_keys_changed` carries `list[str] | None`. Its receiver accepts only `list` or
  `None` and emits a type-only warning for anything else.
- `RequestWorker.script_output` carries `str | None` as its second value. Its receiver accepts only
  those values and emits a type-only warning for anything else.
- `RequestWorker.error` retains its pre-existing `ExecutionError | str` compatibility surface, and
  the presenter narrows both branches before use. Current worker emissions use `ExecutionError`.
- `variable_set_requested` retains its pre-existing nullable key payload and is unrelated to the
  diagnostics addressed by PYPOST-1086.

Qt does not provide a useful runtime union expression for these signal declarations. The current
combination of `object`, receiver narrowing, warning coverage, and precise comments is appropriate;
introducing wrappers or duplicate signals would add complexity without improving behavior.

## Validation and Logging

No validation debt was identified.

- Both invalid dynamic payload paths have behavioral tests that assert rejection, the exact event
  and unexpected type, and absence of secret-like payload values from logs.
- The impossible overwrite-without-snapshot path logs a structured ERROR and does not emit a
  typed persistence signal.
- Worker cancellation and unexpected exceptions continue through the existing error signal.
- Success and native thread termination remain distinct and are tested with a real bounded thread.

The added logs are restricted to invariant violations. No request body, response body, environment
value, hidden-key value, collection content, or rejected dynamic payload is added to logs.

## Missing Tests and Timeouts

No in-scope coverage gap or timeout blocker remains.

- The reviewed regression test exercises distinct result delivery and native zero-argument thread
  termination using `QThread.start()`, a 5-second internal wait, and a 30-second pytest timeout.
- Worker success, cancellation, result errors, unexpected exceptions, retries, nullable script
  output, hidden keys, and ownership races remain covered.
- Environment, main-window wiring, import, persistence, save flow, warning privacy, and baseline
  tooling have focused coverage.
- Every touched or relevant Python test module declares a module-, class-, or test-level timeout.

An additional native lifecycle test for every possible worker exit path is not required. Qt owns
the `finished()` guarantee, the implementation has one unconditional cleanup connection, and the
worker's individual error branches already have focused behavioral coverage.

## Baseline Correctness

The baseline reconciliation is exact:

- schema version: 2;
- scope: `pypost/core`, `pypost/models`, and `pypost/ui`;
- declared and actual entry count: 217;
- removed records: only the resolved `secret_store.py` `no-any-return` record and
  `encryption_migration_section.py` `arg-type` record;
- `make typecheck`: exit 0 with 217 current diagnostics matching 217 known records.

The checked scope, multiset identity, parser behavior, reporting, and update schema are unchanged.
No current diagnostic was silently discarded or newly accepted.

## Performance and Lifecycle Risks

No material performance concern was introduced. Signal declaration changes have no per-request
algorithmic cost. Type checks occur only at two small presenter boundaries, and warnings occur only
for invalid internal payloads.

Lifecycle risk is reduced: deferred deletion now follows native thread termination on success,
cancellation, and exceptions rather than response or error payload delivery. The presenter still
clears tab ownership through its existing result/error handlers, while `deleteLater()` is connected
once to the native lifecycle event.

## Architecture Deviations

There is one deliberate, reviewed test-strategy refinement and no production deviation. The Step 2
repro text mentioned invoking `run()` directly, while the accepted Step 3 test uses real
`QThread.start()`. A real thread is necessary to observe inherited `QThread.finished()` semantics;
the bounded event-loop and worker waits make this refinement deterministic. Production signal
interfaces, error handling, baseline reconciliation, and invocation order follow the architecture.

## Pre-existing Repository Findings

### Full-suite failures

The full Step 4 run reported 2,347 passed tests and the following three failures. All three
reproduced in a detached worktree at base commit `49441bb4` and are non-blockers already owned by
existing Debt issues:

- `tests/test_suite_qapp_alignment.py::`
  `test_suite_has_no_local_qapp_fixtures_or_setupclass_qapplication`
  - Classification: NON-BLOCKER — pre-existing.
  - Jira: [PYPOST-1110](https://pypost.atlassian.net/browse/PYPOST-1110), To Do.
- `tests/test_pypost_1077_verification_artifacts.py::`
  `test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`
  - Classification: NON-BLOCKER — pre-existing.
  - Jira: [PYPOST-1111](https://pypost.atlassian.net/browse/PYPOST-1111), To Do.
- `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::`
  `test_markdown_snapshot_matches_current_metrics`
  - Classification: NON-BLOCKER — pre-existing.
  - Jira: [PYPOST-1111](https://pypost.atlassian.net/browse/PYPOST-1111), To Do.

Read-only Jira verification on 2026-08-20 confirmed both issue summaries, Debt type, and To Do
status. Step 7 created no Jira issue.

### Direct test-tree style findings

Direct flake8 on the three touched test modules reports legacy E302/E304/E305 spacing findings in
`test_env_presenter.py` and `test_tabs_presenter.py`, plus an unused method-local `RetryPolicy`
import in `test_worker.py`. The same finding categories in the same files reproduced at base commit
`49441bb4`; only line numbers moved after adding tests.

**Classification:** NON-BLOCKER — pre-existing accepted test-tree style debt. The repository's
canonical `make lint` target intentionally checks production Python and passes. Reformatting broad
legacy test files or changing lint policy is outside PYPOST-1086, and no task-specific follow-up is
warranted.

## Follow-up and Blocker Assessment

- **Blocker:** none.
- **New in-scope technical debt:** none.
- **Unticketed follow-up remaining:** none.
- **Existing ticketed non-blockers:** PYPOST-1110 and PYPOST-1111.
- **New Jira issues created in Step 7:** none, as required.

The task is ready to proceed to developer documentation after Step 7 review.
