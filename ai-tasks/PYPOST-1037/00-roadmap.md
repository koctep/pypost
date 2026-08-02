# Roadmap: PYPOST-1037

**Programming language:** Python

## STEP 1 Approval Record

The applicable `sprint-runner` workflow explicitly runs in autonomous mode and
preauthorizes continuing without a separate confirmation between phases. That
explicit preapproval is the approval basis for completing STEP 1.

## STEP 2 Approval Record

The same autonomous `sprint-runner` preapproval authorizes completion after
the required independent architecture review. The final review passed after
the plan added URL, parameter, JSON-body, and malformed-`to_int` fail-closed
red-test coverage.

## STEP 3 Approval Record

The independent Step 3 test review passed. The focused pre-implementation run
records the required red path while preserving the two compatibility controls;
the autonomous `sprint-runner` authorization permits proceeding to Step 4.

## STEP 4 Approval Record

The independent development review passed after confirming that failed direct
`to_int(...)` calls fail closed only during HTTP preparation, while unrelated
invalid expressions (including `foo.to_int(...)`) retain the compatibility
fallback. The review also confirmed compatibility with legacy
`TemplateService` subclasses. The autonomous `sprint-runner` authorization
permits proceeding to Step 5.

## STEP 5 Approval Record

The remediation recheck passed: the focused affected suite reports 117
passing tests, lint and patch-whitespace checks pass, and independent review
confirmed the two previous Step 4 regressions are covered. The autonomous
`sprint-runner` authorization permits proceeding to Step 6.

## STEP 7 Approval Record

The final independent SAFE TO CLOSE review verified corrected failed-token
provenance in both mixed-expression orders across URL, headers, parameters,
and JSON bodies. Invalid `to_int(...)` expressions block dispatch, while a
valid `to_int(...)` combined with an unrelated invalid expression preserves
legacy literal fallback and dispatch. The focused suite passed with 155 tests;
no release-blocking technical debt remains.

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *[Red test path or N/A — no behavioral change]*
- [x] **STEP 4: Development**
  - [x] Added allow-listed `to_int` conversion for ASCII decimal string inputs.
  - [x] Added HTTP-only strict conversion rendering that blocks invalid `to_int` expressions before dispatch.
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Review and Technical Debt**
- [x] **STEP 8: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1037/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1037/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1037/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1037/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-1037/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/template_expression_functions.md` — `to_int` syntax, strict HTTP
  failure boundary, compatibility contract, observability, and test guidance
- `doc/dev/README.md` — discoverable developer-docs index entry
- `ai-tasks/PYPOST-1037/70-dev-docs.md`
