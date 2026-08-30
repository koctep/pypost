# Roadmap: PYPOST-1233

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1233/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [/] `ai-tasks/PYPOST-1233/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [/] Pre-existing red guard confirmed: `tests/test_lint_pytestmark_e402.py::test_no_e402_findings_in_tests_dir`
    (no new test written, per architecture). `make test PYTEST_ARGS="tests/test_lint_pytestmark_e402.py"`
    fails: `flake8 --jobs=1 --select=E402 tests/ reported 20 finding(s) (expected 0)`. Confirmed via
    direct `flake8 --select=E402 tests/` that all 20 findings fall in exactly the four named files
    (test_examples_modernization.py: 4, test_examples_modernization_repro.py: 3,
    test_ui_library_manager.py: 10, test_ui_library_manager_repro.py: 3) — no unrelated/fixture errors.
- [x] **STEP 4: Development**
  - [x] Mechanically relocated the module-level `pytestmark = pytest.mark.timeout(30)`
    line to directly below the last top-level import in each of the 4 offending files
    (no other code/imports/logic changed):
    - `tests/test_examples_modernization.py`: pytestmark was line 7 (between `import pytest`
      at line 5 and 4 imports at lines 9-16); moved to immediately after the last import
      (`from pypost.models.models import Collection`, now the line directly above pytestmark).
    - `tests/test_examples_modernization_repro.py`: pytestmark was line 7 (between
      `import pytest` and 3 imports at lines 9-14); moved to immediately after the last
      import (`from pypost.core.collection_serializer import read_collection_file`).
    - `tests/test_ui_library_manager.py`: pytestmark was line 18 (between `import pytest`
      and 10 imports spanning lines 20-52, incl. `PySide6`, `pypost.core.*`,
      `pypost.models.*`, `pypost.ui.*`); moved to immediately after the last import
      (`from pypost.ui import widget_ids`), directly above the `sample_manifest` fixture.
    - `tests/test_ui_library_manager_repro.py`: pytestmark was line 13 (between
      `import pytest` and 3 imports at lines 15-26); moved to immediately after the last
      import (`from pypost.ui import widget_ids`).
  - [x] Verified fix: `python -m flake8 --select=E402` on all 4 files now reports 0 findings
    (was 4 + 3 + 10 + 3 = 20, matching Step 3's count).
  - [x] `make test PYTEST_ARGS="tests/test_lint_pytestmark_e402.py"` — PASSED (was the
    failing repro from Step 3).
  - [x] `make test PYTEST_ARGS="tests/test_examples_modernization.py tests/test_examples_modernization_repro.py tests/test_ui_library_manager.py tests/test_ui_library_manager_repro.py"` —
    all 4 files PASSED (4/4), confirming the pytestmark relocation did not affect timeout
    marker application or any test behavior.
- [x] **STEP 5: Code Cleanup**
  - [x] Ran full-default `flake8` (not just `--select=E402`) on the 4 files touched by Step 4;
    confirmed 0 E402 findings and that the 30 pre-existing non-E402 findings (F401 unused
    imports, E501 long lines, W293 trailing-whitespace blank lines) are unchanged in count/type
    from the pre-fix versions (only line numbers shifted by the 2-line relocation) — no new
    warnings introduced.
  - [x] Confirmed the moved `pytestmark` line has correct formatting/indentation/line length in
    all 4 files (diff is exactly a 2-line move per file, verified via `git diff`).
  - [x] Confirmed no unused imports/variables, dead code, or debug prints were introduced by
    Step 4 (it only relocated one existing line).
  - [x] `make test PYTEST_ARGS="tests/test_lint_pytestmark_e402.py"` — PASSED (1/1, 3.93s),
    reconfirming the fix.
  - [x] `ai-tasks/PYPOST-1233/40-code-cleanup.md` created, documenting this as a minimal
    mechanical fix with pre-existing unrelated findings left out of scope.
- [x] **STEP 6: Observability**
  - [x] N/A: this change touches only test-file import/`pytestmark` ordering in
    `tests/test_examples_modernization.py`, `tests/test_examples_modernization_repro.py`,
    `tests/test_ui_library_manager.py`, and `tests/test_ui_library_manager_repro.py`. No
    production code was added or modified and no runtime behavior changed (the fix relocates
    one existing `pytestmark = pytest.mark.timeout(N)` line below the last top-level import to
    satisfy flake8 E402; test execution semantics are unchanged, confirmed in Steps 4-5). There
    is no component, code path, or metric surface to instrument. See
    `ai-tasks/PYPOST-1233/50-observability.md` for the full N/A rationale.
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyzed Steps 4-6 for new debt per the step skill's checklist (shortcuts, code quality,
    missing tests, missing timeout markers, performance, architecture deviations, hardcoded
    values): none found — Step 4 was a minimal 2-line-per-file mechanical move, no shortcuts or
    new debt introduced. All 4 files already carry `pytestmark = pytest.mark.timeout(30)`, so no
    timeout-marker blocker.
  - [x] Documented the 30 pre-existing flake8 findings (16 F401, 12 E501, 2 W293) across the 4
    touched files as a Follow-up Task, classified NON-BLOCKER — pre-existing tech debt (linter
    findings, not failing tests). Re-ran full-default `flake8` on the post-fix files to get exact
    per-file/per-category counts; total (30) matches Step 5's count.
  - [x] Dedup check (read-only `jira_get_issue`/JQL) against PYPOST-1234, PYPOST-1111,
    PYPOST-1251, PYPOST-1252 (all pre-existing test-failure clusters, unrelated to flake8
    findings) and PYPOST-729 (resolved, different files/violations): no existing issue covers
    these findings — needs a NEW follow-up issue (orchestrator to create in Phase D).
  - [x] `ai-tasks/PYPOST-1233/60-tech-debt.md` created using the step skill's template.
  - Left `[/]` per td-roadmap: this executing agent does not own the acceptance gate; the gate
    owner marks `[x]` after review passes.
- [x] **STEP 8: Dev Docs**
  - [x] Searched `doc/dev/` (`grep -ril "pytestmark\|E402" doc/dev/`) for existing
    documentation of the pytestmark-below-imports convention. Found it in
    `doc/dev/testing.md` ("Per-test timeouts (mandatory)" section, written during
    PYPOST-1070): documents the convention, an example, and E402 troubleshooting guidance.
    No file-specific "known exceptions" / "files pending fix" list existed anywhere in
    `doc/dev/` naming the 4 touched files (also checked `doc/dev/test_audit.md`,
    `doc/dev/examples_library_format.md`, `doc/dev/library_manager_ui.md` — none list
    per-file E402 exceptions), so there was nothing to remove them from.
  - [x] Made one small, proportionate addition to `doc/dev/testing.md`'s "Enforcement"
    subsection: a short paragraph noting the repo-wide guard test
    `tests/test_lint_pytestmark_e402.py` (which runs `flake8 --select=E402` over `tests/`)
    and naming the 4 files fixed under PYPOST-1233 as now compliant. No new standalone doc
    file created.
  - Left `[/]` per td-roadmap: this executing agent does not own the acceptance gate; the
    gate owner marks `[x]` after review passes.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1233/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1233/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1233/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1233/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1233/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
