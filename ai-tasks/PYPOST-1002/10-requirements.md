# PYPOST-1002: Extend import conflict combinatorial tests

## Goals

Environment import lets a user resolve name conflicts one at a time, or apply
one decision ("Skip", "Keep both", "Overwrite") to every remaining conflict at
once via "apply to all." The disambiguation logic behind "Keep both"
(`generate_import_copy_name`) numbers duplicate copies until it finds a free
name. Both behaviors are implemented as a loop, and both are only proven today
at the smallest size that exercises a loop at all: exactly **two** conflicting
names for apply-to-all, and exactly **one** taken numbered slot (`(2)`) for
copy-name generation.

A loop that is only tested at its smallest non-trivial size does not prove it
actually loops — an off-by-one, an early `break`, or a condition that
happens to be equivalent to a plain `if` at size 2 could pass today's suite
and still be wrong for size 3 or beyond. This task closes that gap: it proves
the apply-to-all decision is honored across a third (and further) conflict,
not just carried from the first to a second, and it proves the numbered-copy
generator keeps incrementing past the first taken slot instead of stopping
there.

This is verification/testing debt only, carried over from
`ai-tasks/PYPOST-986/60-tech-debt.md` ("Missing Tests": three-or-more-way
apply-to-all sequencing, and `generate_import_copy_name` beyond `(2)`). The
underlying production logic already exists and already handles these cases
per code inspection (see Task Description); no new user-facing behavior is
expected. If a new assertion surfaces an actual defect in either loop, fixing
that defect is in scope as a byproduct of this task — but is not the expected
outcome.

**Implementation language**: Python (existing PyPost desktop app; test-only
change, same stack as the rest of the codebase).

## User Stories

- As a developer relying on the import conflict flow, I want an automated
  test proving "apply to all" is honored for a third (and later) conflicting
  name, not just carried from the first conflict to the second, so a
  regression that only breaks past the second iteration cannot merge
  unnoticed.
- As a developer relying on `generate_import_copy_name`, I want an automated
  test proving the numbered-suffix search keeps advancing past `(2)` to
  `(3)`, so a regression that stops the search too early (e.g. an early
  `return` or a loop bound of exactly one iteration) cannot merge unnoticed.
- As a maintainer of environment import, I want these two new tests to sit
  alongside the existing two-conflict and "(2)" tests without duplicating or
  replacing them, so the suite gains combinatorial coverage without losing
  clarity about what each test proves.

## Definition of Done

1. A new (or extended) test proves "apply to all" is honored across **three
   or more** conflicting names during import: the conflict-decision prompt is
   shown exactly once, and every conflicting name — including the third one —
   receives the same decision that was chosen for the first, with the correct
   resulting state (e.g. all three existing environments left untouched under
   `SKIP`, or all three renamed/overwritten consistently under another
   decision).
2. A new test proves `generate_import_copy_name` reaches a `(3)` suffix: given
   an existing-names set where both `"Copy of <name>"` and
   `"Copy of <name> (2)"` are already taken, the function returns
   `"Copy of <name> (3)"`.
3. Both new tests are in scope's terms functional (pytest) tests, not just
   inspection — they must fail if the loop under test is truncated,
   off-by-one, or short-circuited.
4. Both new tests follow existing project and file conventions: they live in
   the same test files/classes as their two-way/`(2)` siblings
   (`tests/test_environment_list_widget.py::TestImportEnvironments` for
   apply-to-all; the `generate_import_copy_name` test class in
   `tests/test_environment_import.py` for copy-name), and inherit the
   module-level `pytest.mark.timeout(60)` already declared in those files.
5. No existing test's behavior or assertions change unless a genuine defect
   is found and fixed; if that happens, the defect and the fix are recorded
   explicitly (this is not the expected outcome — see Goals).
