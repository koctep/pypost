# PYPOST-1002: Technical Debt Analysis

## Holistic Self-Review Against Step 1 Definition of Done

Re-checking the shipped diff (`tests/test_environment_list_widget.py` +32
lines, `tests/test_environment_import.py` +6 lines, zero production changes;
`git diff --stat` confirms only these two files) against every DoD bullet in
`ai-tasks/PYPOST-1002/10-requirements.md`:

1. "A new test proves 'apply to all' is honored across three or more
   conflicting names ... prompt shown exactly once ... every conflicting
   name — including the third one — receives the same decision" — met:
   `test_apply_to_all_conflicts_applies_to_third_and_later_conflicts`
   (`tests/test_environment_list_widget.py:146-177`) imports three colliding
   names ("Dev", "Prod", "Staging"), asserts
   `mock_prompt_conflict.assert_called_once()`, and asserts all three
   `envs[i].variables` are unchanged under SKIP, including `envs[2]`
   ("Staging") — the assertion that actually distinguishes "loops over all
   remaining conflicts" from "carries the decision to exactly one more."
2. "A new test proves `generate_import_copy_name` reaches a `(3)` suffix" —
   met: `test_returns_next_numbered_copy_when_first_two_taken`
   (`tests/test_environment_import.py:151-155`) seeds
   `{"Copy of Dev", "Copy of Dev (2)"}` and asserts the result is
   `"Copy of Dev (3)"`.
3. "Both new tests are ... functional (pytest) tests ... must fail if the
   loop under test is truncated, off-by-one, or short-circuited" — verified
   directly in Step 3's review: the reviewing subagent temporarily broke
   each underlying loop (apply-to-all carry, SKIP-mutates-state, and the
   copy-name generator's `while`→`if`) and confirmed each targeted new test
   failed, then reverted (`pypost/` diff confirmed clean afterward). Not
   just inspection — actually exercised.
4. "Both new tests follow existing project and file conventions ... live in
   the same test files/classes as their two-way/`(2)` siblings ... inherit
   the module-level `pytest.mark.timeout(60)`" — met: both new methods sit
   in `TestImportEnvironments` / `TestGenerateImportCopyName` immediately
   after their named siblings; both files declare
   `pytestmark = pytest.mark.timeout(60)` at module scope (line 5 and line
   10 respectively, confirmed again this step), which the new methods
   inherit with no per-test override needed — satisfies the BLOCKER-class
   timeout rule in `.cursor/lsr/do-testing.md`.
5. "No existing test's behavior or assertions change unless a genuine
   defect is found and fixed" — met: `git diff` shows pure addition (0
   deletions in both files); no existing test method's body changed. No
   defect was found in either loop (both new assertions passed immediately
   against current code — a verification lock, same pattern as sibling
   PYPOST-1001), so DoD item 5's fix/record branch does not apply.
6. Out-of-scope list (2-conflict case, `(2)` case, invalid-file,
   zero-candidates, Overwrite × encryption cache / PYPOST-999,
   `EnvPresenter` wiring / PYPOST-1000, Import… button / PYPOST-1001, any
   production/UI/on-disk-format change) — respected: no production file was
   touched (`git diff --stat -- pypost/` empty, reconfirmed this step); no
   other test file was modified.

No gap found between the delivered diff and the Step 1 scope/DoD. Full
targeted re-run this step: `.venv/bin/python -m pytest
tests/test_environment_list_widget.py tests/test_environment_import.py -q`
→ 26 passed, 0 failed (reconfirmed independently of the Step 4/5 runs).

**Parent ticket closure check (informational only).** PYPOST-1002 is
Follow-up Task 4 of 4 in `ai-tasks/PYPOST-986/60-tech-debt.md`'s "Follow-up
Tasks" list (that list has exactly four entries, each already carrying a
Jira link — not five *additional* entries beyond this one, so the count
below is three others, not five):

1. PYPOST-999 (Overwrite × ciphertext-reuse-cache round trip) — roadmap
   shows all 8 steps `[x]`, closed.
