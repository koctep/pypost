# PYPOST-1357: Collection export UI worker crashes after all assertions pass

## Goals

Maintainers and contributors rely on the Make quality gate (`make check` /
`make test`) to trust that collection export UI behavior is correct. During
planning for PYPOST-1336, a failure mode appeared where all nineteen collection
export UI tests (non-slow marker set) report **PASSED**, then the native test
worker dies with a process-level crash (exit code −11 / SIGSEGV). The suite
itself shows no failing assertion and no Python traceback; the Make runner then
treats the file as failed because the worker exited abnormally after the last
PASS.

The defect is environment-sensitive: under an affected dependency mix the
focused single-worker run crashes after green results; after a dependency
refresh the same focused module and an isolated clean baseline can pass with a
normal worker exit. Original dependency versions were not fully captured.
Root cause has not been investigated; teardown after the last test is only a
working suspicion. The ticket treats this as distinct from the environment
export UI dispose issue tracked by PYPOST-1315, while noting it may belong to
the same broad lifetime/teardown class.

**Business goal**: restore a trustworthy quality signal for the collection
export UI suite by obtaining a reproducible crash or a diagnostic crash
artifact under affected conditions, identifying whether the cause is teardown
behavior or the test environment, fixing the identified cause without weakening
existing assertions or timeouts, and proving focused and parallel Make runs
complete without post-PASS worker death.

**Implementation language**: Python.

## User Stories

- **US1 (maintainer, quality gate)**: As a maintainer running `make check` or
  `make test`, I want the collection export UI test file to finish with a
  normal worker exit after all tests pass, so that a green assertion set is not
  overturned by a silent native crash.
- **US2 (contributor, focused reruns)**: As a contributor running the focused
  collection export UI module through Make (including the documented
  single-worker reproduction), I want stable completion that matches CI
  expectations, so that local and gate results agree under the same conditions.
- **US3 (maintainer, evidence)**: As a maintainer, I want either a bounded
  reproduction of the post-PASS crash under affected conditions or a captured
  diagnostic crash artifact, so that the cause can be identified and the fix
  justified without an unbounded flake hunt.
- **US4 (maintainer, cause clarity)**: As a maintainer, I want a clear
  determination of whether the failure is driven by teardown behavior, by the
  test environment (dependency mix), or by both, so that remediation addresses
  the real cause and is not confused with PYPOST-1315 unless evidence shows a
  shared defect.
- **US5 (maintainer, coverage integrity)**: As a maintainer, I want all existing
  collection export UI assertions and timeout markers retained (no skips, no
  weakened checks), so that fixing the crash does not trade stability for lost
  product coverage.
- **US6 (maintainer, validation breadth)**: As a maintainer, I want both focused
  and parallel Make validations to complete successfully for this suite, so that
  the gate remains honest under normal project worker layouts.

## Definition of Done

1. **Crash evidence.** The team has either a bounded reproduction of the
   post-PASS native worker crash under affected conditions, or a captured
   diagnostic crash artifact sufficient to confirm the defect class—without an
   unbounded flaky-hunt loop.
2. **Cause identified.** Investigation identifies whether the failure is caused
   by teardown behavior, by the test environment (including dependency
   versions), or by an interaction of both, and records that conclusion clearly
   relative to PYPOST-1315 (shared vs distinct).
3. **Defect resolved.** The identified cause is remediated so that completing
   the nineteen collection export UI tests does not leave the worker in a state
   that ends in a native crash attributable to this defect.
4. **Assertions preserved.** All existing assertions in the nineteen listed
   collection export UI tests remain; product behavior under test is not
   weakened or rewritten away to hide the crash.
5. **Timeout markers preserved.** Existing pytest timeout markers (per-test or
   module/class `pytestmark`) on those tests remain; stability is not achieved
   by removing or disabling timeout enforcement.
6. **No skips.** Validation does not rely on skipping the collection export UI
   tests.
7. **Focused Make validation.** Focused Make runs of the collection export UI
   suite (including forms equivalent to the ticket’s single-worker reproduction)
   complete successfully with a normal worker exit (no post-PASS native crash).
8. **Parallel Make validation.** Parallel Make runs used for acceptance
   complete without the collection export UI file failing via worker exit −11
   (or equivalent native death) after all tests in that file have passed.
