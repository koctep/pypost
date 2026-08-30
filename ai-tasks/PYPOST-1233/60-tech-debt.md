# PYPOST-1233: Technical Debt Analysis

## Shortcuts Taken

None. Step 4 made a minimal, mechanical 2-line move per file (relocating the existing
`pytestmark = pytest.mark.timeout(30)` line to directly below the last top-level import) in each
of the 4 target files. No shortcuts, no `# noqa` suppressions, no scope creep — verified via
`git diff` in Step 5 that each file's diff is exactly the one-line-removed/one-line-added move.

## Code Quality Issues

None introduced by this task. The implementation itself does not add any code sections needing
refactoring, renaming, or function breakdown — it only reorders one existing line per file.

Pre-existing code quality issues in the same 4 files were discovered (not introduced) during this
task's Step 5 cleanup pass and are documented under Follow-up Tasks below, out of scope for this
1-story-point mechanical fix.

## Missing Tests

None. The pre-existing guard test `tests/test_lint_pytestmark_e402.py::test_no_e402_findings_in_tests_dir`
(from Step 3) already covers the E402 regression this task fixes and now passes. No new test was
needed per the Step 2 architecture decision (a repro already existed).

**Tests missing explicit timeout markers**: none. All 4 touched files already carry
`pytestmark = pytest.mark.timeout(30)` — Step 4 only relocated that line; it did not add or remove
timeout coverage. Not a blocker.

## Performance Concerns

None. The change affects only import/pytestmark statement ordering at module load time in 4 test
files; it has no effect on test execution time or runtime performance.

## Deviations from Architecture

None. Step 4 followed the Step 2 architecture exactly: relocate `pytestmark` below the last
top-level import, touch nothing else.

## Hardcoded Values

None introduced. The `pytest.mark.timeout(30)` value itself was pre-existing and unchanged by this
task (only its line position moved).

## Follow-up Tasks

**NON-BLOCKER — pre-existing flake8 findings (F401/E501/W293), out of scope for PYPOST-1233.**

Discovered during this task's Step 5 code-cleanup pass (documented in
`ai-tasks/PYPOST-1233/40-code-cleanup.md`) via a full-default `flake8` run (no `--select`) against
the 4 files this task touched. These findings pre-date PYPOST-1233 (only their reported line
numbers shifted by the 2-line pytestmark relocation) and are unrelated to this task's E402 scope.
Re-run on the current (post-fix) tree to get exact counts:

```
.venv/bin/python -m flake8 tests/test_examples_modernization.py \
  tests/test_examples_modernization_repro.py \
  tests/test_ui_library_manager.py \
  tests/test_ui_library_manager_repro.py
```

Total: 30 findings (16 F401, 12 E501, 2 W293) — matches Step 5's count exactly.

| File | F401 (unused import) | E501 (line too long) | W293 (whitespace-only blank line) | Total |
| --- | --- | --- | --- | --- |
| `tests/test_examples_modernization.py` | 2 | 2 | 0 | 4 |
| `tests/test_examples_modernization_repro.py` | 0 | 1 | 0 | 1 |
| `tests/test_ui_library_manager.py` | 8 | 7 | 0 | 15 |
| `tests/test_ui_library_manager_repro.py` | 6 | 2 | 2 | 10 |
| **Total** | **16** | **12** | **2** | **30** |

Detail:
- `tests/test_examples_modernization.py` — F401: `read_library_manifest`, `validate_manifest_collections`
  (both from `pypost.core.library_manifest`, line 7) imported but unused; E501: lines 1 and 67 over
  100 chars.
- `tests/test_examples_modernization_repro.py` — E501: line 1 over 100 chars.
- `tests/test_ui_library_manager.py` — F401: `Qt` (PySide6.QtCore), `QApplication`/`QDialog`
  (PySide6.QtWidgets), `GitAuthConfig` (pypost.models.git_library), `LibraryCollectionEntry`
  (pypost.models.library_manifest), `LibraryCollectionsWidget`/`LibraryDetailWidget`/`LibraryListWidget`
  (pypost.ui.widgets.library_manager_panel) — 8 total, all imported but unused; E501: lines 1, 109,
  119, 201, 312, 324, 325 over 100 chars.
- `tests/test_ui_library_manager_repro.py` — F401: `GitAuthConfig`, `GitAuthMode`, `GitBranchInfo`,
  `GitDiagnosticError`, `GitDiagnosticErrorCode`, `GitRepoStatus` (all from `pypost.models.git_library`,
  line 13) imported but unused; E501: lines 1 and 129 over 100 chars; W293: lines 103 and 105
  (whitespace-only blank lines).

**Classification**: NON-BLOCKER — pre-existing tech debt (linter findings, not failing tests; the
`failing-tests-triage` pre-existing-failure process with baseline-worktree comparison does not
apply here — these are static-analysis findings, already confirmed unchanged in count/type across
the pre-fix and post-fix versions of these files per Step 5).

**Dedup check against known-tracked issues** (read-only `jira_get_issue` lookups, no issues
created or modified):

- `PYPOST-1234` — pre-existing failure cluster for `tests/test_makefile.py` /
  `tests/test_pytest_exit_policy.py` timing out under full-suite parallel load (worker-timeout
  class). Does not cover flake8 findings. No overlap.
- `PYPOST-1111` — pre-existing audit/baseline-metrics snapshot drift (dialogs audit report, SOLID
  audit baseline) across several test files. Does not cover flake8 findings, and does not name any
  of the 4 files touched by PYPOST-1233. No overlap.
- `PYPOST-1251` — pre-existing SIGSEGV crash in `tests/test_main_window_alert_reload.py`
  (Qt/PySide6/shiboken6 widget-teardown lifecycle defect). Unrelated file, unrelated class of
  issue. No overlap.
- `PYPOST-1252` — pre-existing LOC/inventory drift in
  `tests/test_pypost_1077_verification_artifacts.py` (dialog audit report staleness). Unrelated
  file, unrelated class of issue. No overlap.
- Also checked `PYPOST-729` ("[PYPOST-687] Fix flake8 violations for make lint", found via JQL
  `text ~ "F401"`) — Done/resolved in June 2026, fixed a different, unrelated set of 4 flake8
  violations (F841, F401, W391, E501) elsewhere in the codebase. Already closed; does not cover
  these 4 files' current findings.

**Conclusion**: none of the known-tracked issues cover these 30 F401/E501/W293 findings in the 4
files. This is real, previously-undocumented tech debt discovered during PYPOST-1233. Suggested
scope: run full-default `flake8` (not `--select`) on these 4 files, remove the 16 unused imports
(F401), wrap/shorten the 12 over-length lines (E501), and strip whitespace from the 2 blank-only
lines (W293); verify with `make test
PYTEST_ARGS="tests/test_examples_modernization.py tests/test_examples_modernization_repro.py
tests/test_ui_library_manager.py tests/test_ui_library_manager_repro.py"` afterward to confirm no
behavior change. Priority: Low (lint-only, no functional impact, no CI gate currently blocked by
these findings since `make lint`/CI in this repo evidently does not run full-default flake8 with
these rules enforced as a gate, or these would already be failing builds).

**Jira**: [PYPOST-1253](https://pypost.atlassian.net/browse/PYPOST-1253) (Debt, 2 SP, Low priority)
