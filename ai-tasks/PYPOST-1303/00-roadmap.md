# Roadmap: PYPOST-1303

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Documented routine quality feedback for test-source regressions through existing Make gates.
  - Artifact: `ai-tasks/PYPOST-1303/10-requirements.md`.
  - Business reason supplied by the issue: unused imports and other test quality defects escape
    normal lint feedback because test sources are outside its current scope.
  - Preserved existing production lint obligations and automated test coverage in requirements.
  - Requirements complete for independent review; STEP 1 remains in progress until acceptance.
- [x] **STEP 2: High-Level Architecture Design**
  - Measuring legacy test-source lint findings before selecting an adoption policy.
  - Artifact: `ai-tasks/PYPOST-1303/20-architecture.md`.
  - Make-only analysis found 409 existing test findings; flake8-print is installed, T201 is zero.
  - Selected a transparent test-only occurrence baseline with strict parsing and prune-only ratchet.
  - Preserved production/docs checks; isolated Make fixtures receive real checker assets.
  - Designed meaningful Make lint red tests for new test F401/E501/T201 and clean/production cases.
  - Architecture complete for independent review; STEP 2 remains in progress until acceptance.
- [x] **STEP 3: Failing Repro Test**
  - Creating private offline Make lint gate regressions before implementation.
  - Added `tests/test_makefile_test_lint_gate.py` with an explicit 60-second module timeout
    and 20-second bounded Make subprocess calls. Fixtures use the installed repository
    interpreter, private clean trees, and satisfied local stamps; no package installation runs.
  - Exact red command: `make test PYTEST_ARGS='tests/test_makefile_test_lint_gate.py'`.
    Output captured in `/tmp/pypost-1303-step3-red.log`; normal eight-worker runner retained.
  - Result: Make exit 2; exactly 3 intended failures and 2 passing controls, without timeouts.
  - In `tests/test_makefile_test_lint_gate.py`,
    `test_make_lint_rejects_new_test_source_defects[F401]`, `[E501]`, and `[T201]` fail because
    actual Make returns zero and prints only `.venv/bin/python -m flake8 --jobs=1 pypost/`.
    Failure excerpts: `AssertionError: make lint accepted new test F401`, and the equivalent
    E501/T201 assertions. These defects are confined to private test files.
  - `test_make_lint_accepts_clean_test_and_production_sources` passes;
    `test_make_lint_still_rejects_production_unused_import` also passes with actual F401 feedback.
  - Every case asserts no `pip install` appeared; no skips/xfails or Make/helper/checker/baseline
    implementation edits were made. STEP 3 remains `[/]` pending independent review.
- [x] **STEP 4: Development**
  - Implementing strict schema/diagnostic identities, then Make integration and error regressions.
  - Iteration 1: added narrow diagnostic/source identities and validated schema primitives.
  - Iteration 2: added strict baseline parsing, bounded plugin-required scan, and occurrence diff.
  - Iteration 3: added read-only gate diagnostics and atomic prune-only baseline updates.
  - Iteration 4: wired lint-tests/prune into Make lint and seeded real lint assets into fixtures.
  - One-time Make-only capture asserted exactly 409 legacy findings (375 unique identities).
    Baseline source/message fragments are bounded to 60 characters; committed JSON stays
    within 100 columns. No new test defects were accepted into the baseline.
  - Iterations 5–7: added checker regressions for duplicate growth, changed same-file source,
    stale debt ratcheting, prune refusal/atomic cleanup, schemas, source escapes, tool failures,
    plugin requirement, contradictory output, and bounded timeout/launch failures.
  - Green repro: `make test PYTEST_ARGS='tests/test_makefile_test_lint_gate.py'`, exit 0;
    all five original repro/control cases pass. Log: `/tmp/pypost-1303-step4-gate.log`.
  - Focused checker/gate verification: `make test PYTEST_ARGS='tests/test_test_lint_baseline.py
    tests/test_makefile_test_lint_gate.py'`, exit 0, both files pass in 3.45 seconds.
    Arguments form one line. Log: `/tmp/pypost-1303-step4-focused.log`.
  - `make lint` passes with 409 accepted legacy occurrences and unchanged production/docs
    checks; log `/tmp/pypost-1303-step4-lint.log`. Checker-only static analysis also passes
    through `make -f /tmp/pypost-1303-analysis.mk analyze-checker`.
  - Affected fixture command: `make test PYTEST_ARGS='tests/test_makefile_exit_behavior.py
    tests/test_makefile_target_filtering.py tests/test_makefile_recipes.py
    tests/test_makefile_shared_readiness.py tests/test_makefile_install_seed_contract.py'`.
    Arguments form one line. Three suites pass; the two lint-success nodes fail with existing
    flake8 reporter `KeyError: 'default'`, correctly propagated by the new fail-closed scan.
    Current evidence: `/tmp/pypost-1303-step4-fixtures.log`. Exact node ids join module/suffix:
    - `tests/test_makefile_exit_behavior.py` +
      `TestExitBehavior::test_lint_succeeds_from_bare_venv_via_venv_test`.
    - `tests/test_makefile_target_filtering.py` +
      `TestTargetFiltering::test_lint_succeeds_after_install`.
  - Reporter baseline provenance: the normal check logged in `/tmp/pypost-1299-step4-check.log`
    reproduced both exact nodes on the tree subsequently committed as `be94b7e4`. Historical
    isolated `fd830ea8` evidence in `/tmp/pypost-1298-step4-baseline-reporter.log` confirms the
    same failures. This is existing PYPOST-1363, not a fresh `be94b7e4` worktree rerun.
  - Final normal `make check`: test lint accepts exactly 409 existing occurrences; production
    lint and documentation/link checks pass. Eight-worker full suite: 395 files, 383 passed,
    5 failed, 7 unchanged skips; 250.31 seconds; no timeout or task-caused failure.
    Full log: `/tmp/pypost-1303-step4-check.log`; Make exit 2 from known baseline test failures.
  - All five failed node ids match `/tmp/pypost-1299-step4-check.log` on the tree subsequently
    committed as base `be94b7e4`: the reporter pair above (PYPOST-1363), and these snapshot nodes
    (PYPOST-1361), written as module + suffix joined with `::`:
    - `tests/test_pypost_1077_verification_artifacts.py` +
      `test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`.
    - `tests/test_pypost_1287_failing_repro.py` +
      `test_live_report_inventory_loc_matches_discovery`.
    - `tests/test_solid_audit_baseline.py` +
      `TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`.
    Existing tracked baseline failures are NON-BLOCKER; no application or snapshot edits made.
  - `make verify-ai-tasks` passes separately because Make stopped before artifact verification
    after the known test failures. Log: `/tmp/pypost-1303-step4-artifacts.log`.
  - Development implementation complete for independent review; STEP 4 remains `[/]`.
