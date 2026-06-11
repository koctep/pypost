# Roadmap: PYPOST-158

**Language:** Python

**Suggested branch:** `test/PYPOST-158-legacy-sse-close-and-405`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] SSE close regression test with mocked transport (no live stream hang)
  - [x] Expanded 405 guards for wrong methods on `/` and `/messages`
  - [x] Mounted `/sse` method guard tests
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-158/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-158/20-architecture.md`

### STEP 3: Development

- `tests/test_mcp_legacy_sse.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-158/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-158/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-158/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/testing.md`
- `ai-tasks/PYPOST-158/70-dev-docs.md`
