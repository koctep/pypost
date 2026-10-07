# Roadmap: PYPOST-1287

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - Requirements: `ai-tasks/PYPOST-1287/10-requirements.md`
  - Repro at `aef30005`:
    `make test WORKERS=1 PYTEST_ARGS='tests/test_pypost_1077_verification_artifacts.py -q'`
    reports 1 file passed (4 tests passed). The test no longer fails as Jira describes: PYPOST-1259
    (`23e66c84`) dropped the check that compares discovered LOC with the report, so the
    test now checks only that the report is consistent with itself.
  - The underlying defect is still present. The report says 1,790 LOC, but discovery finds 2,505 LOC
    (`library_dialogs.py` 533 → 703, `mcp_servers_dialog.py` 486 → 1,031; the other seven are
    unchanged). The guard is green but no longer catches this drift.
  - Scope restated as: refresh the report, restore drift detection against discovery
    with no pinned snapshot figures, and align the dev docs that cite 1,790/486.
- [x] **STEP 2: High-Level Architecture Design**
  - Architecture: `ai-tasks/PYPOST-1287/20-architecture.md`
  - Design: pure validator `_dialog_audit_report_errors(report_markdown, modules)` in
    `tests/test_pypost_1077_verification_artifacts.py`; all expected values derived from
    `discover_dialog_modules()` (rules R1-R7, per-case messages with recorded vs discovered,
    ints printed);
    live test becomes a thin wrapper; PYPOST-1259 helper signatures frozen. Count checks only
    on the Scope count and Verdict phrase; no automated prose-figure rule (`At 263 LOC` is
    re-checked by the hand refresh).
  - Refresh decision: hand edit of the PYPOST-374 report (script `--markdown` schema differs and
    has no make target); `make test` failure output is the refresh oracle.
  - Docs: rewrite current contract text in `doc/dev/verification_artifact_contracts.md`;
    keep the PYPOST-1111 entry in `doc/dev/solid_audit.md`.
  - Failing repro design: `tests/test_pypost_1287_failing_repro.py` — synthetic discovery and
    report via monkeypatch of module-level seams (5 cases, all red at `aef30005`); value
    assertions require both values on one message line (regex per line).
