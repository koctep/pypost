# Roadmap: PYPOST-395

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `DARK_JSON_SYNTAX_COLORS` and `resolve_json_syntax_colors()` in theme module
  - [x] Added `JsonHighlighter.set_colors()` for runtime palette rebinding
  - [x] Wired `TabsPresenter.apply_settings` to refresh highlighter colors
  - [x] Extended `tests/test_json_highlighter.py` for dark palette and `set_colors`
- [x] **STEP 4: Code Cleanup**
- [x] **STEP 5: Observability**
- [x] **STEP 6: Review and Technical Debt**
- [x] **STEP 7: Dev Docs**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Programming language

**Python** — PySide6, dataclasses, pytest + unittest.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-395/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-395/20-architecture.md`

### STEP 3: Development

- `pypost/ui/theme/json_syntax_theme.py`
- `pypost/ui/widgets/json_highlighter.py`
- `pypost/ui/presenters/tabs_presenter.py`
- `tests/test_json_highlighter.py`

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-395/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-395/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-395/60-tech-debt.md`

### STEP 7: Dev Docs

- `ai-tasks/PYPOST-395/70-dev-docs.md`
- `doc/dev/json_syntax_highlighting.md`