2. PYPOST-1000 (`EnvPresenter`-level `read_import_file` wiring test) —
   roadmap shows all 8 steps `[x]`, closed.
3. PYPOST-1001 (Import… button click wiring) — roadmap shows all 8 steps
   `[x]`, closed.
4. PYPOST-1002 (this ticket, the two combinatorial gaps) — being closed by
   this Step 7/8.

All four of PYPOST-986's `60-tech-debt.md` Follow-up Tasks are therefore
ticketed and, once this ticket finishes Step 8, all closed. No
PYPOST-986-sourced follow-up is left unticketed or uncovered. (One
unrelated commit, `bb36a00d fix(import): PYPOST-1003 preserve all duplicate
rename pairs`, appears in the same file history — it is a bug fix, not one
of the four `60-tech-debt.md` follow-ups, and is out of scope for this
check.) Reconciling this against PYPOST-986's *other* debt sections (Code
Quality Issues, Performance Concerns) for full-ticket closure is Phase D of
the parent orchestration, not this step — noted here for the record only,
nothing created.

## Shortcuts Taken

None. No temporary solutions, stubs, or compromises were made. The one
deliberate choice — adding a new test method per gap rather than
parametrizing or editing the existing 2-conflict/`(2)` tests — is a
documented architectural decision (Step 2, "Decision: new method vs.
parametrizing the existing test"), not a shortcut: it was chosen precisely
to satisfy DoD item 5 (don't touch existing, currently-passing tests) and
to keep each scenario's failure independently diagnosable.

## Code Quality Issues

None found in the ticket's own diff (see `ai-tasks/PYPOST-1002/40-code-cleanup.md`
for the full review: zero new flake8 findings, no line-length/unused-import/
dead-code/duplication issues, naming and placement mirror each new test's
nearest sibling).

One pre-existing, repo-wide item was reconfirmed but is explicitly not this
ticket's to fix (same item already recorded as PYPOST-1070 by sibling
PYPOST-1001): `E402` flake8 warnings on both touched files'
`pytestmark`-before-imports lines, confirmed identical before/after this
ticket's diff. Not repeated as a new follow-up here — already ticketed.

## Missing Tests

