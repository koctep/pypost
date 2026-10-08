# Roadmap: PYPOST-1238

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Independent requirements re-review passed; orchestrator accepted Step 1.
- [x] **STEP 2: High-Level Architecture Design**
  - Independent architecture review passed; orchestrator accepted Step 2.
- [x] **STEP 3: Failing Repro Test**
  - Independent review reproduced the intended red cases; orchestrator accepted Step 3.
  - Added focused source-string reference and misleading-loop regressions in
    `tests/test_display_role_scan_ownership_repro.py`; helper implementation unchanged.
  - Red command: `make test WORKERS=1` with
    `PYTEST_ARGS='tests/test_display_role_scan_ownership_repro.py'`.
  - Result: 8 failed, 17 passed; Make exit 2. All failures assert `True is False`, proving
    incorrect recognition rather than fixture/import failure. Existing seven tests pass.
  - Failing node prefix: `tests/test_display_role_scan_ownership_repro.py::`.
    Reference test: `test_find_child_guard_recognizes_supported_references`, with IDs
    `child-substring-delegation`, `child-substring-forbids-inline-display-role`,
    `uppercase-child-substring-delegation`,
    `uppercase-child-substring-forbids-inline-display-role`,
    `full-name-substring-delegation`, `full-name-substring-forbids-inline-display-role`.
    Loop test: `test_find_child_guard_rejects_tree_only_loop`, with IDs `delegation` and
    `forbids-inline-display-role`. Complete nodes concatenate prefix, test, and `[ID]`.
  - Supported names/lookups and unrelated tree references pass for both predicates.
    New tests inherit the explicit ten-second module timeout; Step 3 review pending.
- [x] **STEP 4: Development**
  - Independent implementation review passed; orchestrator accepted Step 4.
  - Implemented exact membership for every bare name; preserved non-name AST-dump fallback.
    Updated the helper description without changing either consuming predicate.
  - Green: `make test WORKERS=1` with `PYTEST_ARGS` selecting
    `tests/test_display_role_scan_ownership_repro.py` and
    `tests/test_display_role_scan_ownership.py`; both files pass (2.73 seconds).
  - `make lint` passed. `make typecheck` passed against the unchanged 181-error baseline.
  - All eight Step 3 failures resolved; no production or Qt changes. Review pending.
- [x] **STEP 5: Code Cleanup**
  - Independent cleanup review passed; orchestrator accepted Step 5.
  - Reviewed the focused diff; no further code or formatting changes needed.
  - `make analyze` unavailable; documented repository `make lint` passed instead.
  - `make verify-ai-tasks` passed (393 completed tasks; two legacy gaps).
  - Prior targeted tests/type gate remain green; no code changes since those checks.
    Cleanup report prepared for independent review.
- [x] **STEP 6: Observability**
  - Independent observability review passed; orchestrator accepted Step 6.
  - Assessed test-only classifier paths; application logs and metrics are not applicable.
  - Existing pytest parameter IDs, assertion context, and Make test reporting provide
    diagnostics. Recorded source evidence and red-to-green validation; review pending.
- [x] **STEP 7: Technical Debt Analysis**
  - Independent debt review passed; orchestrator accepted Step 7.
  - Reviewed classifier change and both-consumer regressions against accepted scope.
  - No new actionable debt or blockers identified; documented retained fallback limitation
    and excluded PYPOST-1236 work. Independent review pending.
- [x] **STEP 8: Dev Docs**
  - Independent documentation review passed; orchestrator accepted Step 8.
  - Updated the existing DisplayRole ownership guard section in `doc/dev/ui_actions.md`
    with exact-name behavior, fallback boundary, focused regressions, and troubleshooting.
    Documentation review pending.
  - `make lint` and `make verify-ai-tasks` passed. Test suites were not repeated for docs only.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1238/10-requirements.md`
- Captured the confirmed false-green risk, supported reference behavior, and focused scope.
- Step 1 artifacts prepared for independent review; acceptance remains pending.

### STEP 2: Architecture

- `ai-tasks/PYPOST-1238/20-architecture.md`
- Designed strict bare-name recognition with preserved non-name lookup compatibility.
- Defined self-contained AST regressions for both ownership predicates; review pending.

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1238/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1238/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1238/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
