# PYPOST-1002: Extend import conflict combinatorial tests

## Research

**Target 1 — apply-to-all loop.**

`EnvironmentListWidget._resolve_import_conflicts`
(`pypost/ui/widgets/environments/environment_list_widget.py:342-359`):

```python
def _resolve_import_conflicts(
    self, candidates: list[Environment]
) -> dict[str, ImportConflictDecision]:
    conflicts = find_conflicts(self.environments, candidates)
    decisions: dict[str, ImportConflictDecision] = {}
    apply_to_all: ImportConflictDecision | None = None
    for i, name in enumerate(conflicts):
        if apply_to_all is not None:
            decisions[name] = apply_to_all
            continue
        remaining_count = len(conflicts) - i - 1
        decision, use_for_all = prompt_import_conflict(
            self, name, remaining_count=remaining_count
        )
        decisions[name] = decision
        if use_for_all:
            apply_to_all = decision
    return decisions
```

Called from `import_environments` (line 322): `decisions =
self._resolve_import_conflicts(candidates)`, then `plan_import(...)` applies
`decisions` to build the new environments list. `find_conflicts` (imported
from `pypost.core.environment_import`, re-exported from
`pypost.core.import_conflicts`) returns the ordered list of colliding names.

The existing lock, `test_apply_to_all_conflicts_prompts_only_once`
(`tests/test_environment_list_widget.py:123-144`), lives in
`TestImportEnvironments` inside `tests/test_environment_list_widget.py`. It
patches `prompt_import_conflict` to always return `(SKIP, True)`
(`use_for_all=True` on the *first* call), imports two conflicting names
("Dev", "Prod"), and asserts the prompt fired once and both existing
environments kept their original variables. Because `conflicts` has length 2,
this test cannot distinguish the real loop (`for i, name in
enumerate(conflicts): ...`) from a hypothetical bug that only ever applies
`apply_to_all` to exactly one subsequent name (e.g. an early `break` after
the second iteration, or a bound that special-cases `i == 1`) — both would
produce identical results at size 2.

Sibling methods in the same class (`test_conflict_prompts_once_per_conflicting_name`,
line 99; `test_happy_path_...`, line 30) establish the file's fixture idiom:
a local `read_import_file` closure returning `(candidates, parse_errors)`,
a list of existing `Environment` objects passed into `_make_widget`, and
`@patch` decorators over `prompt_import_environments_file`,
`prompt_import_conflict`, and `show_import_result` at module scope (`_MODULE
= "pypost.ui.widgets.environments.environment_list_widget"`). The module
declares `pytestmark = pytest.mark.timeout(60)` at line 5, applying to every
test in the file including new ones.

**Target 2 — copy-name suffix search.**

`generate_import_copy_name` (`pypost/core/import_conflicts.py:21-29`):

```python
def generate_import_copy_name(name: str, existing_names: set[str]) -> str:
    """"Copy of X" when free, else "Copy of X (2)", "(3)", ... until unique."""
    candidate = format_copy_of_name(name)
    if candidate not in existing_names:
        return candidate
    suffix = 2
    while f"{candidate} ({suffix})" in existing_names:
        suffix += 1
    return f"{candidate} ({suffix})"
```

A pure function, no I/O, re-exported from `pypost.core.environment_import`
for backward compatibility (`tests/test_environment_import.py` imports it
from there, line 19). Its existing tests live in
`tests/test_environment_import.py::TestGenerateImportCopyName`
(`unittest.TestCase`, lines 142-149):

```python
class TestGenerateImportCopyName(unittest.TestCase):
    def test_returns_copy_of_name_when_free(self) -> None:
        self.assertEqual(generate_import_copy_name("Dev", set()), "Copy of Dev")

    def test_returns_numbered_copy_when_first_taken(self) -> None:
        self.assertEqual(
            generate_import_copy_name("Dev", {"Copy of Dev"}), "Copy of Dev (2)"
        )
```

