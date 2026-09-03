# Roadmap: PYPOST-1252

## Task Metadata

- **Implementation language**: Python 3.11+

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - `ai-tasks/PYPOST-1252/10-requirements.md` — corrected business requirements for
    synchronizing the dialog-audit record to the source-authoritative settings inventory.
  - Scope correction: `settings_dialog.py` is 263 LOC while the frozen report/test record says
    260 LOC; the source-authoritative aggregate is 1790 LOC rather than 1787 LOC.
  - `mcp_servers_dialog.py` is 486 LOC and matches its recorded value, so it is outside the
    corrected scope.
  - Step 1 accepted after independent requirements review.
- [x] **STEP 2: High-Level Architecture Design**
  - `ai-tasks/PYPOST-1252/20-architecture.md` — corrected architecture for synchronizing the
    source-authoritative `settings_dialog.py` value of 263 LOC and the 1790-LOC aggregate.
  - Preserves `mcp_servers_dialog.py` at 486 LOC and leaves production behavior and audit policy
    unchanged.
  - Defines the existing offline contract test as the mandatory Step 3 red repro before the
    contract expectation and PYPOST-374 report are updated together.
  - Step 2 accepted after independent architecture review.
- [x] **STEP 3: Failing Repro Test**
  - Red repro test module: `tests/test_pypost_1077_verification_artifacts.py`.
  - Red repro test name: `test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`.
  - Command: `make test PYTEST_ARGS='tests/test_pypost_1077_verification_artifacts.py'`
  - Result: exit 2; 1 failed and 3 passed in the focused test file.
  - Failure evidence: the red test reports that discovery must total 1,787 LOC and that the
    module inventory does not match discovery.
  - Mismatch evidence: source `settings_dialog.py` is 263 LOC, while the frozen report records
    260 LOC and 1,787 LOC in its aggregate; current discovery is 1,790 LOC. The unchanged
    `mcp_servers_dialog.py` source is 486 LOC, matching its recorded value.
  - No production, test, audit-report, requirements, or architecture files were changed in
    Step 3. Step accepted after independent red-repro review.
- [x] **STEP 4: Development**
  - [x] Synchronized the contract aggregate from 1,787 to 1,790 LOC.
  - [x] Updated the directly affected `settings_dialog.py` inventory row from 260 to 263 LOC.
  - [x] Preserved exact inventory/set/MCP checks and `mcp_servers_dialog.py` at 486 LOC.
  - [x] Confirmed the reviewed red repro passes with the synchronized artifacts.
- [x] **STEP 5: Code Cleanup**
  - `ai-tasks/PYPOST-1252/40-code-cleanup.md` — reviewed formatting, line length, whitespace,
    merge markers, and the explicit pytest timeout contract.
  - `make analyze` is unavailable because the repository has no `analyze` target; `make lint`
    was used as the applicable analysis target.
  - Focused contract test and `make verify-ai-tasks` passed. No production cleanup or unrelated
    refactoring was performed.
- [x] **STEP 6: Observability**
  - `ai-tasks/PYPOST-1252/50-observability.md` — documenting that this audit
    artifact synchronization adds no production behavior, logging, metrics, or
    monitoring paths.
- [x] **STEP 7: Technical Debt Analysis**
  - `ai-tasks/PYPOST-1252/60-tech-debt.md` — analysis of the artifact-only scope correction,
    including known frozen audit-count tradeoffs and pre-existing full-suite failures.
  - Independent technical-debt review passed; separate blocker review: SAFE TO CLOSE.
- [x] **STEP 8: Dev Docs**
  - `doc/dev/verification_artifact_contracts.md` — synchronized the dialog-audit contract with
    the source-authoritative inventory: nine modules, 1,790 LOC total, and
    `mcp_servers_dialog.py` at 486 LOC; retained the three-MCP-dialog summary and contract
    meaning.
  - Validation: `make lint`, `make verify-ai-tasks`, and the focused artifact contract test all
    passed.
  - Independent documentation review passed; no unrelated documentation or implementation changes.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1252/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1252/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1252/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1252/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1252/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