9. **Repository gates.** Quality gates are exercised only through `make`
   targets; no new failures attributable to this task remain in the accepted
   validation runs.

## Task Description

### Problem

The collection export UI automated suite can report nineteen PASSes and then
have its native test worker die (exit_code=−11 / SIGSEGV) with no crash
traceback. The Make summary then shows the file as failed (Passed: 0 /
Failed: 1) even though every assertion passed. Evidence from discovery:

- Original full `make test` and two focused pre-refresh runs crashed after all
  nineteen assertions passed (3/3 crashes on the affected environment).
- Reproduction command used in the ticket:

  `make test WORKERS=1 PYTEST_ARGS='tests/test_collection_export_ui.py -m "not slow"'`

- Isolated clean baseline at commit
  `31f2b25a1fcacf490c5136c25ac4dac57ec41b06` passes for this UI module.
- After environment restore via `make install` (reported restored versions:
  PySide6 6.11.1 and pydantic 2.14.0; originals not fully captured), focused
  current runs and the isolated baseline module pass with worker exit 0.
- Found during planning-only PYPOST-1336; no production or test changes were
  made for this defect in that work.
- Ticket states the issue is distinct from PYPOST-1315 (environment export UI
  dispose) but may relate to the same lifetime/teardown patterns.

Exact collection export UI identifiers in scope for coverage retention
(file `tests/test_collection_export_ui.py`):

- `TestExportCollectionEntryPoint`:
  - `test_panel_exposes_an_identified_export_button_wired_to_the_flow`
  - `test_panel_exposes_export_all_button_wired_to_the_flow`
- `TestExportCollection`:
  - `test_happy_path_exports_selected_collection_and_shows_success`
- `TestExportAllCollections`:
  - `test_all_export_one_collection_writes_object_root`
  - `test_exports_every_collection_without_a_tree_selection`
  - `test_logs_completion_with_safe_all_export_counts`
  - `test_empty_library_exports_valid_empty_backup`
  - `test_cancelled_all_export_does_not_serialize_or_write`
  - `test_all_export_write_failure_shows_error_dialog`
  - `test_cancelled_save_dialog_leaves_files_unchanged`
  - `test_no_tree_selection_shows_error`
  - `test_request_selection_exports_parent_collection`
  - `test_write_failure_shows_error_dialog`
  - `test_no_serialize_callable_is_noop`
  - `test_logs_completed_event`
- `TestExportCollectionSourcePrecedence`:
  - `test_source_index_pointing_to_collection_overrides_distant_current_index`
  - `test_source_index_pointing_to_child_request_exports_its_parent_collection`
  - `test_export_without_source_index_defaults_to_current_index`
  - `test_presenter_export_collection_at_index_forwards_source_index`

### Business reason

A quality gate that fails after every assertion has already passed is a false
signal. It blocks delivery, burns investigation time, and undermines trust in
collection export UI coverage and Make-based CI. The business need is stable,
honest proof that collection export UI behavior still holds—not a workaround
that drops tests, softens timeouts, or ignores environment-only crashes that
still break contributor and CI workflows under affected conditions.

### Implementation language

Python.

### Scope

- Reproduce the post-PASS native worker crash under affected conditions, or
  capture a diagnostic crash artifact when live reproduction is not available.
- Identify whether the cause is teardown behavior, test environment
  (dependency mix), or both; clarify relationship to PYPOST-1315.
- Remediate the identified cause so the worker exits normally after the
  nineteen green tests.
- Retain all listed collection export UI assertions and timeout markers.
- Validate with focused and parallel Make runs without skips.

### Out of scope

- Changing collection export product behavior beyond what is required to
  correct the identified crash cause.
- Removing, skipping, or rewriting away the nineteen collection export UI
  tests (or their timeout markers) as a substitute for a fix.
- Broad redesign of the entire UI test harness or global worker policy
  unrelated to this defect.
- Treating environment restore alone as the “fix” while leaving a proven
  teardown defect unaddressed, if evidence shows such a defect remains.
- Re-litigating or re-implementing PYPOST-1315’s environment export UI scope
  except where shared-cause evidence requires coordinated handling.
- Unrelated failures elsewhere in the full suite that are not caused by this
  defect.

### Constraints and assumptions

