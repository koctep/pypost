# Roadmap: PYPOST-1235

## Task Metadata

- **Implementation language**: Python (test-suite code under `tests/`; no production change)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1235/10-requirements.md` — 10 ACs; open question Q1 (how the
    "no readable manifest" outcome is signalled) deferred to Step 2.
  - Census at HEAD `5e8a9010`: 285 files under `pypost/`, 57 module-level `__all__`, all
    plain list-literal assignments; 0 annotated, 0 augmented, 0 `__all__.<method>()` calls.
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1235/20-architecture.md` — Q1 resolved: `_module_all_exports -> set[str] | None`
    (`None` = no readable literal; handles `ast.AnnAssign`); two single-line diagnostics both
    prefixed `__all__ must export [...]`; new tests in
    `tests/test_display_role_scan_ownership_all_exports.py` (discoverability regions untouched).
- [x] **STEP 3: Failing Repro Test**
  - `tests/test_display_role_scan_ownership_all_exports.py` (`timeout(10)`; seam imported from
    the repro file via underscore names only). Run:
    `make test PYTEST_ARGS="tests/test_display_role_scan_ownership_all_exports.py -p no:randomly -rA"`
    → 11 failed, 5 passed (16 collected), red set matches the 20-architecture tables exactly.
  - E2E red: `accepts_annotated_literal_all[annotated-list|annotated-tuple]` (`found []`);
    `lists_present_names_for_annotated_literal_missing_name` (regex mismatch, got `found []`);
    `reports_unreadable_all_distinctly[bare-annotation|computed|absent]` (regex mismatch, got
    `found []`).
  - E2E green guard: `keeps_found_empty_for_empty_literal_all`.
  - Reader red: `[annotated-list]`, `[annotated-tuple]` (got `set()`); `[computed]`,
    `[bare-annotation]`, `[absent]` (got `set()`, expected `None`).
  - Reader green guards: `[plain-list]`, `[plain-tuple]`, `[empty-literal]`,
    `[bare-then-literal]`.
- [x] **STEP 4: Development**
  - [x] Iteration 1: `_module_all_exports(tree) -> set[str] | None` in
    `tests/test_display_role_scan_ownership.py` now normalises `ast.Assign` /
    `ast.AnnAssign` to one `(targets, value)` pair; list/tuple literal -> names (`set()` if empty),
    bare annotation / computed value skipped, no literal -> `None`; docstring updated. Main test
    hoists the `expected_exports` literal above the call and adds
    `assert tree_exports is not None` with the "no statically readable literal `__all__` found
    (absent, bare annotation, or computed value)" message; the `found [...]` message is unchanged.
    +21/-10 lines, one file; nothing under `pypost/`, repro/independent/aggregate/discoverability
    files and the Step 3 test unedited.
  - [x] Gates: `tests/test_display_role_scan_ownership_all_exports.py` 16/16 passed; ownership
    family (main 1, repro 7, independent 4, aggregate 3, discoverability 20, all_exports 16) all
    green; `make lint`, `make typecheck`, `make verify-ai-tasks` OK; `make check` 364 passed /
    6 skipped / 1 failed file — only the pre-existing `tests/test_pytest_exit_policy.py`
    (PYPOST-1299, 120s file timeout).
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1235/40-code-cleanup.md`
  - Checked both task files by inspection against `.flake8`. `tests/` is outside the `make lint`
    scope (PYPOST-1303) and the `make typecheck` scope. Result: 0 lines over 100, no
    unused imports, no prints, no trailing whitespace.
  - `tests/test_display_role_scan_ownership_all_exports.py`: the module docstring now describes
    the pre-fix reader in the past tense, and `_tree_index_with` has a one-line docstring.
    `tests/test_display_role_scan_ownership.py` is unchanged in this step, with no new `def`
    (AC-8).
  - Gates: `make lint` OK; `make typecheck` OK (baseline); ownership family `make test` 6/6
    files passed.
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1235/50-observability.md` documents the two deterministic ownership
    assertion diagnostics: unreadable manifest versus readable literal missing names.
  - Runtime logs and metrics are N/A: this is a static test helper, with no production changes.
    Diagnostic formatting and owner context checked by source inspection.
  - Validation: `make test
    PYTEST_ARGS="tests/test_display_role_scan_ownership_all_exports.py -p no:randomly -rA"`
    passed (1 file, 16 cases; 0 failed).
  - `make lint` passed (production flake8, Markdown lint, relative link checks); test-code
    diagnostic inspection supplements the existing lint scope gap (PYPOST-1303).
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1235/60-tech-debt.md`: no new scope-related blocker or follow-up;
    accepted static-reader limitations and private test-seam coupling documented.
  - All 16 regression cases cover the accepted manifest/diagnostic contract; both changed test
    modules have explicit `timeout(10)` markers. Existing Step 4–6 evidence reused.
  - Existing non-blockers linked: PYPOST-1299 exit-policy file timeout (no individual failing
    node retained in artifacts) and PYPOST-1303 exclusion of tests from flake8 lint scope.
    Typecheck scope limitation disclosed; Step 8 developer documentation remains pending.
- [x] **STEP 8: Dev Docs**
  - `doc/dev/ui_actions.md`: documents plain/annotated literal lists and tuples,
    `_module_all_exports(tree) -> set[str] | None`, empty versus unreadable results,
    static-reader limits, distinct diagnostics and remedies, and focused Make validation.
  - `make lint-docs verify-ai-tasks` passed (16 Markdown files, 18 link-check files,
    390 completed tasks; 2 grandfathered legacy gaps). The documentation lint/link targets
    cover user docs/README files, so the changed developer-doc paragraphs were checked by
    source inspection against the accepted helper, caller diagnostics and architecture.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1235/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1235/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1235/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1235/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1235/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/ui_actions.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
