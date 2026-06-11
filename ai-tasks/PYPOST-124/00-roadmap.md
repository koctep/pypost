# Roadmap: PYPOST-124

**Programming language:** Python (PySide6)

**Suggested branch:** `feature/PYPOST-124-json-variable-highlighting`

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `{{...}}` placeholder highlighting to `JsonHighlighter` (darkorange, bold)
  - [x] Reused `TEMPLATE_PLACEHOLDER_PATTERN` from core tokenizer (PYPOST-536)
  - [x] Added unit tests for plain variables and function expressions
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

- `ai-tasks/PYPOST-124/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-124/20-architecture.md`

### STEP 3: Development

- `pypost/ui/widgets/json_highlighter.py`
- `tests/test_json_highlighter.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-124/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-124/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-124/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-124/70-dev-docs.md`
- `doc/dev/json_syntax_highlighting.md`
