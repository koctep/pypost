# Roadmap: PYPOST-450

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added first slice: allow-listed `urlencode` in template rendering with tests.
  - [x] Extended allow-list with `md5` and `base64`; added focused tests,
    including mixed function-placeholder usage.
  - [x] Enforced strict function-placeholder validation and added negative tests for
    malformed, nested, multi-arg, and unknown function variants.
  - [x] Added typed function-expression validation outcomes and tests for
    error-code mapping with backward-compatible rendering fallback.
  - [x] Added hover parity slice by resolving function expressions
    via runtime-compatible path and covering line/body hover contexts in tests.
  - [x] Closed table-cell hover parity for params/headers by resolving
    expressions in table widgets and adding focused tooltip tests.
- [x] **STEP 4: Code Cleanup**
  - [x] Simplified function-expression validation and hover resolution/mouse-move paths
    via helper extraction while keeping behavior unchanged.
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

## Implementation Context

- Programming language: `Python`

### STEP 1: Requirements

- `ai-tasks/PYPOST-450/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-450/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-450/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-450/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-450/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/`

## Branch Recommendation

- `feature/PYPOST-450-template-function-expressions`
