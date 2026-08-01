# Roadmap: PYPOST-958

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_e2e_http.py::test_mapping_compound_keys_gui_send_scenario_module_exists`
- [x] **STEP 4: Development**
  - [x] Added `tests/test_agent_e2e_http_mapping_compound_keys.py` with
    `test_mapping_compound_keys_same_url_get_post_panel_outcomes`
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

- `ai-tasks/PYPOST-958/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-958/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_e2e_http.py::test_mapping_compound_keys_gui_send_scenario_module_exists`

### STEP 4: Development

- `tests/test_agent_e2e_http_mapping_compound_keys.py`
- `tests/test_agent_e2e_http.py` — inventory gate

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-958/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-958/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-958/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/agent_e2e_http.md`
- `doc/dev/agent_e2e.md`

Suggested branch (reference): `debt/PYPOST-958-compound-key-gui-scenario`
