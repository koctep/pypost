# Roadmap: PYPOST-889

**Programming language:** Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_e2e_double_response_body.py` (exactly-once RESPONSE_PANEL; red via temp discard no-op)
- [x] **STEP 4: Development**
  - [x] Confirmed Step 3 lock green under `make test-agent-e2e` (40 passed)
  - [x] FR1–FR6 already wired (catalog, body id, streaming stub); no product changes
  - [x] FR7 `doc/dev/` discoverability deferred to Step 8
  - [x] FR8 Relates to PYPOST-887 verified on Jira
- [x] **STEP 5: Code Cleanup**
  - [x] `make lint` clean; scoped flake8 on touched tests clean
  - [x] No unused imports/dead code/debug prints in PYPOST-889 files
  - [x] PYPOST-889 tests: 9 passed; `40-code-cleanup.md` written
- [x] **STEP 6: Observability**
  - [x] N/A for production paths (e2e lock + body widget id only)
  - [x] Reuses existing `agent_e2e_http_stub_installed` INFO; no new logs/metrics
  - [x] `50-observability.md` written
- [x] **STEP 7: Review and Technical Debt**
  - [x] `60-tech-debt.md` written; SAFE TO CLOSE
  - [x] TD-1/TD-2 non-blockers (FR5 automation, stub naming); no Jira in this step
  - [x] Shared panel helpers / response ids already tracked (PYPOST-869 / 853)
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/agent_e2e_double_response_body.md` (lock note)
  - [x] Linked from agent_e2e / golden / HTTP / streaming / README
  - [x] FR7 discoverability complete (sprint-task-runner autonomy)

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-889/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-889/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_e2e_double_response_body.py` — agent e2e exactly-once lock
- Harness: `REQUEST_BODY_EDIT` id; `CANNED_DOUBLE_BODY_LOCK_OK` +
  `canned_send_with_one_chunk` in `pypost/fixtures/agent_e2e_http.py`
- FR5 red proven locally by temporarily no-op'ing `_discard_chunk_buffer` in
  `_on_request_finished` (count=2); restored — HEAD run is green

### STEP 4: Development

- No new product code — PYPOST-887 discard already on HEAD; lock stays green
- Verified: `make test-agent-e2e` (40 passed, lock included);
  `tests/test_agent_e2e_http.py` + identity spot-check (8 passed)
- FR7 (`doc/dev/` note + umbrella links) left for Step 8

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-889/40-code-cleanup.md`
- Lint/format clean on PYPOST-889-touched files; no cleanup code edits
- `make check` residual failures are pre-existing (SOLID caps, ai-tasks
  baseline) — not introduced by this task

### STEP 6: Observability

- `ai-tasks/PYPOST-889/50-observability.md`
- N/A — no new production logging/metrics; harness stub INFO reused;
  regression signal is pytest exactly-once assert

### STEP 7: Review

- `ai-tasks/PYPOST-889/60-tech-debt.md`
- Verdict: SAFE TO CLOSE; Phase D tickets TD-1/TD-2 if desired
- FR7 discoverability remains Step 8 (not Debt)

### STEP 8: Dev Docs

- `doc/dev/agent_e2e_double_response_body.md` — lock overview, run, red proof
- Cross-links: `agent_e2e.md`, `agent_golden_e2e.md`, `agent_e2e_http.md`,
  `response-streaming-display.md`, `doc/dev/README.md`
- Catalog row `double_body_lock_ok` + `canned_send_with_one_chunk` in HTTP docs
- FR7 complete under sprint-task-runner autonomy (no separate user gate)

## Suggested branch

`test/PYPOST-889-double-response-body-lock`