6. Out of scope for this task (each already covered elsewhere or ticketed
   separately): the existing two-conflict apply-to-all case and the existing
   `(2)`-taken copy-name case (already covered, left as-is); invalid import
   file and zero-candidates handling (already covered); the Overwrite ×
   encryption-cache interaction (PYPOST-999); `EnvPresenter`-level import
   wiring (PYPOST-1000); the **Import…** button click wiring (PYPOST-1001,
   completed); any new production API, UI change, or on-disk format change.

## Task Description

**Problem:** Two pieces of already-implemented, already-working loop logic in
the PYPOST-986 import feature are under-tested at their smallest boundary
only:

- `EnvironmentListWidget._resolve_import_conflicts`
  (`pypost/ui/widgets/environments/environment_list_widget.py:342-359`) loops
  over `conflicts` (one entry per conflicting name) and, once the user picks
  "apply to all" on the first conflict, applies that same decision to every
  subsequent name without prompting again. The existing test
  (`test_apply_to_all_conflicts_prompts_only_once`,
  `tests/test_environment_list_widget.py:123-144`) uses exactly two
  conflicting names ("Dev", "Prod"), so it only proves the decision carries
  from conflict 1 to conflict 2 — it cannot distinguish "the loop applies to
  all remaining conflicts" from "the loop happens to also apply to exactly
  one more."
- `generate_import_copy_name`
  (`pypost/core/import_conflicts.py:21-29`) returns `"Copy of <name>"` when
  free, else walks a `while` loop incrementing `suffix` from 2 until
  `f"{candidate} ({suffix})"` is not in `existing_names`. The existing tests
  (`tests/test_environment_import.py`, `TestGenerateImportCopyName` class
  around line 140) cover only "free" (`"Copy of Dev"`) and "first numbered
  slot taken" (`"Copy of Dev (2)"`) — the `while` loop's continuation past its
  first iteration (to `(3)`, `(4)`, ...) is implemented but never directly
  exercised.

**Goal:** Add one test per gap, each sized to prove the loop actually
iterates rather than merely handling its smallest case:

- An apply-to-all test with **three or more** conflicting names, asserting
  the conflict prompt is still invoked exactly once and that the chosen
  decision's effect is visible on all conflicting entries, including the
  last one.
- A `generate_import_copy_name` test where both `(2)` and the base "Copy of
  X" name are already taken, asserting the function returns the `(3)` form.

**Scope (in):**

- One new/extended apply-to-all test at 3+ conflicting names in
  `tests/test_environment_list_widget.py`.
- One new `generate_import_copy_name` test reaching `(3)` in
  `tests/test_environment_import.py`.
- Fixing a defect in either loop, only if one of the two new assertions
  actually fails against current code (not expected; see Goals).

**Scope (out):**

- Everything already covered: the 2-conflict apply-to-all case, the `(2)`
  copy-name case, invalid import file, zero import candidates, and the
  Overwrite × encryption-cache interaction (that interaction is PYPOST-999,
  not this ticket).
- `EnvPresenter`-level import wiring (PYPOST-1000).
- **Import…** button click wiring (PYPOST-1001, already completed).
- Any change to import UX, conflict-prompt copy, the on-disk import format,
  or the "Copy of X" naming convention itself.
- Testing conflict counts beyond what's needed to prove the loop continues
  (i.e., this does not require exhaustive testing at every N — 3 is enough to
  distinguish "loops" from "handles exactly 2").

**Constraints and assumptions:**