None within this ticket's scope — its entire DoD (two named combinatorial
gaps) is now closed. Two non-blocking informational gaps were flagged during
Step 3's review and are evaluated below under Follow-up Tasks rather than
fixed in-ticket, since both are explicitly out of scope per the requirements
Q&A ("How many conflicting names / how deep a suffix chain is 'enough' to
prove the loop?" — three and `(3)` respectively, "no wider matrix is
required by this ticket's scope").

Broader Import behavior — conflict handling for OVERWRITE/KEEP_BOTH at 3+
conflicts, invalid files, parse failures, the Overwrite × encryption-cache
round trip, presenter wiring, button-click wiring — is intentionally out of
scope and already covered by the existing `TestImportEnvironments`/
`TestPlanImport*` suites and by sibling tickets PYPOST-999/1000/1001 (all
completed).

Every new test carries an explicit timeout via the module-level
`pytestmark = pytest.mark.timeout(60)` in both files — confirmed satisfied,
not a gap.

## Performance Concerns

None. Both additions are hermetic, in-memory: one offscreen-Qt widget test
with three small `Environment` objects and mocked dialogs (no real file
I/O, no network), and one pure-function call on a 2-element `set[str]`.
Neither has any runtime/production performance surface.

## Follow-up Tasks

1. **SKIP-default blind spot shared by both apply-to-all tests (2-conflict
   and this ticket's new 3-conflict test)** (Priority: Low).
   - **What**: Both `test_apply_to_all_conflicts_prompts_only_once`
     (existing, 2 conflicts) and the new
     `test_apply_to_all_conflicts_applies_to_third_and_later_conflicts` (3
     conflicts) only exercise `ImportConflictDecision.SKIP` as the
     apply-to-all decision. Neither proves the loop correctly propagates
     `OVERWRITE` or `KEEP_BOTH` to a third-and-later conflict (only SKIP's
     "leave untouched" effect is asserted at 3+ conflicts).
   - **Why it's debt, not urgent**: `_resolve_import_conflicts`
     (`pypost/ui/widgets/environments/environment_list_widget.py:342-359`)
     branches only on `apply_to_all is not None`, not on which decision
     value it holds — the loop's control flow is decision-agnostic, so a
     SKIP-only test already exercises the code path that would break for
     any decision. The gap is combinatorial-completeness of the *test
     matrix*, not a known or suspected code defect (confirmed by Step 3's
     review subagent, which found no divergence when it broke the loop
     generically). Requirements Q&A for this ticket explicitly scoped this
     out: "SKIP ... is what the existing 2-conflict sibling uses ... DoD
     item 1 only requires 'the same decision that was chosen for the
     first' to propagate, not exhaustive coverage of all three decision
     kinds."
   - **Suggested fix** (future ticket): one additional test in
     `TestImportEnvironments` using `OVERWRITE` or `KEEP_BOTH` as the
     apply-to-all decision across 3 conflicts, asserting the corresponding
     effect (id-preserving overwrite / numbered copy) lands on all three,
     not just the first two.
   - **Suggested Jira type/priority**: Debt / Low.
   - **First observed**: Step 3 review of this ticket
     (`ai-tasks/PYPOST-1002/00-roadmap.md` Step 3 entry), explicitly framed
     there as non-blocking and out of this ticket's DoD.
   - **Jira**: [PYPOST-1074](https://pypost.atlassian.net/browse/PYPOST-1074)

2. **`generate_import_copy_name` test proves "at least one increment," not
   strict "loop re-checks every step"** (Priority: Low).
   - **What**: `test_returns_next_numbered_copy_when_first_two_taken`
     (this ticket) proves the `while` loop advances from `suffix=2` to
     `suffix=3` when both are taken. It does not distinguish "the loop
     correctly re-checks membership on every iteration" from a
     hypothetical bug that, say, always performs exactly one extra
     increment regardless of how many further slots are taken — that
     divergence only becomes visible at `(4)` and beyond (e.g. taking
     `"Copy of Dev"`, `"(2)"`, and `"(3)"` and asserting `(4)` is returned).
   - **Why it's debt, not urgent**: the production `while` loop
     (`pypost/core/import_conflicts.py:21-29`) has an unbounded condition
     (`while f"{candidate} ({suffix})" in existing_names: suffix += 1`)
     with no special-casing by iteration count — there is no code-inspection
     reason to suspect it stops re-checking after one extra pass. This is a
     test-matrix completeness note, not a suspected defect. Requirements
     Q&A for this ticket explicitly scoped this out: "3 [conflicts] ... and
     a `(3)` result for copy-name generation ... are the minimum needed to
     distinguish real looping from a size-2-shaped special case; no wider
     matrix is required by this ticket's scope."
   - **Suggested fix** (future ticket, low priority, likely not worth its
     own ticket unless bundled with #1 above): one additional
     `TestGenerateImportCopyName` case seeding `{"Copy of Dev", "Copy of
     Dev (2)", "Copy of Dev (3)"}` and asserting `"Copy of Dev (4)"` is
     returned, to fully rule out any not-strictly-looping implementation.
   - **Suggested Jira type/priority**: Debt / Low (candidate for bundling
     with Follow-up #1 above into a single small ticket, since both are
     "go one step further in the same combinatorial matrix this ticket
     already extended").
   - **First observed**: Step 3 review of this ticket, explicitly framed
     as non-blocking and out of this ticket's DoD.
   - **Jira**: [PYPOST-1075](https://pypost.atlassian.net/browse/PYPOST-1075)

No other technical debt was identified. This ticket's actual deliverable —
two hermetic test methods with no production diff — introduced no new debt
of its own. Both follow-ups above are refinements to the very test matrix
this ticket extended, surfaced by Step 3's review while confirming the two
new tests were genuine (non-tautological) locks, and are recorded here per
the rule file's guidance on out-of-scope discoveries rather than expanded
in-ticket (both were explicitly named out-of-scope in the Step 1
requirements Q&A).
