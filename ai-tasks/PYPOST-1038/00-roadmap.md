# Roadmap: PYPOST-1038

**Programming language:** Python

## STEP 1 Approval Record

The autonomous `sprint-runner` workflow preauthorizes continuation without a
separate user gate. An independent requirements review completed with PASS and
no findings before STEP 1 was marked complete.

## STEP 2 Approval Record

The autonomous `sprint-runner` workflow preauthorizes continuation without a
separate user gate. An initial independent review identified a native-JSON-
integer compatibility contradiction; the architecture was revised to use an
explicit integer-or-decimal-string schema union and a fresh independent review
completed with PASS and no blocking gaps.

## STEP 3 Approval Record

The final independent Step 3 review passed after the R5 correction. The focused
pre-implementation run recorded all six required repros as red: union-schema
model/import, native-integer conversion, published fixture mapping, valid
dual-form MCP dispatch, and fail-closed non-integral dispatch protection. The
working tree contains only PYPOST-1038 test artifacts and task documentation;
no production implementation was present. The autonomous `sprint-runner`
authorization permits proceeding to Step 4.

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_mcp_tool_contract.py`, `tests/test_collection_import.py`,
    `tests/test_template_service.py`, `tests/test_example_fixtures.py`, and
    `tests/test_mcp_server_integration.py` — six independently verified red
    reproductions (R1–R5, with R1 split into model and import coverage).
- [x] **STEP 4: Development**
  - [x] Added the explicit `integer_or_string` MCP parameter schema, native-integer
    `to_int` support, the six Jira path mappings, and end-to-end regression coverage.
- [x] **STEP 5: Code Cleanup**
  - [x] Completed static checks, targeted tests, JSON/syntax validation, cleanup report,
    and a corrected independent review.
- [x] **STEP 6: Observability**
  - [x] Existing bounded template and HTTP telemetry covers accepted native
    integers and fail-closed invalid identifiers; no new metric or log field is
    warranted. Independent review passed.
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**
  - [x] Documented the narrow `integer_or_string` contract, true-int and
    decimal-string `to_int` support, all six Jira mappings, and isolated
    fixture/MCP-loopback validation for developers and importers.

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1038/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1038/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1038/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1038/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1038/60-tech-debt.md`

### STEP 8: Dev Docs

- `ai-tasks/PYPOST-1038/70-dev-docs.md`
- `doc/dev/README.md`
- `doc/dev/template_expression_functions.md`
- `doc/dev/mcp_integration.md`
- `doc/dev/jira_mcp_project_default.md`
- `doc/dev/testing.md`
- `examples/README.md`