- Programming language: Python (existing PyPost desktop app).
- Source: follow-up 4 in `ai-tasks/PYPOST-986/60-tech-debt.md` ("Extend
  `test_apply_to_all_conflicts_prompts_only_once`-style coverage to 3+
  conflicting names and add a `generate_import_copy_name` case that reaches
  `(3)`"), ticketed as
  [PYPOST-1002](https://pypost.atlassian.net/browse/PYPOST-1002).
  Parent: [PYPOST-986](https://pypost.atlassian.net/browse/PYPOST-986).
- Both loops are believed correct today by code inspection (see Task
  Description); this is verification debt unless a new assertion reveals a
  defect.
- Approval for Step 1 artifacts is treated as granted under
  sprint-task-runner autonomy (same as sibling ticket PYPOST-1001).

## Non-Functional Requirements

- The new tests must be fast and hermetic: no network, no live key service,
  no real disk I/O beyond what the existing `TestImportEnvironments` fixtures
  already use (in-memory `Environment` objects, mocked dialog prompts).
- Must not make the Environments manager or import test suites flaky or
  unbounded (explicit `pytest.mark.timeout(60)` already applies at module
  level in both target files; no unbounded GUI waits).
- Security: no new surface; both tests operate on in-memory names/environment
  objects with no secret-bearing data required.
- Focused: exactly two new test cases are needed to close the two named
  gaps — no broader combinatorial matrix is required.

## Main Entities

- **Apply-to-all decision** — a single `ImportConflictDecision` (Overwrite /
  Keep both / Skip) chosen by the user on the first conflict and then reused,
  without re-prompting, for every subsequent conflicting name in the same
  import.
- **Conflict list** — the ordered set of import candidate names that collide
  with an existing environment's name, produced by `find_conflicts` and
  iterated by `_resolve_import_conflicts`.
- **`generate_import_copy_name`** — the pure function that derives a unique
  "Copy of X" name for the "Keep both" decision, incrementing a numeric
  suffix until it finds a name not already in the existing-names set.
- **Existing-names set** — the set of already-used environment names that
  `generate_import_copy_name` checks candidates against.

## User scenarios

1. A user imports a file containing three environments whose names all
   collide with existing environments. On the first conflict prompt they
   choose "Skip, apply to all." The prompt is shown once; all three existing
   environments remain unchanged, including the third one. (Currently
   asserted only for two conflicting names — this task extends it to three.)
2. A user imports environments and chooses "Keep both" for a name where both
   the plain "Copy of X" and "Copy of X (2)" already exist. The import
   assigns "Copy of X (3)". (Currently asserted only up to the "(2)" case —
   this task adds the "(3)" case.)

## Q&A

**Q:** Why is testing at size 2 (or "(2)") not already sufficient?

**A:** A loop's smallest non-trivial size can pass by coincidence even when
the loop is broken for further iterations (e.g. an off-by-one that happens to
allow exactly one extra pass, or a bound that is really "at most one repeat").
Only a size-3 case actually distinguishes "this loops" from "this handles
exactly two."

**Q:** Is any production behavior expected to change?

**A:** No. Both loops are implemented and, per code inspection
(`_resolve_import_conflicts` at
`pypost/ui/widgets/environments/environment_list_widget.py:342-359` and
`generate_import_copy_name` at `pypost/core/import_conflicts.py:21-29`),
already handle 3+ conflicts and `(3)` correctly. This task is expected to add
passing tests, not fix bugs — same pattern as sibling ticket PYPOST-1001,
which completed with zero production changes.

**Q:** Where do the two new tests belong?

**A:** Alongside their existing siblings: the apply-to-all extension in
`tests/test_environment_list_widget.py::TestImportEnvironments` (next to
`test_apply_to_all_conflicts_prompts_only_once`), and the copy-name `(3)`
case in the `generate_import_copy_name` test class in
`tests/test_environment_import.py` (next to
`test_returns_numbered_copy_when_first_taken`).

**Q:** Does this ticket touch the Overwrite × encryption-cache interaction,
presenter wiring, or the Import… button?

**A:** No. Those are separately ticketed: PYPOST-999 (Overwrite ×
encryption-cache), PYPOST-1000 (`EnvPresenter` wiring), and PYPOST-1001
(Import… button click, completed). This ticket only closes the two named
combinatorial test gaps.

**Q:** How many conflicting names / how deep a suffix chain is "enough" to
prove the loop?

**A:** Three conflicting names for apply-to-all, and a `(3)` result for
copy-name generation, per the Jira description and the source tech-debt note.
Both are the minimum needed to distinguish real looping from a
size-2-shaped special case; no wider matrix is required by this ticket's
scope.