The second test seeds only `{"Copy of Dev"}`, so `suffix = 2` is checked once
(`"Copy of Dev (2)" not in existing_names` → returns immediately). The
`while` loop's *continuation* — incrementing `suffix` again after the first
failed check — is implemented but never exercised: a bug that returned
`f"{candidate} ({suffix})"` unconditionally after one failed lookup (instead
of looping) would still pass both existing tests. The file declares
`pytestmark = pytest.mark.timeout(60)` at line 10 (module scope, applies to
the whole file including `unittest.TestCase` subclasses collected by
pytest).

## Implementation Plan

**Gap 1 — apply-to-all at 3+ conflicts: new test method, not parametrization.**

Add one new test method to the existing `TestImportEnvironments` class in
`tests/test_environment_list_widget.py`, placed immediately after
`test_apply_to_all_conflicts_prompts_only_once` (after line 144). Working
name: `test_apply_to_all_conflicts_applies_to_third_and_later_conflicts`.

Shape (mirrors the existing test's structure exactly, sized up):

- `@patch(f"{_MODULE}.show_import_result")`,
  `@patch(f"{_MODULE}.prompt_import_conflict", return_value=(ImportConflictDecision.SKIP, True))`,
  `@patch(f"{_MODULE}.prompt_import_environments_file", return_value=Path("/tmp/import.json"))` —
  identical decorator stack to the existing test.
- `read_import_file` returns **three** colliding `Environment` objects (e.g.
  "Dev", "Prod", "Staging"), each with a distinguishable variable so a
  mutation would be individually detectable.
- `envs` holds three existing `Environment` objects with matching names and
  original (pre-import) variables.
- After `widget.import_environments()`:
  - `mock_prompt_conflict.assert_called_once()` — proves the prompt was
    shown exactly once despite three conflicts (only meaningful if the
    third conflict is actually reached without a second prompt).
  - Assert **all three** environments — including the third —
    kept their original variables under `SKIP`. Asserting only the first
    two would reproduce today's blind spot; the third assertion is the one
    that actually distinguishes "loops over all remaining conflicts" from
    "carries the decision to exactly one more."

**Decision: new method vs. parametrizing the existing test — new method
chosen.**

- The DoD and requirements Q&A ("Where do the two new tests belong?") are
  explicit that the new test sits *alongside* the existing 2-conflict test,
  not replacing it: "these two new tests... without duplicating or
  replacing" the two-way/`(2)` siblings. Folding the existing test into a
  `@pytest.mark.parametrize(("names", ...), [...])` case would edit the
  existing test's body and decorator stack — forbidden by DoD item 5
  ("No existing test's behavior or assertions change unless a genuine
  defect is found").
  - Parametrizing here also fights the file's own conventions:  every test
  in `TestImportEnvironments` uses a fixed number of stacked `@patch`
  decorators whose `return_value`/mock names are matched positionally to
  test parameters; the existing 2-conflict test's assertions are hardcoded
  to specific `envs[0]`/`envs[1]` variable dicts, not generalized over a
  variable-length `names` list. Reshaping that into a data-driven
  parametrized test would touch the current, working, explicitly-in-scope-
  as-untouched test and increase the diff surface for no benefit, since only
  one new size (3) is required (not a matrix).
  - A new, independent method keeps each test's failure diagnosable on its
  own ("the 2-conflict case broke" vs. "the 3-conflict case broke") and
  matches the existing file's one-test-per-scenario style (see
  `test_conflict_prompts_once_per_conflicting_name` next to
  `test_apply_to_all_conflicts_prompts_only_once` — already two closely
  related, non-parametrized siblings).

**Gap 2 — `generate_import_copy_name` reaching `(3)`.**

Add one new test method to `TestGenerateImportCopyName`
(`tests/test_environment_import.py`, after line 149). Working name:
`test_returns_next_numbered_copy_when_first_two_taken`.

```python
def test_returns_next_numbered_copy_when_first_two_taken(self) -> None:
    self.assertEqual(
        generate_import_copy_name("Dev", {"Copy of Dev", "Copy of Dev (2)"}),
        "Copy of Dev (3)",
    )
```

Seeding both `"Copy of Dev"` and `"Copy of Dev (2)"` as taken forces the
`while` loop to fail its first check (`suffix = 2`) and execute a second
iteration (`suffix = 3`) before returning — the exact continuation the
existing `(2)`-only test cannot exercise. No new fixtures or helpers needed;
this is a single additional method on the existing `unittest.TestCase`
subclass, consistent with its two current one-liner test bodies.

**Mandatory — Failing Repro (next Step 3):** Both new tests are the "red"
artifacts for Step 3, written before touching any production file:

1. `tests/test_environment_list_widget.py::TestImportEnvironments::test_apply_to_all_conflicts_applies_to_third_and_later_conflicts`
   — asserts `prompt_import_conflict` (mocked) is called exactly once across
   three conflicting names, and that all three existing environments'
   variables are unchanged under a `SKIP`+apply-to-all decision. No live
   external deps: `prompt_import_environments_file`, `prompt_import_conflict`,
   and `show_import_result` are all patched at `_MODULE` scope (matching
   every other test in the class), and the Qt widget runs against the
   existing offscreen `qapp` fixture — no real file dialog, no disk I/O.
2. `tests/test_environment_import.py::TestGenerateImportCopyName::test_returns_next_numbered_copy_when_first_two_taken`
   — asserts `generate_import_copy_name("Dev", {"Copy of Dev", "Copy of Dev (2)"})
   == "Copy of Dev (3)"`. Pure function, in-memory `set[str]`, no I/O at all.

Sequencing: research (this document, done) → write both tests against
current `dev` code → run `pytest tests/test_environment_list_widget.py
tests/test_environment_import.py`. Per the Task Description's code
inspection (both loops already correctly continue past their first
iteration), both new tests are expected to pass immediately — this is a
verification lock (same pattern as sibling PYPOST-1001), not a classic
red-then-fix TDD cycle. If either test unexpectedly fails against current
code, that failure is the real defect this task exists to catch, and
Step 4 becomes: fix the minimal defect in the corresponding loop (either
`_resolve_import_conflicts`'s `for` loop or `generate_import_copy_name`'s
`while` loop) until green, and record the defect explicitly per DoD item 5.

## Architecture

No new modules, classes, or production interfaces are introduced. This is a
test-only addition to two existing test files, each adding one method to an
existing test class.

```
tests/test_environment_list_widget.py
└── TestImportEnvironments
    ├── test_apply_to_all_conflicts_prompts_only_once        (existing, untouched — 2 conflicts)
    └── test_apply_to_all_conflicts_applies_to_third_and_later_conflicts   (new — 3 conflicts)
            │
            │ widget.import_environments()
            │   → self._resolve_import_conflicts(candidates)     [environment_list_widget.py:342-359]
            │        conflicts = find_conflicts(...)              → ["Dev", "Prod", "Staging"]
            │        for i, name in enumerate(conflicts):
            │          i=0 "Dev":     prompt_import_conflict(...) → (SKIP, True)  [1 real prompt call]
            │          i=1 "Prod":    apply_to_all is SKIP        → decisions["Prod"] = SKIP   (no prompt)
            │          i=2 "Staging": apply_to_all is SKIP        → decisions["Staging"] = SKIP (no prompt)
            │   → plan_import(self.environments, candidates, decisions)
            └── assert: prompt called once; envs[0..2].variables all unchanged

tests/test_environment_import.py
└── TestGenerateImportCopyName
    ├── test_returns_copy_of_name_when_free              (existing, untouched)
    ├── test_returns_numbered_copy_when_first_taken       (existing, untouched — "(2)")
    └── test_returns_next_numbered_copy_when_first_two_taken   (new — "(3)")
            │
            │ generate_import_copy_name("Dev", {"Copy of Dev", "Copy of Dev (2)"})
            │   [import_conflicts.py:21-29]
            │     candidate = "Copy of Dev"          → already in existing_names
            │     suffix = 2  → "Copy of Dev (2)"      → already in existing_names → loop continues
            │     suffix = 3  → "Copy of Dev (3)"      → not in existing_names     → loop exits
            └── assert: returns "Copy of Dev (3)"
```

**Module interaction.**

- `tests/test_environment_list_widget.py` (test) → imports
  `EnvironmentListWidget` from
  `pypost.ui.widgets.environments.environment_list_widget` (system under
  test, unchanged) and `ImportConflictDecision` from
  `pypost.core.environment_import` (unchanged). No new imports needed beyond
  what the file already has for the sibling 2-conflict test.
- `tests/test_environment_import.py` (test) → imports
  `generate_import_copy_name` from `pypost.core.environment_import`
  (unchanged; itself re-exported from `pypost.core.import_conflicts`). No new
  imports needed.
- Neither `pypost/ui/widgets/environments/environment_list_widget.py` nor
  `pypost/core/import_conflicts.py` (nor
  `pypost/core/environment_import.py`) is expected to change.

**Selected pattern and justification.**

- **Behavior-locking unit/widget tests via mock-and-assert, sized to the
  minimum that distinguishes "loops" from "handles exactly N-1"**, matching
  the existing two tests being extended and the sibling PYPOST-1001 pattern.
  No new pattern is introduced; the new tests are structurally identical to
  their existing siblings, just larger inputs.
- **New method over parametrization** (Gap 1) and **new method over editing
  an existing one-liner** (Gap 2): both keep the diff to pure addition,
  satisfy the DoD's "without duplicating or replacing" existing tests, and
  keep per-scenario failures independently diagnosable — consistent with
  this codebase's existing style of one narrowly-scoped test method per
  scenario rather than data-driven parametrization for small, semantically
  distinct cases.
- **No production code changes anticipated.** Both loops are already
  correct by code inspection (`for i, name in enumerate(conflicts)` has no
  early exit; `while f"...({suffix})" in existing_names: suffix += 1` has no
  bound other than the membership check). This mirrors PYPOST-1001, which
  completed with zero production changes; the only trigger for a production
  edit here is a new assertion actually failing in Step 3/4, which is
  possible but not expected.

## Q&A

**Q:** Why not parametrize `test_apply_to_all_conflicts_prompts_only_once`
over conflict count (e.g. `@pytest.mark.parametrize("count", [2, 3])`)?

**A:** DoD item 5 forbids changing the existing test's behavior/assertions
absent a discovered defect, and the Q&A in the requirements doc explicitly
says the new test sits "alongside" its sibling. Converting the existing
fixed-shape test (hardcoded `envs[0]`/`envs[1]` assertions, two named
environments "Dev"/"Prod") into a parametrized, variable-length version
would rewrite the existing, currently-passing test — out of scope and risks
regressing its clarity for no coverage gain, since only one additional size
(3) is required.

**Q:** Why three conflicts and not four or five?

**A:** Per the requirements' own scope-out list and Q&A: "3 is enough to
distinguish 'loops' from 'handles exactly 2'"; no wider matrix is required.
Same reasoning applies to reaching exactly `(3)` for the copy-name test
rather than `(4)` or beyond.

**Q:** Does the new apply-to-all test need a different decision
(`OVERWRITE`/`KEEP_BOTH`) instead of `SKIP`?

**A:** No — `SKIP` is what the existing 2-conflict sibling uses, it is the
simplest decision to assert against (environments simply keep their
pre-import `variables`), and DoD item 1 only requires "the same decision
that was chosen for the first" to propagate, not exhaustive coverage of all
three decision kinds at 3+ conflicts (that already exists for exactly one
decision kind, which is what's needed to prove the loop).

**Q:** Are there any new fixtures, helpers, or imports required?

**A:** No. Both new tests reuse existing fixtures/helpers verbatim:
`_make_widget`, `qapp`, the `_MODULE`-scoped `@patch` targets in
`test_environment_list_widget.py`; plain `self.assertEqual` in the existing
`unittest.TestCase` subclass in `test_environment_import.py`.
