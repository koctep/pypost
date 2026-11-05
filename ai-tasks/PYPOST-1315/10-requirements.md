# PYPOST-1315: Flaky environment export UI worker segfaults after all tests pass

## Goals

Maintainers and contributors rely on the Make quality gate (`make check` / `make test`) to
trust that environment export UI behavior is correct. During PYPOST-1266, a flaky failure
appeared where all eight environment export UI tests report **PASSED**, then the native test
worker dies with a process-level crash (exit code −11 / SIGSEGV). No product or test changes
were made to that module in that task; focused single-file reruns often pass, while full or
parallel suite runs fail intermittently.

That pattern makes the gate unreliable: green assertions are contradicted by a worker death
after the last PASS line, with no Python traceback. Time is lost triaging false failures,
real regressions are harder to spot, and confidence in the environment export UI suite drops.
A related symptom has been seen on collection export UI tests under disk pressure (same class
of native crash after or around otherwise green results).

**Business goal**: restore a trustworthy quality signal for environment export UI (and the
same lifetime/teardown defect class where it also hits collection export UI) by obtaining
bounded reproducible native-crash evidence, removing the defect that kills the worker after
tests pass, keeping every existing assertion and timeout marker, and proving focused and
parallel Make runs complete without skips or post-PASS worker crashes.

**Implementation language**: Python.

## User Stories

- **US1 (maintainer, quality gate)**: As a maintainer running `make check` or parallel
  `make test`, I want the environment export UI test file to finish with a normal worker exit
  after all tests pass, so that a green suite is not overturned by a silent native crash.
- **US2 (contributor, focused reruns)**: As a contributor running focused environment export
  UI tests through Make, I want the same stable completion as in the full suite, so that
  local and CI results agree and I am not chasing environment-only flakes.
- **US3 (maintainer, evidence)**: As a maintainer, I want bounded, reproducible evidence that
  the native crash is (or was) attributable to a lifetime/teardown defect in this area, so
  that the fix is justified and regressions can be recognized if the crash returns.
- **US4 (maintainer, coverage integrity)**: As a maintainer, I want all existing environment
  export UI assertions and timeout markers retained (no skips, no weakened checks), so that
  fixing the crash does not trade stability for lost product coverage.
- **US5 (maintainer, related export UI)**: As a maintainer, when the same lifetime/teardown
  defect also causes collection export UI worker crashes under load or disk pressure, I want
  that path covered by the same fix class so we do not leave a twin flake open after closing
  the environment export case.

## Definition of Done

1. **Bounded crash evidence.** The team has bounded, reproducible evidence of the native
   worker crash associated with the environment export UI suite (post-PASS worker death with
   the historically observed exit class), sufficient to confirm the defect before and/or
   validate absence after the fix—without requiring an unbounded flaky-hunt loop.
2. **Lifetime/teardown defect resolved.** The identified lifetime/teardown defect that causes
   the worker to die after the environment export UI tests have passed is fixed. After the
   fix, completing those tests must not leave the worker in a state that ends in a native
   crash attributable to that defect.
3. **Assertions preserved.** All existing assertions in the eight environment export UI
   tests remain; product behavior under test is not weakened or rewritten away to hide the
   crash.
4. **Timeout markers preserved.** Existing pytest timeout markers (per-test or module/class
   `pytestmark`) on those tests remain; stability is not achieved by removing or disabling
   timeout enforcement.
5. **No skips.** Validation does not rely on skipping the environment export UI tests (or
   the related collection export UI cases when they are in the validation set for the same
   defect).
6. **Focused Make validation.** Focused Make runs of the environment export UI tests
   complete successfully with a normal worker exit (no post-PASS native crash).
7. **Parallel / full-gate Make validation.** Parallel or full-suite Make runs used for
   acceptance (including forms equivalent to `make check` with the project’s normal worker
   timeout) complete without the environment export UI file failing via worker exit −11 (or
   equivalent native death) after all tests in that file have passed.
8. **Related collection export path (same defect).** If investigation shows the same
   lifetime/teardown defect drives the collection export UI native crashes noted on this
   issue, that path is included in the fix and validation so the twin flake is not left
   open. If evidence shows a distinct root cause, that remainder is documented as out of
   scope or follow-up debt rather than silently ignored.
9. **Repository gates.** Quality gates are exercised only through `make` targets; no new
   failures attributable to this task remain in the accepted validation runs.

## Task Description

### Problem

The environment export UI automated suite can report eight PASSes and then have its native
test worker die (historically exit_code=−11 / SIGSEGV; related runs have also seen SIGBUS)
with no crash traceback. Focused single-file runs often exit 0; failures appear under higher
parallel load or environmental pressure (e.g. disk pressure for the related collection export
UI file). Classification is flaky by unchanged-tree rerun evidence, not a claim of a
deterministic single-run baseline failure.

Exact environment export UI identifiers in scope for coverage retention:

- `tests/test_environment_export_ui.py::TestExportEnvironments::test_single_environment_export_writes_object_root`
- `tests/test_environment_export_ui.py::TestExportEnvironments::test_happy_path_exports_all_and_shows_success`
- `tests/test_environment_export_ui.py::TestExportEnvironments::test_cancelled_scope_leaves_files_unchanged`
- `tests/test_environment_export_ui.py::TestExportEnvironments::test_selected_scope_without_selection_shows_error`
- `tests/test_environment_export_ui.py::TestExportEnvironments::test_hidden_values_require_confirmation`
- `tests/test_environment_export_ui.py::TestExportEnvironments::test_cancelled_secrets_confirmation_skips_write`
- `tests/test_environment_export_ui.py::TestExportEnvironments::test_no_serialize_callable_is_noop`
- `tests/test_environment_export_ui.py::TestExportEnvironments::test_logs_completed_event`

