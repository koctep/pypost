# PYPOST-1358: Environment list widget worker crashes after passing assertions

## Goals

Maintainers and contributors rely on the Make quality gate (`make check` /
`make test`) to trust that environment list widget behavior is correct. Under
current and clean-baseline conditions, the focused environment list widget
suite can report all **thirteen** assertions as **PASSED**, then the native
test worker dies with a process-level crash (exit code −11 / SIGSEGV or −7 /
SIGBUS). No failing Python assertion and no Python traceback have been
observed; the Make runner then treats the file as failed because the worker
exited abnormally after the last PASS.

The defect is pre-existing and environment-sensitive: small samples on both
the current workspace and an isolated clean baseline show intermittent
post-PASS native termination. Root cause must not be inferred from the
signal alone; investigation must consider fixture and application lifetime
relative to native teardown among other evidence-backed hypotheses.

**Business goal**: restore a trustworthy quality signal for the environment
list widget suite by reproducing the native termination under bounded
conditions, eliminating the post-PASS native worker termination via whatever
evidence-backed root-cause correction investigation finds, and proving with
**five consecutive** successful isolated `WORKERS=1` Make invocations that all
thirteen assertions pass and the process exits 0—without weakening existing
assertions or timeouts.

**Implementation language**: Python.

## User Stories

- **US1 (maintainer, quality gate)**: As a maintainer running `make check` or
  `make test`, I want the environment list widget test file to finish with a
  normal worker exit after all tests pass, so that a green assertion set is
  not overturned by a silent native crash.
- **US2 (contributor, focused reruns)**: As a contributor running the focused
  environment list widget module through Make (including the documented
  single-worker reproduction), I want stable completion that matches CI
  expectations, so that local and gate results agree under the same
  conditions.
- **US3 (maintainer, evidence)**: As a maintainer, I want bounded
  reproduction of the post-PASS native worker termination, so that the
  defect class is confirmed without an unbounded flake hunt and without
  treating the crash signal alone as the root cause.
- **US4 (maintainer, trustworthy completion)**: As a maintainer, I want the
  post-PASS native worker termination eliminated by correcting the
  evidence-backed root cause found in investigation—whether that root cause
  is lifecycle/teardown relative to fixture and application lifetime or
  another confirmed cause—so the worker exits normally after green results.
  Dispose/DeferredDelete and related notes from PYPOST-1315 / PYPOST-1357 are
  investigative hypotheses only, not a design lock-in; a non-lifecycle root
  cause that removes the termination still satisfies this story.
- **US5 (maintainer, coverage integrity)**: As a maintainer, I want all
  existing environment list widget assertions and timeout markers retained
  (no skips, no weakened checks), so that fixing the crash does not trade
  stability for lost product coverage.
- **US6 (maintainer, repeated validation)**: As a maintainer, I want
  **five consecutive** successful isolated Make invocations of this suite
  (`make test WORKERS=1 PYTEST_ARGS='tests/test_environment_list_widget.py'`)
  each completing with all thirteen assertions passing and process exit 0, so
  that acceptance is not a single lucky run. Any unsuccessful run resets the
  consecutive counter; validation stops when five consecutive successes are
  achieved (no further runs required for Done).

## Definition of Done

1. **Crash reproduction.** The team has a bounded reproduction of the
   post-PASS native worker termination for the environment list widget suite
   (historically exit −11 / SIGSEGV and/or −7 / SIGBUS after all assertions
   pass)—without an unbounded flaky-hunt loop and without treating the
   signal alone as proof of a specific root cause.
2. **Post-PASS native termination eliminated.** Completing the thirteen
   environment list widget tests no longer ends in a native worker crash
   attributable to this defect. Acceptance is outcome-based: any
   evidence-backed root-cause correction that removes the termination
   satisfies Done. Lifecycle/teardown relative to fixture and application
   lifetime is an investigative hypothesis, not the only acceptable fix
   class; dispose/DeferredDelete notes (PYPOST-1315 / PYPOST-1357) are
   hypotheses only, not design lock-in. A confirmed non-lifecycle root cause
   that eliminates the termination still satisfies this criterion.
3. **Assertions preserved.** All existing assertions in the thirteen listed
   environment list widget tests remain; product behavior under test is not
   weakened or rewritten away to hide the crash.