- [x] **STEP 5: Code Cleanup**
  - Reviewing formatting, baseline fragments, timeout declarations, and scoped static analysis.
  - Artifact: `ai-tasks/PYPOST-1303/40-code-cleanup.md`.
  - Shortened changed Make help text and removed redundant exception subclasses without
    changing error behavior. No unused imports, debug prints, or broad formatting edits needed.
  - `make lint` and scoped Make checker/format verification pass; checker suite passes after
    cleanup via `make test PYTEST_ARGS='tests/test_test_lint_baseline.py'`.
  - Retained accepted full gate evidence and exact tracked baseline exceptions; no broad rerun.
  - Cleanup complete for independent review; STEP 5 remains `[/]` until acceptance.
- [x] **STEP 6: Observability**
  - Reviewing actionable CLI output and the developer-tool observability boundary.
  - Artifact: `ai-tasks/PYPOST-1303/50-observability.md`.
  - Existing CLI output covers live finding locations, resolved allowance counts/prune guidance,
    accepted legacy counts, and explicit schema/source/tool failure reasons with exit status.
  - Production metrics/log integration N/A: finite developer/CI tooling, no application path changes.
  - Reused validated Make and checker diagnostic evidence; no runtime changes or repeated tests.
  - Observability complete for independent review; STEP 6 remains `[/]` until acceptance.
- [x] **STEP 7: Technical Debt Analysis**
  - Assessing accepted baseline limitations, gate assumptions, and tracked full-suite exceptions.
  - Artifact: `ai-tasks/PYPOST-1303/60-tech-debt.md`.
  - Disclosed authorized 409-occurrence adoption, exact multiset identity limitations,
    prune-only ratchet, finite tool timeout, version assumptions, and stable-checkout boundary.
  - No acceptance-critical missing tests or new concrete follow-up issue identified.
  - Recorded existing PYPOST-1363/1361 exceptions with exact node ids, logs, and base provenance.
  - Technical debt analysis complete for independent review; STEP 7 remains `[/]`.
- [x] **STEP 8: Dev Docs**
  - Updating developer lint workflow, baseline policy, and troubleshooting documentation.
  - Updated `doc/dev/testing.md` with gate architecture, Make usage, occurrence identity/count
    boundaries, stale allowance/prune-only policy, configuration/assets/plugin requirements,
    60-second scan bound, real fixture seeding, and actionable troubleshooting.
  - Corrected the older test-lint scope statements and updated `doc/dev/setup.md` to link the
    current workflow. No code, tests, or automatic acceptance/baseline refresh mode added.
  - `make lint` passes with 409 accepted occurrences and production/docs checks; log
    `/tmp/pypost-1303-step8-lint.log`.
  - Added developer prose/links validate via
    `make -f /tmp/pypost-1303-analysis.mk verify-doc-changes`, exit 0 (71 added lines);
    log `/tmp/pypost-1303-step8-docs.log`. Existing unrelated long documentation lines preserved.
  - Documentation complete for independent review; STEP 8 remains `[/]` until acceptance.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1303/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1303/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1303/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1303/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1303/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