- Work is Jira-driven (PYPOST-1357); Debt issue; estimate 5 story points for
  full Steps 1–8.
- Labels include `failing-test` and `tech-debt`.
- Sprint context: Worker Shutdown & UI Stability.
- All build/test/lint operations go through `make` targets only.
- Crash evidence is environment-sensitive; acceptance allows either bounded
  reproduction under affected conditions or a diagnostic crash artifact—not a
  claim that every current host will crash on every run.
- “Likely teardown” and possible relation to dispose/DeferredDelete patterns
  are investigative context from the ticket, not a design mandate; later steps
  refine the defect once evidence is in hand.
- Assumption: the nineteen listed nodes (non-slow set) are the contracted
  coverage set; slow-marked tests in the same file are outside mandatory
  retention unless they share the same crash cause and are pulled into
  validation explicitly.

### Main entities (business domain)

- **Collection export UI capability**: user-facing ability to export one or all
  collections (entry points, selection rules, success/error feedback,
  cancellation, logging)—already covered by the nineteen tests; must keep that
  coverage.
- **Quality gate / Make run**: the maintainer-facing proof path that must end
  with an honest pass/fail, not a post-PASS native worker death.
- **Test worker process**: the process that executes the UI tests; after tests
  complete it must exit normally when assertions passed.
- **Affected test environment**: the dependency/runtime mix under which the
  crash was observed; must be characterized enough to support evidence or a
  durable fix.
- **Teardown / lifetime defect (suspected)**: the business-facing defect class
  where work associated with collection export UI tests is not released safely
  relative to process end, producing a native crash after green results—subject
  to confirmation.
- **Related environment export UI issue (PYPOST-1315)**: adjacent export UI
  crash class; treated as distinct unless evidence shows a shared cause.

### Non-functional requirements

- **Reliability**: focused and parallel Make validations for the collection
  export UI suite complete without post-PASS native worker crashes attributable
  to this defect.
- **Integrity of coverage**: no loss of assertions or timeout enforcement for
  the nineteen listed collection export UI tests.
- **Operability**: evidence and validation remain runnable through existing Make
  workflows with bounded effort (no ad-hoc, unbounded flake hunting as the only
  proof).
- **Honesty of signal**: a PASSED test file must not be reported as a file-level
  failure solely because the worker died after the last PASS for this defect.
- **Cause transparency**: the accepted outcome states whether remediation
  addressed teardown, environment, or both, so future triage does not confuse
  this ticket with PYPOST-1315 without evidence.

## Q&A

- **Q: Why is this a business/requirements issue if the symptom is a native
  crash in tests?**
  **A:** The business asset at risk is trustworthy delivery proof. Post-PASS
  worker death makes Make results unusable for deciding whether collection
  export UI is safe to ship.

- **Q: Why not skip or quarantine the flaky file until later?**
  **A:** Acceptance explicitly requires retaining assertions and validating
  without skips. Quarantine would hide coverage for a core export workflow.

- **Q: Is this the same work as PYPOST-1315?**
  **A:** No by ticket charter: PYPOST-1357 owns the collection export UI
  post-PASS crash under affected environments. PYPOST-1315 owns the environment
  export UI dispose/crash class. They may share a lifetime/teardown pattern;
  shared-cause handling is allowed only when evidence supports it, and must be
  recorded explicitly.

- **Q: Must the crash reproduce on every current host before a fix is allowed?**
  **A:** No. Acceptance asks for reproduction under affected conditions *or* a
  diagnostic crash artifact, then a cause identification and a fix validated by
  focused and parallel Make runs—not a guarantee of 100% live reproduction on
  every restored environment.

- **Q: Does “likely teardown” or dispose/DeferredDelete dictate the solution?**
  **A:** No. Those notes are investigative context. Requirements only mandate
  identifying the teardown/environment cause and remediating it; design choices
  belong in later steps.

- **Q: Links**
  - Issue: [PYPOST-1357](https://pypost.atlassian.net/browse/PYPOST-1357)
  - Discovered during: [PYPOST-1336](https://pypost.atlassian.net/browse/PYPOST-1336)
  - Related distinct ticket:
    [PYPOST-1315](https://pypost.atlassian.net/browse/PYPOST-1315)
  - Baseline commit referenced in evidence: `31f2b25a1fcacf490c5136c25ac4dac57ec41b06`