4. **Timeout markers preserved.** Existing pytest timeout markers (per-test
   or module/class `pytestmark`) on those tests remain; stability is not
   achieved by removing or disabling timeout enforcement.
5. **No skips.** Validation does not rely on skipping the environment list
   widget tests.
6. **Bounded repeated isolated Make validation.** Acceptance validation is
   **exactly** five consecutive successful isolated Make invocations of:

   `make test WORKERS=1 PYTEST_ARGS='tests/test_environment_list_widget.py'`

   Each run must complete with all thirteen assertions passing and process
   exit 0 (no post-PASS native worker death). Any unsuccessful run resets
   the consecutive-success counter. Stop condition: once five consecutive
   successes are achieved, Done for this criterion is met and no further
   isolated runs are required. Full-suite / parallel `make check` (or
   parallel `make test`) success is **not** required for Done; Jira
   acceptance emphasizes these bounded repeated isolated `WORKERS=1`
   invocations.
7. **Related-ticket clarity.** Relationship to PYPOST-1315 / PYPOST-1357
   (shared vs distinct lifetime/teardown class) is recorded when evidence
   supports a conclusion; shared-cause handling is allowed only with
   explicit evidence.
8. **Repository gates.** Quality gates for this task’s accepted validation
   are exercised only through `make` targets. Done for PYPOST-1358 is the
   isolated `WORKERS=1` streak in criterion 6; a green full/parallel
   `make check` is desirable context (see US1) but is not an acceptance
   gate for this ticket. No new failures attributable to this task remain
   in those accepted isolated validation runs.

## Task Description

### Problem

The environment list widget automated suite can report thirteen PASSes and
then have its native test worker die (exit_code=−11 / SIGSEGV or −7 /
SIGBUS) with no crash traceback. The Make summary then shows the file as
failed even though every assertion passed. Evidence from discovery:

- Reproduction command used in the ticket:

  `make test WORKERS=1 PYTEST_ARGS='tests/test_environment_list_widget.py'`

- Current workspace and clean baseline at commit `1e64239f` (path
  `/tmp/pypost1348-baseline`) each use their own Make-managed environment;
  reported runtime context includes Python 3.13.5, PySide6 6.11.1, pytest
  8.4.2, offscreen Qt via Make.
- Current full gate and focused repeats: worker exit −11 or −7 after all
  thirteen assertions passed (observed 3/3 native crashes on the current
  sample).
- Clean baseline: one successful worker exit 0, then exits −7 and −11 after
  all thirteen passed (2/3 native crashes on that sample)—establishing
  pre-existing flakiness, not a stable crash probability estimate.
- Scope charter: pre-existing environment-sensitive native worker
  termination after assertions pass; investigate fixture/application
  lifetime and native teardown among other hypotheses; do not infer root
  cause from the signal alone.
- May relate to PYPOST-1315 / PYPOST-1357 dispose/lifetime patterns; that
  relation is investigative context and hypothesis only, not a design
  mandate or the only acceptable fix class.

Exact environment list widget identifiers in scope for coverage retention
(file `tests/test_environment_list_widget.py`):

- `TestImportEnvironments`:
  - `test_happy_path_adds_environments_and_shows_success`
  - `test_cancelled_file_picker_leaves_environments_unchanged`
  - `test_invalid_file_shows_error_and_leaves_environments_unchanged`
  - `test_zero_candidates_treated_as_invalid_file`
  - `test_conflict_prompts_once_per_conflicting_name`
  - `test_apply_to_all_conflicts_prompts_only_once`
  - `test_apply_to_all_conflicts_applies_to_third_and_later_conflicts`
  - `test_apply_to_all_conflicts_applies_overwrite_to_third_and_later_conflicts`
  - `test_apply_to_all_conflicts_applies_keep_both_to_third_and_later_conflicts`
  - `test_partial_parse_failure_still_imports_valid_entries`
  - `test_no_read_import_file_callable_is_noop`
  - `test_logs_completed_event_with_counts`
- `TestImportButtonWiring`:
  - `test_mouse_click_on_import_button_starts_import`

### Business reason

A quality gate that fails after every assertion has already passed is a
false signal. It blocks delivery, burns investigation time, and undermines
trust in environment list widget coverage and Make-based CI. The business
need is stable, honest proof that environment list import/list UI behavior
still holds—not a workaround that drops tests, softens timeouts, or
declares victory from a single non-crashing run while flakiness remains.

