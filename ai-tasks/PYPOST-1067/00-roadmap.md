# Roadmap: PYPOST-1067

## Task Metadata

- **Implementation language**: Python
- **Suggested branch name**: `fix/PYPOST-1067-derive-mypy-parser-scope`
- **Delivery branch**: `dev` (existing sprint branch; no branch switch performed)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Artifact: `ai-tasks/PYPOST-1067/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - Artifact: `ai-tasks/PYPOST-1067/20-architecture.md`
  - Design: derive the anchored diagnostic regex from escaped, boundary-aware `MYPY_PATHS`
  - Step 3 plan: hermetically extend scope in a temporary module copy and prove parsing drift
- [x] **STEP 3: Failing Repro Test**
  - Red test:
    `tests/test_mypy_baseline.py::TestMypyBaseline::`
    `test_configured_path_extension_drives_diagnostic_parsing`
  - Evidence: the exact-node Makefile run excludes `pypost/agent_extra/...` but fails with
    `assert [] == [MypyError(...)]` because the newly configured `pypost/agent/...` diagnostic
    remains unparsed
- [x] **STEP 4: Development**
  - [x] Derived the import-time diagnostic path alternation from escaped `MYPY_PATHS`,
    ordered longest-first with a lexical tie-break and retaining the literal slash boundary
  - [x] Made the reviewed configured-path repro green and added a focused companion test for
    regex metacharacter escaping and deterministic overlap ordering
  - [x] Verified the exact repro and all 22 mypy-baseline tests; changed-code lint passes apart
    from pre-existing `T201` findings reproduced at base commit `3f97f904`
  - [x] Ran `make test`; all PYPOST-1067 coverage passed, while three unrelated guardrail
    failures reproduced unchanged at base commit `3f97f904`
  - [x] Refactored temporary-module test setup to discover the `MYPY_PATHS` assignment by
    syntax, derive the extension case from the imported tuple, and avoid duplicating scope
    members while preserving fresh `runpy` imports
- [x] **STEP 5: Code Cleanup**
  - [x] Artifact: `ai-tasks/PYPOST-1067/40-code-cleanup.md`
  - [x] Inspected the accepted Step 4 diff; no behavior-neutral source or test cleanup was needed
  - [x] Verified repository lint, changed-file lint and syntax, both focused tests, the full
    mypy-baseline module, conflict-marker absence, explicit timeouts, and `git diff --check`
  - [x] Reproduced unrelated typecheck drift at base commit `3f97f904` and retained the three
    previously classified pre-existing full-suite failures as non-blockers
- [x] **STEP 6: Observability**
  - [x] Artifact: `ai-tasks/PYPOST-1067/50-observability.md`
  - [x] N/A for production changes: the import-time derivation needs no new logs or metrics
  - [x] Documented existing stdout/stderr reports, exit codes, scope metadata, CI visibility,
    error behavior, and privacy constraints
  - [x] Preserved the baseline gate's existing CLI/reporting interface and avoided noisy or
    sensitive instrumentation
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Artifact: `ai-tasks/PYPOST-1067/60-tech-debt.md`
  - [x] Found no in-scope debt, missing coverage, performance concern, architecture deviation,
    blocker, or unticketed follow-up
  - [x] Linked the three pre-existing suite failures to To Do issues PYPOST-1110/PYPOST-1111
    and the pre-existing typecheck drift to To Do sprint issue PYPOST-1086
  - [x] Classified seven pre-existing `T201` CLI prints as intentional reporting behavior, not
    debug output or an evidence-backed follow-up
- [x] **STEP 8: Dev Docs**
  - [x] Updated `doc/dev/static_type_checking.md`
  - [x] Documented `MYPY_PATHS` as the single authority for invocation, baseline scope metadata,
    success output, and accepted diagnostic prefixes
  - [x] Documented prefix escaping, longest-first overlap ordering, the required slash boundary,
    and the one-edit scope-extension workflow
  - [x] Preserved the guide's accurate `make typecheck` optional and not-in-CI wording
- [x] **COMMIT: Commit Changes**
  - Primary commit: `b11babda` — `fix(typecheck): PYPOST-1067 derive parser scope from paths`

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1067/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1067/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1067/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1067/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1067/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- `b11babda` — `fix(typecheck): PYPOST-1067 derive parser scope from paths`
