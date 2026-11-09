# Roadmap: PYPOST-1492

## Task Metadata

- **Implementation language**: Python
- **Jira**: [PYPOST-1492](https://pypost.atlassian.net/browse/PYPOST-1492) — Debt (2 SP), Medium
- **Sprint**: Test Gate Recovery

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Gathered requirements from Jira PYPOST-1492 and PYPOST-1324 tech-debt triage
  - [x] Confirmed failing gate in `tests/test_solid_audit_baseline.py`
        (`TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`)
  - [x] Documented business goals, scope, entities, and DoD in
        `ai-tasks/PYPOST-1492/10-requirements.md`
  - Acceptance: reviewed externally (PASS)
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Researched SOLID audit stack (`audit_baseline_metrics.py`, snapshot,
        equality gate) and industry baseline+drift-gate patterns
  - [x] Confirmed Make-only: equality test red; `make check-baseline-metrics` green
  - [x] Documented modules, interfaces, Mermaid diagram, and Step 3 red-test plan
        in `ai-tasks/PYPOST-1492/20-architecture.md`
  - [x] Scope: regenerate `ai-tasks/PYPOST-376/baseline-metrics.md` only; no cap /
        assertion / runtime changes (observed drift: `http_client.py` 378→395)
  - Acceptance: reviewed externally (PASS)
- [x] **STEP 3: Failing Repro Test**
  - [x] Confirmed existing red equality gate (no new test; no snapshot regen;
        no production fix):
        `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`
  - [x] Make repro confirmed RED (committed snapshot ≠ live metrics)
  - Acceptance: reviewed externally (PASS)
- [x] **STEP 4: Development**
  - [x] Regenerated `ai-tasks/PYPOST-376/baseline-metrics.md` via
        `make baseline-metrics` (http_client Baseline LOC 378→395; caps unchanged)
  - [x] Confirmed `make check-baseline-metrics` green (no cap raises)
  - [x] Confirmed Step 3 equality test green:
        `tests/test_solid_audit_baseline.py` (full module) PASSED via `make test`
  - [x] `make check`: Step 3 target green; remaining reds triaged vs base
        `369b96a5` — all pre-existing/flaky, linked Debt (incl. new PYPOST-1552
        for flaky MCP process reconfigure); see
        `ai-tasks/PYPOST-1492/60-tech-debt.md`
  - Acceptance: reviewed externally (PASS)
- [x] **STEP 5: Code Cleanup**
  - [x] Snapshot-only: no runtime Python to format/clean
  - [x] `make lint`, `make typecheck`, `make check-baseline-metrics` OK
  - [x] Equality gate green; report `40-code-cleanup.md`
  - Acceptance: reviewed externally (PASS)
- [x] **STEP 6: Observability**
  - [x] N/A for new logs/metrics — existing SOLID gates remain the signal
  - [x] Report: `50-observability.md`
  - Acceptance: reviewed externally (PASS)
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Full analysis; suite NON-BLOCKERs with Jira links; no DoD blockers
  - [x] Report: `60-tech-debt.md`
  - Acceptance: reviewed externally (SAFE TO CLOSE)
- [x] **STEP 8: Dev Docs**
  - [x] N/A — procedure already in `doc/dev/solid_audit.md` / `testing.md`
  - Acceptance: reviewed externally (PASS)
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1492/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1492/20-architecture.md`

### STEP 3: Failing Repro

- Existing red (no new test):
  `tests/test_solid_audit_baseline.py::TestSolidAuditBaseline::test_markdown_snapshot_matches_current_metrics`
- Failure mode: `AssertionError` exact UTF-8 inequality; committed Baseline LOC
  `378` vs live `395` (http_client row); caps not involved

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1492/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1492/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1492/60-tech-debt.md`

### STEP 8: Dev Docs

- N/A — no `doc/dev/` changes (justification under STEP 8 status)

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are
  reported in chat only, never written to this file.
