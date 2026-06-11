# Roadmap: PYPOST-515

**Programming language:** Python (PySide6 UI, PyYAML)

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Development**
  - [x] Added `convert_json_object_to_yaml` in `yaml_json_converter`
  - [x] Extended `CodeEditor.insertFromMimeData` for JSON→YAML when YAML + yaml_as_json
  - [x] Wired `RequestWidget` to sync `yaml_as_json` and body format to `CodeEditor`
  - [x] Added unit tests for converter and paste behavior
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

- `ai-tasks/PYPOST-515/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-515/20-architecture.md`

### STEP 3: Development

- Source code
- Tests
- Documentation updates

### STEP 4: Code Cleanup

- `ai-tasks/PYPOST-515/40-code-cleanup.md`

### STEP 5: Observability

- `ai-tasks/PYPOST-515/50-observability.md`

### STEP 6: Review

- `ai-tasks/PYPOST-515/60-tech-debt.md`

### STEP 7: Dev Docs

- `doc/dev/yaml_as_json.md`

## Suggested branch name

`feature/PYPOST-515-json-paste-to-yaml`
