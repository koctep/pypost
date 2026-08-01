# Roadmap: PYPOST-948

**Programming language:** Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] *Convention lock: `tests/test_agent_e2e_response_panel.py` — `test_send_modules_use_identity_scoped_text_wait_settle` — sibling Send modules must use `wait_for_text` on `RESPONSE_STATUS` / `RESPONSE_BODY`, not `wait_for_snapshot(_response_ready)`*
- [x] **STEP 4: Development**
  - [x] Added `tests/helpers/agent_e2e_send_settle.py` (`wait_response_after_send`, `json_response_body_display`)
  - [x] Migrated double-body, presentation-matrix, http_env Send settle to identity text waits
  - [x] Migrated optional seed POST Send response settle; tree-open stays snapshot-based
  - [x] Extended convention test to accept shared helper; convention + agent e2e green
- [x] **STEP 5: Code Cleanup**
  - [x] `make lint` + flake8 on scoped test paths clean
  - [x] `40-code-cleanup.md` recorded
- [x] **STEP 6: Observability**
  - [x] Test-only migration — no new production logs; `50-observability.md`
- [x] **STEP 7: Review and Technical Debt**
  - [x] `60-tech-debt.md` with PYPOST-949/950 follow-ups; SAFE TO CLOSE
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/agent_e2e_send_settle.md` + sibling doc touch-ups
  - [x] `70-dev-docs.md` recorded

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-948/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-948/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-948/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-948/50-observability.md`

### STEP 7: Review

- `ai-tasks/PYPOST-948/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

## Parent / source

- [PYPOST-920](https://pypost.atlassian.net/browse/PYPOST-920) — optional response
  status/body widget ids (golden migrated; siblings deferred)
- TD-1 in `ai-tasks/PYPOST-920/60-tech-debt.md`

## Suggested branch

`test/PYPOST-948-sibling-e2e-text-wait-settle`