- [x] **STEP 3: Failing Repro Test**
  - Red test: `tests/test_pypost_1287_failing_repro.py` (module `timeout(10)`; monkeypatch
    seam on the 1077 module globals `discover_dialog_modules` / `check_audit_report_covers` /
    `_DIALOG_AUDIT_REPORT`; synthetic report under `tmp_path`; per-line `_any_line_matches`).
  - Run at `aef30005`:
    `make test WORKERS=1 PYTEST_ARGS='tests/test_pypost_1287_failing_repro.py -q'` →
    5 failed, all for the intended reason (no import, fixture or timeout errors):
    - Case 1 (coherent synthetic report): pinned checks fire (`exactly nine modules`,
      `sum to 1,790 (got 200)`, `mcp_servers_dialog.py at 486`, scope/verdict `nine`).
    - Case 2 (per-module drift): no line names `alpha_dialog.py` with 100 and 120.
    - Case 3 (missing/unknown): generic `cover every discovered dialog exactly once`; neither
      `gamma_dialog.py` nor `ghost_dialog.py` is named.
    - Case 4 (aggregate drift): no `declared 3 ... discovered 2` or
      `declared 999 ... discovered 200` line.
    - Case 5 (live drift): `library_dialogs.py` 533 != 703, `mcp_servers_dialog.py` 486 != 1031.
  - Unchanged existing tests still pass: `tests/test_pypost_1077_verification_artifacts.py`,
    `tests/test_pypost_1259_failing_repro.py`.
  - Review fix: `_run_contract_expecting_failure` keeps only the custom message (drops
    pytest's `assert not [...]` line) so each line is one error; case 2 regex uses `\D+`.
- [x] **STEP 4: Development**
  - [x] Iteration 1 (check): `tests/test_pypost_1077_verification_artifacts.py` gains the pure
    `_dialog_audit_report_errors(report_markdown, modules)` (R1-R7) with helpers `_parse_int`,
    `_parse_count`, `_inventory_errors`, `_aggregate_errors` (R4 LOC only),
    `_module_count_errors` (R5, sole module-count source), `_testability_errors`; every expected
    value comes from `modules`. Live test is a thin wrapper over the module-global seams.
    PYPOST-1259 helpers unchanged; semantic phrases and stale-claim denylist kept verbatim
    (moved to module constants). Repro cases 1-4 green; live test then lists the drift:
    `library_dialogs.py` 533 != 703, `mcp_servers_dialog.py` 486 != 1031, row sum / Scope /
    Total 1790 != 2505.
  - [x] Iteration 2 (report): `ai-tasks/PYPOST-374/30-dialogs-audit-report.md` hand-refreshed
    from that output: rows 703 / 1,031, Scope and Total 2,505, `Inventory refreshed` line,
    `The 486-LOC dialog` -> `The dialog`, direct-script `Regenerate counts` line replaced by the
    make-only verify command. `At 263 LOC` re-checked against discovery (unchanged). Case 5 and
    the live 1077 test green.
  - [x] Iteration 3 (docs): `doc/dev/verification_artifact_contracts.md` Contract Architecture
    paragraph and PYPOST-1259 invariants 1-4 rewritten with no snapshot figures; validator and
    message shapes described. `doc/dev/solid_audit.md` PYPOST-1111 entry left as written.
  - Gates: `make test WORKERS=1 PYTEST_ARGS='tests/test_pypost_1287_failing_repro.py
    tests/test_pypost_1077_verification_artifacts.py tests/test_pypost_1259_failing_repro.py -q'`
    3/3 files passed; `tests/test_dialogs_audit.py` passed; `make lint` OK; `make typecheck`
    baseline OK (181 known); `make verify-ai-tasks` OK.
- [x] **STEP 5: Code Cleanup**
  - Cleanup report: `ai-tasks/PYPOST-1287/40-code-cleanup.md`
  - Cleanup: renamed `_module_count_errors` param `n` -> `module_count`; repro module docstring
    made past-tense (assertions/regexes untouched); no unused imports, dead code or long lines.
  - Gates: `make lint` OK; `make typecheck` baseline OK (181); `make verify-ai-tasks` OK;
    targeted `make test` 4/4 files passed.
  - `make check`: 368 files, 361 passed, 1 failed, 6 skipped; the only failure is
    `tests/test_pytest_exit_policy.py` (PYPOST-1299, filed pre-existing). No new failures.
- [x] **STEP 6: Observability**
  - Observability report: `ai-tasks/PYPOST-1287/50-observability.md`
  - Conclusion: no production logging or metrics. `git diff --stat -- pypost scripts` is empty
    (only test code, one ai-tasks report and one dev doc changed).
  - Diagnostic surface: validator failure-message contract (R1-R7). One line per violation, with
    module name and recorded/discovered values, e.g. `<file>: recorded LOC r != discovered LOC d`,
    `<label>: declared x != discovered y`, missing/unknown/duplicate module lines.
  - No logging added to test code. Monitoring integration N/A, with reasons in the report.
- [x] **STEP 7: Technical Debt Analysis**
  - Tech-debt report: `ai-tasks/PYPOST-1287/60-tech-debt.md` (TD-1..TD-13, no BLOCKER; both
    changed test modules carry `timeout(10)`).
  - New follow-ups proposed (not filed in this step): TD-1+TD-2+TD-7 count/figure-agnostic
    stale-claim and prose rules (Medium); TD-3+TD-4 make target and report-schema refresh for
    `scripts/audit_dialogs_inventory.py` (Medium); TD-6 SOLID re-audit of
    `mcp_servers_dialog.py` / `library_dialogs.py` (Medium); TD-8 extract validator and
    markdown helpers to a shared test module (Low).
  - Existing, not re-filed: TD-5 PYPOST-1303 (flake8 on `tests/`); TD-13 PYPOST-1299
    (`NON-BLOCKER — pre-existing`, `tests/test_pytest_exit_policy.py`).
  - Note for Step 8: fix the Troubleshooting "Regenerate the inventory" text in
    `doc/dev/verification_artifact_contracts.md` (TD-3).
- [x] **STEP 8: Dev Docs**
  - `doc/dev/verification_artifact_contracts.md`: Troubleshooting "Regenerate the inventory"
    replaced by the hand-refresh procedure (recorded vs discovered values from the failure
    message, prose re-check, `make test WORKERS=1 PYTEST_ARGS=...1077...` verify, make target
    in PYPOST-1307); one-line PYPOST-1307 note under the Usage raw-script calls (calls kept);
    regression-coverage paragraph naming `tests/test_pypost_1287_failing_repro.py`; new
    "Known Limitations" subsection (PYPOST-1308, PYPOST-1310).
  - `doc/dev/testing.md`, `doc/dev/README.md`: unchanged. Task repros are cited in the feature
    doc, not in `testing.md`; the README index already links the contracts doc. Raw script
    calls there and in `doc/dev/solid_audit.md` are left to PYPOST-1307.
  - `doc/dev/solid_audit.md`: PYPOST-1111 changelog entry left as written.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1287/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1287/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1287/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1287/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1287/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