Related observation (same issue comment): `tests/test_collection_export_ui.py` workers have
crashed with the same native-signal class under disk pressure; environment-dependent, not
proven as a separate product regression.

### Business reason

A quality gate that fails after every assertion has already passed is a false signal. It
blocks delivery, burns investigation time, and undermines trust in both the environment
export UI coverage and Make-based CI. The business need is stable, honest proof that export
UI behavior still holds—not a workaround that drops tests or softens timeouts.

### Implementation language

Python.

### Scope

- Obtain bounded reproducible evidence of the post-PASS native worker crash for the
  environment export UI suite (and, when the same defect applies, the related collection
  export UI symptom).
- Fix the identified lifetime/teardown defect responsible for that crash class.
- Retain all listed environment export UI assertions and timeout markers.
- Validate with focused and parallel Make runs without skips.
- Include collection export UI in the fix/validation set when it shares the same defect;
  otherwise record distinct-cause remainder explicitly.

### Out of scope

- Changing environment or collection export product behavior beyond what is required to
  correct the lifetime/teardown defect that kills the worker.
- Removing, skipping, or rewriting away the eight environment export UI tests (or their
  timeout markers) as a substitute for a fix.
- Broad redesign of the entire UI test harness or global worker policy unrelated to this
  defect.
- Treating disk-pressure infrastructure alone as the “fix” while leaving a proven shared
  lifetime/teardown defect unaddressed.
- Unrelated failures elsewhere in the full suite that are not caused by this defect.

### Constraints and assumptions

- Work is Jira-driven (PYPOST-1315); estimate 5 story points for full Steps 1–8.
- Found during PYPOST-1266; labels include `failing-test` and `tech-debt`.
- Sprint context: Worker Shutdown & UI Stability.
- All build/test/lint operations go through `make` targets only.
- Crash evidence may be intermittent; acceptance requires *bounded* reproducibility, not an
  infinite flake campaign.
- Suspected class (ownership/lifetime under teardown or load) is a working hypothesis from
  the ticket, not a design mandate; Step 2+ may refine the defect once evidence is in hand.

### Main entities (business domain)

- **Environment export UI capability**: user-facing ability to export environments (scope,
  secrets confirmation, success/error feedback, logging of completion)—already covered by
  the eight tests; must keep that coverage.
- **Quality gate / Make run**: the maintainer-facing proof path that must end with a honest
  pass/fail, not a post-PASS native worker death.
- **Test worker process**: the process that executes the UI tests; after tests complete it
  must exit normally when assertions passed.
- **Lifetime/teardown defect**: the business-facing defect class where objects or work
  associated with export UI tests are not released safely relative to process end, producing
  a native crash after green results.
- **Related collection export UI suite**: adjacent export UI coverage that has shown the same
  native-crash symptom under pressure; in scope when the same defect applies.

### Non-functional requirements

- **Reliability**: focused and parallel Make validations for the in-scope suites complete
  without post-PASS native worker crashes attributable to this defect.
- **Integrity of coverage**: no loss of assertions or timeout enforcement for the eight
  environment export UI tests.
- **Operability**: evidence and validation remain runnable through existing Make workflows
  with bounded effort (no ad-hoc, unbounded flake hunting as the only proof).
- **Honesty of signal**: a PASSED test file must not be reported as a file-level failure
  solely because the worker died after the last PASS for this defect.

## Q&A

- **Q: Why is this a business/requirements issue if the symptom is a native crash in tests?**
  **A:** The business asset at risk is trustworthy delivery proof. Post-PASS worker death
  makes Make results unusable for deciding whether environment export UI is safe to ship.

- **Q: Why not skip or quarantine the flaky file until later?**
  **A:** Acceptance explicitly requires retaining assertions and validating without skips.
  Quarantine would hide coverage for a core export workflow.

- **Q: Is collection export UI mandatory scope?**
  **A:** Environment export UI is the primary contracted scope. Collection export UI is in
  scope when it shares the same lifetime/teardown defect; if evidence shows a separate cause,
  that remainder is called out rather than assumed fixed.

- **Q: Must the crash reproduce on every run before a fix is allowed?**
  **A:** No. Acceptance asks for *bounded* reproducible evidence and then a fix validated by
  focused and parallel Make runs—not a guarantee of 100% historical reproduction rate.

- **Q: Does “suspected Qt ownership/teardown” dictate the solution?**
  **A:** No. That note is investigative context from the ticket. Requirements only mandate
  fixing the identified lifetime/teardown defect once evidence pins it; design choices belong
  in later steps.

- **Q: Links**
  - Issue: [PYPOST-1315](https://pypost.atlassian.net/browse/PYPOST-1315)
  - Discovered during: [PYPOST-1266](https://pypost.atlassian.net/browse/PYPOST-1266)
  - Related comment evidence also references work around
    [PYPOST-1334](https://pypost.atlassian.net/browse/PYPOST-1334) (collection export UI
    crashes under disk pressure)
