# Roadmap: PYPOST-1288

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
- [x] **STEP 2: High-Level Architecture Design**
  - [/] `ai-tasks/PYPOST-1288/20-architecture.md` drafted for independent review; includes
    transport acceptance, shared frame signal, outbound metrics wiring, and Step 3 red-test plan.
- [x] **STEP 3: Failing Repro Test**
  - [/] `tests/test_websocket_outbound_metrics_repro.py` covers accepted text and binary
    payload counts, blocked sends, and rejected text and binary handoffs. Targeted `make test`
    result: 3 intended failures (missing outbound metrics; rejected handoffs still emit
    `frame_sent`) and 1 passing blocked-send case. Pending independent review.
- [x] **STEP 4: Development**
  - [x] Made transport sends report complete handoff, gated `frame_sent` on acceptance,
    recorded outbound message and byte counters in the presenter, and updated transport fakes.
  - [x] Added Qt adapter contract cases for full, partial, empty, and disconnected handoffs.
  - [x] Targeted `make test` passed the outbound metrics repro and adapter cases; `make check`
    passed lint and all affected WebSocket test files. Full suite remained red on unrelated
    failures: expression validation and PYPOST-1077 inventory reproduce at base commit
    `aa7f33e07af4`; stream export passed on isolated rerun, while Makefile smoke tests timed
    out during virtual environment setup. Triage details were handed to the runner.
- [x] **STEP 5: Code Cleanup**
  - [/] `ai-tasks/PYPOST-1288/40-code-cleanup.md` records a clean formatting review,
    passing targeted `make check`, and passing `make typecheck` baseline. `make analyze`
    has no target in this repository. Pending independent review.
- [x] **STEP 6: Observability**
  - [/] `ai-tasks/PYPOST-1288/50-observability.md` records payload-free accepted and rejected
    handoff logs and the existing outbound counters. Affected `make check` passed lint, four
    WebSocket test files, and artifact verification. Pending independent review.
- [x] **STEP 7: Technical Debt Analysis**
  - [/] `ai-tasks/PYPOST-1288/60-tech-debt.md` records no new blockers, one optional
    loopback-metrics coverage follow-up, and the four pre-existing full-suite failure groups
    with their existing Jira links. Pending independent review.
- [x] **STEP 8: Dev Docs**
  - [/] Updated `doc/prometheus_monitoring.md` with the outbound counter contract and
    `doc/dev/websocket_session_engine.md` with the transport, signal, metric, and diagnostic
    details. `make lint` and `make verify-ai-tasks` passed. Pending independent review.
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1288/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1288/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1288/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1288/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1288/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