### Implementation language

Python.

### Scope

- Reproduce the post-PASS native worker termination under bounded
  conditions for the environment list widget suite.
- Eliminate that termination via whatever evidence-backed root-cause
  correction investigation finds (lifecycle/teardown is a hypothesis, not
  a mandated sole solution).
- Retain all listed environment list widget assertions and timeout markers.
- Validate Done with **five consecutive** successful isolated
  `WORKERS=1` Make invocations showing all thirteen assertions passing and
  process exit 0 (see Definition of Done #6); full/parallel `make check`
  success is not required for Done.
- Clarify relationship to PYPOST-1315 / PYPOST-1357 when evidence supports
  shared vs distinct cause.

### Out of scope

- Changing environment list / import product behavior beyond what is
  required to correct the identified root cause of the post-PASS native
  termination.
- Removing, skipping, or rewriting away the thirteen environment list
  widget tests (or their timeout markers) as a substitute for a fix.
- Broad redesign of the entire UI test harness or global worker policy
  unrelated to this defect.
- Inferring and locking a root cause from the crash signal alone without
  evidence-based investigation (including lifetime/teardown hypotheses).
- Mandating a lifecycle/teardown-only solution, or locking design to
  dispose/DeferredDelete patterns from PYPOST-1315 / PYPOST-1357, when
  evidence points elsewhere.
- Re-litigating or re-implementing PYPOST-1315 / PYPOST-1357 scopes except
  where shared-cause evidence requires coordinated handling.
- Requiring a green full-suite or parallel `make check` / parallel
  `make test` as an acceptance gate for this ticket (Done is the isolated
  `WORKERS=1` streak only).
- Unrelated failures elsewhere in the full suite that are not caused by
  this defect.
- Claiming a fixed crash probability from the small discovery samples.

### Constraints and assumptions

- Work is Jira-driven (PYPOST-1358); Debt issue; estimate 5 story points
  for full Steps 1–8.
- Labels include `failing-test` and `tech-debt`.
- Sprint context: Worker Shutdown & UI Stability.
- All build/test/lint operations go through `make` targets only.
- Crash evidence is environment-sensitive and pre-existing on clean
  baseline; acceptance requires bounded reproduction and **five consecutive**
  successful isolated `WORKERS=1` Make runs—not a claim that every host
  crashes on every run, and not a requirement that full/parallel gates pass
  for Done.
- Notes about fixture/application lifetime, native teardown, and possible
  relation to dispose/DeferredDelete patterns on PYPOST-1315 / PYPOST-1357
  are investigative hypotheses from the ticket, not a design mandate; a
  non-lifecycle root cause that eliminates post-PASS native termination
  still satisfies Done. Later steps refine the defect once evidence is in
  hand.
- Assumption: the thirteen listed nodes are the contracted coverage set for
  retention and acceptance validation.
- Assumption: “bounded repeated isolated Make success” means five
  consecutive successes of the ticket reproduction command; the consecutive
  counter resets on any unsuccessful run; validation stops when the streak
  is met.

### Main entities (business domain)

- **Environment list widget capability**: user-facing ability to import and
  manage environments in the list UI (happy path, cancellation, invalid
  input, conflict handling, partial failure, logging, import button
  wiring)—already covered by the thirteen tests; must keep that coverage.
- **Quality gate / Make run**: the maintainer-facing proof path that must
  end with an honest pass/fail, not a post-PASS native worker death. For
  this ticket’s Done, the contracted proof path is the isolated
  `WORKERS=1` focused suite (five consecutive successes).
- **Test worker process**: the process that executes the UI tests; after
  tests complete it must exit normally when assertions passed.
- **Post-PASS native termination defect**: the business-facing defect where
  the worker dies after green environment list widget results; root cause
  is subject to confirmation and is not locked to lifecycle/teardown.
- **Related lifetime tickets (PYPOST-1315 / PYPOST-1357)**: adjacent
  export-UI / dispose-lifetime crash classes; treated as related
  investigative hypotheses unless evidence shows a shared cause requiring
  coordinated handling.

### Non-functional requirements

- **Reliability**: **five consecutive** isolated `WORKERS=1` Make
  validations for the environment list widget suite complete without
  post-PASS native worker crashes attributable to this defect; full/parallel
  gate success is not an NFR acceptance bar for this ticket.
- **Integrity of coverage**: no loss of assertions or timeout enforcement
  for the thirteen listed environment list widget tests.
- **Operability**: evidence and validation remain runnable through existing
  Make workflows with bounded effort (no ad-hoc, unbounded flake hunting as
  the only proof); stop when the five-consecutive streak is met.
- **Honesty of signal**: a PASSED test file must not be reported as a
  file-level failure solely because the worker died after the last PASS for
  this defect.
- **Cause transparency**: acceptance does not treat the crash signal alone
  as the root cause, does not lock the fix class to lifecycle/teardown or
  dispose/DeferredDelete, and records relation to PYPOST-1315 / PYPOST-1357
  when evidence warrants it. Any evidence-backed correction that eliminates
  the termination satisfies Done.

## Q&A

- **Q: Why is this a business/requirements issue if the symptom is a native
  crash in tests?**
  **A:** The business asset at risk is trustworthy delivery proof.
  Post-PASS worker death makes Make results unusable for deciding whether
  environment list widget behavior is safe to ship.

- **Q: Why not skip or quarantine the flaky file until later?**
  **A:** Acceptance explicitly requires retaining assertions and validating
  without skips. Quarantine would hide coverage for a core environment
  import/list workflow.

- **Q: Is this the same work as PYPOST-1315 or PYPOST-1357?**
  **A:** No by ticket charter: PYPOST-1358 owns the environment list widget
  post-PASS native termination. PYPOST-1315 and PYPOST-1357 own related
  export-UI / dispose-lifetime crash classes. They may share a
  lifetime/teardown pattern; shared-cause handling is allowed only when
  evidence supports it, and must be recorded explicitly. Their
  dispose/DeferredDelete notes remain hypotheses for this ticket, not
  design lock-in.

- **Q: Must the crash reproduce on every current host before a fix is
  allowed?**
  **A:** No. Acceptance asks for bounded reproduction of the native
  termination, then evidence-backed correction validated by five consecutive
  isolated `WORKERS=1` Make runs with exit 0—not a guarantee of 100% live
  reproduction on every host.

- **Q: Does “fixture/QApplication lifetime”, SIGSEGV/SIGBUS, or
  dispose/DeferredDelete dictate the solution?**
  **A:** No. Those notes are investigative hypotheses only. Requirements
  mandate not inferring root cause from the signal alone, eliminating the
  post-PASS native termination via whatever evidence-backed root cause is
  found, and validating with isolated Make; a non-lifecycle root cause still
  satisfies Done. Design choices belong in later steps.

- **Q: What is the numerical bound for “bounded repeated” isolated Make
  success?**
  **A:** Five consecutive successful invocations of
  `make test WORKERS=1 PYTEST_ARGS='tests/test_environment_list_widget.py'`,
  each with all thirteen assertions PASS and process exit 0. Any
  unsuccessful run resets the consecutive counter. Stop condition: when five
  consecutive successes are achieved, validation for Done stops (no further
  isolated runs required).

- **Q: Is a green full/parallel `make check` (or parallel `make test`)
  required for Done?**
  **A:** No. Jira acceptance emphasizes bounded repeated isolated Make
  invocations. Done requires only the five-consecutive isolated
  `WORKERS=1` streak (Definition of Done #6). Full/parallel gate success is
  desirable maintainer context (US1) but is not an acceptance gate for this
  ticket.

- **Q: Why “bounded repeated” isolated Make runs rather than a single
  green run?**
  **A:** Discovery showed pre-existing flakiness (including exit 0 then
  native death on clean baseline). A single lucky exit 0 is not enough to
  restore trust; acceptance requires five consecutive isolated successes.

- **Q: Links**
  - Issue: [PYPOST-1358](https://pypost.atlassian.net/browse/PYPOST-1358)
  - Related:
    [PYPOST-1315](https://pypost.atlassian.net/browse/PYPOST-1315),
    [PYPOST-1357](https://pypost.atlassian.net/browse/PYPOST-1357)
  - Baseline referenced in evidence: `1e64239f` at
    `/tmp/pypost1348-baseline`
