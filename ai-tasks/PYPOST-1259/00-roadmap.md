# Roadmap: PYPOST-1259

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1259/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1259/20-architecture.md` — Structural Markdown AST parser and resilient
    contract verification architecture design.
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_pypost_1259_failing_repro.py`
- [x] **STEP 4: Development**
  - [x] Implemented structural Markdown AST helpers (`MarkdownSection`,
    `_parse_markdown_sections`, `_parse_markdown_table`, `_normalize_prose`) and
    resilient `_section` backward compatibility.
  - [x] Refactored `test_dialog_audit_report_has_full_discovery_and_coherent_aggregates`
    to decouple active disk LOC drift from static report invariants and use normalized
    prose / AST parsing.
  - [x] Updated `tests/test_pypost_1259_failing_repro.py` to verify AST parsing,
    table padding, and reflowed prose validation pass green.
- [x] **STEP 5: Code Cleanup**
  - [x] Code formatting, linter verification, typechecking, and test validation
  - [x] Create 40-code-cleanup.md
- [x] **STEP 6: Observability**
  - [x] Diagnostic error reporting and test harness observability analysis
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Technical debt, shortcuts, edge cases, and pre-existing follow-ups analyzed
- [x] **STEP 8: Dev Docs**
  - [x] Document structural Markdown AST parsing in
    `doc/dev/verification_artifact_contracts.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1259/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1259/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1259/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1259/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1259/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/verification_artifact_contracts.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are
  reported in chat only, never written to this file.
