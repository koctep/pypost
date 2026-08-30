# PYPOST-1233: Fix E402 pytestmark import-order findings in four tests/ modules

## Goals

`tests/test_lint_pytestmark_e402.py::test_no_e402_findings_in_tests_dir` is a permanent
regression guard (introduced by PYPOST-1070) that fails `make test` whenever any file under
`tests/` has a top-level `pytestmark = ...` assignment positioned before one or more of that
file's own top-level imports (flake8 E402: "module level import not at top of file"). The guard
is currently red — it was discovered failing during the PYPOST-1041 Step 4 full-suite run, and
independently confirmed to fail identically at that task's base commit `253403db` in a throwaway
baseline worktree, so it is pre-existing debt, not a regression introduced by PYPOST-1041.

A red permanent guard in the suite masks real signal: any other regression the guard is meant to
catch is invisible until this pre-existing failure is cleared, and every `make test` run reports
a false failure that engineers must learn to mentally discount. Fixing it restores `make test` to
a trustworthy pass/fail signal and completes the PYPOST-1070 remediation that this guard was
built to enforce (that task fixed 110 files; these 4 were missed).

## User Stories

- As an engineer running `make test` (or the PYPOST-1233 repro command
  `make test PYTEST_ARGS="tests/test_lint_pytestmark_e402.py"`), I want zero E402 findings under
  `tests/`, so that the suite result reflects real regressions only and I don't have to
  manually distinguish "known pre-existing failure" from "my change broke something."
- As a maintainer of `tests/`, I want every module's `pytestmark` declaration positioned after
  its imports, so that the file follows the same import-order convention already applied
  repo-wide by PYPOST-1070, and future edits don't reintroduce the defect.

## Definition of Done

- `flake8 --select=E402 tests/` (as invoked by the guard test) reports zero findings.
- `make test PYTEST_ARGS="tests/test_lint_pytestmark_e402.py"` passes.
- A full `make test` run no longer fails on this guard test.
- The four modules named in the Jira description each get their `pytestmark = pytest.mark.timeout(N)`
  line relocated to immediately after that module's last top-level import, and are otherwise
  unchanged:
  - `tests/test_examples_modernization.py`
  - `tests/test_examples_modernization_repro.py`
  - `tests/test_ui_library_manager.py`
  - `tests/test_ui_library_manager_repro.py`
- No other files under `tests/` are modified as part of this task.
- No test behavior changes: the same tests run with the same timeout marker value in each file
  (marker resolution reads the module attribute's value, not its source position, so relocating
  the assignment is behaviorally inert — this was already established and exercised at scale by
  PYPOST-1070's 110-file remediation).

## Task Description

**Problem**: Four test modules under `tests/` declare `pytestmark = pytest.mark.timeout(N)` above
their final top-level import block, rather than below it. flake8's E402 check ("module level
import not at top of file") treats any non-import top-level statement — including this
assignment — as closing the file's import block, so every import that follows is flagged. The
permanent regression guard added by PYPOST-1070
(`tests/test_lint_pytestmark_e402.py::test_no_e402_findings_in_tests_dir`) therefore fails,
reporting 20 findings across the four modules (at minimum lines 15, 25, and 26 per the Jira
excerpt).

**Goal**: Bring these four files into conformance with the same import-order convention that
PYPOST-1070 already established across 110 other files in `tests/`, so the guard test — and by
extension `make test` — passes cleanly.

**Constraints**:
- This is scoped strictly to import/statement *ordering* within the four named files. No
  functional, test-assertion, or import-content changes are in scope.
- The remediation must not alter what marker pytest resolves for any test in these files (same
  `pytest.mark.timeout(N)` value, same tests covered).
- `test_ui_library_manager.py`'s PySide6 imports (`QApplication`, `QDialog`, etc.) are plain
  top-level imports with no `importorskip`/`qapp`-availability ordering constraint — they may be
  reordered relative to `pytestmark` like any other import without special handling.
- No other pre-existing, out-of-scope lint findings in `tests/` (e.g. E302/E305/F401) are in
  scope for this task — the guard test itself deliberately excludes them via
  `--select=E402`.

**Assumptions**:
- The fix is purely mechanical: move each file's `pytestmark = pytest.mark.timeout(N)` line to
  directly below that file's last top-level import statement (matching the remediation pattern
  PYPOST-1070 already applied elsewhere, and the guidance already documented in the guard test's
  own docstring).
- No architecture step deliverable beyond this requirements doc is expected to add meaningful
  value given the task's 1-story-point, zero-behavioral-risk scope; Step 2 will record that
  explicitly rather than invent design content.

## Main Entities

This task has no new business entities — it is a source-ordering fix within existing test
modules. The relevant artifact is:

- **Test module** (`tests/*.py`): a pytest file whose module-level statement order (imports vs.
  `pytestmark` assignment) determines whether it satisfies the flake8 E402 lint rule enforced by
  the permanent regression guard.

## Q&A

- **Q: Why fix this now rather than leave the guard red?** A: A red permanent regression guard
  provides no protection — it can't distinguish a new regression from this known pre-existing
  failure, and it pollutes every `make test` run with a false failure signal. The fix is
  low-risk and low-effort (1 story point), so there is no reason to defer it.
- **Q: Does relocating `pytestmark` change which timeout applies to tests in these files?** A:
  No. pytest resolves markers from the module attribute's value via
  `item.get_closest_marker("timeout")`, not from the statement's source position. This is stated
  in the guard test's own docstring and was already validated at scale by PYPOST-1070's 110-file
  remediation using the same relocation pattern.
- **Q: Are the PySide6 imports in `test_ui_library_manager.py` special-cased (e.g. needing
  `importorskip` before other imports)?** A: No — per the Jira description, they are plain
  top-level imports unaffected by reordering relative to `pytestmark`.
