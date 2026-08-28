# Roadmap: PYPOST-993

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-993/10-requirements.md`
  - Step 1 acceptance gate passed (review verdict PASS)
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-993/20-architecture.md`
  - Step 2 acceptance gate passed (review verdict PASS)
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_agent_ui_actions_mcp_seed.py`
  - [x] `ai-tasks/PYPOST-993/25-failing-repro.md`
  - Step 3 acceptance gate passed (review verdict PASS)
- [x] **STEP 4: Development**
  - [x] Implemented `pypost/agent/seed_loader.py` supporting single collection JSON/YAML,
    multi-collection lists, environment files, and seed directories
  - [x] Updated `AgentAppSession.__init__` and `start()` in `pypost/agent/lifecycle.py` to
    inject seed files into ephemeral storage before application composition
  - [x] Updated `pypost/agent/ui_actions_mcp.py` with `--seed` / `--seed-file` CLI flags,
    CLI/env resolution, and mutual exclusion enforcement with `--attach`
  - [x] Enhanced `pypost/agent/ui_snapshot.py` to capture top-level item labels for
    unselected item views
  - [x] Added comprehensive unit tests in `tests/test_agent_seed_loader.py` (10 tests)
  - [x] Validated that all 5 repro tests in `tests/test_agent_ui_actions_mcp_seed.py` are GREEN
  - [x] Verified regression safety in `tests/test_agent_ui_actions_mcp.py` and
    `tests/test_ui_snapshot.py`
  - Step 4 acceptance gate passed (review verdict PASS)

- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-993/40-code-cleanup.md`
  - Performed static code analysis and linting (`make lint`)
  - Enforced PEP 8 and line lengths <= 100 characters across all modified files
  - Consolidated imports, expanded docstrings and type annotations
  - Verified explicit pytest timeout markers on all tests per `do-testing`
  - Verified AI task artifacts integrity (`make verify-ai-tasks`)
  - Step 5 acceptance gate passed (review verdict PASS)
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-993/50-observability.md`
  - Added structured logging across `pypost.agent.seed_loader`, `pypost.agent.lifecycle`,
    and `pypost.agent.ui_actions_mcp`
  - Added context fields (`seed_path`, `collection_count`, `request_count`,
    `duration_ms`, `error_type`)
  - Added performance metrics for staging latency (<5ms) and entity counts
  - Added caplog-backed test assertions for INFO and ERROR observability events per `do-testing`
  - Step 6 acceptance gate passed (review verdict PASS)
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-993/60-tech-debt.md`
  - Evaluated shortcuts taken (pre-compose staging into target data_dir vs. runtime IPC;
    permissive schema validation; directory environment format constraints)
  - Evaluated code quality issues (module-level functions vs. class encapsulation,
    import logic deduplication, private StorageManager method access,
    parser return typing)
  - Verified test suite for missing tests and confirmed explicit 60s timeout markers
    on all tests per `do-testing` (no blockers)
  - Analyzed performance considerations (<5ms staging overhead, zero runtime latency impact)
  - Documented proposed technical debt follow-up tickets
  - Step 7 acceptance gate passed (review verdict PASS)
- [x] **STEP 8: Dev Docs**
  - Created `doc/dev/agent_seed_injection.md` covering architecture,
    pre-compose staging, supported formats, CLI flags, env var precedence,
    attach mutual exclusion, programmatic `AgentAppSession(seed_path=...)`
    usage, observability, and troubleshooting
  - Updated `doc/dev/agent_ui_actions_mcp.md` with `--seed` / `--seed-file`,
    `PYPOST_AGENT_SEED_PATH`, spawn vs attach mutual exclusion, and test
    invocations
  - Updated `doc/dev/agent_lifecycle.md` with `seed_path` in
    `AgentAppSession`, code example, configuration, and observability
  - Updated `doc/dev/README.md` and `doc/dev/gui_testing.md` with cross-references
  - Step 8 acceptance gate passed (review verdict PASS)
- [x] **COMMIT: Commit Changes**
  - Staged and committed task artifacts and code changes

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-993/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-993/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_agent_ui_actions_mcp_seed.py`
- `ai-tasks/PYPOST-993/25-failing-repro.md`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-993/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-993/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-993/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/agent_seed_injection.md`
- `doc/dev/agent_ui_actions_mcp.md`
- `doc/dev/agent_lifecycle.md`
- `doc/dev/gui_testing.md`
- `doc/dev/README.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
