# Roadmap: PYPOST-1046

## Task Metadata

- **Implementation language**: Python
- **Branch name**: `feature/PYPOST-1046-headless-daemon-mode`


## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Recorded the daemon-mode business goal, user stories, scope, and constraints
  - [x] Defined configuration precedence and invalid-directory behavior as testable outcomes
  - [x] Captured current GUI launch, storage defaults, and multi-server context
  - [x] Added `ai-tasks/PYPOST-1046/10-requirements.md`
  - [x] Passed Markdown, line-length, whitespace, and diff integrity checks
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Researched existing GUI, agent, storage, MCP, metrics, CLI, and packaging behavior
  - [x] Verified CLI, environment, packaging, signal, path, and Qt Core assumptions in official docs
  - [x] Designed separate pure configuration and Qt Core daemon lifecycle boundaries
  - [x] Defined precedence, validation, strict loading, readiness, failure, and shutdown contracts
  - [x] Specified hermetic Step 3 red repro and proportional Step 4 regression coverage
  - [x] Added `ai-tasks/PYPOST-1046/20-architecture.md`
  - [x] Passed Markdown, link, line-length, whitespace, and diff integrity checks
- [x] **STEP 3: Failing Repro Test**
  - [x] Added `tests/test_daemon_config.py`
  - [x] Added red node
    `test_resolve_daemon_paths_applies_precedence_independently`
  - [x] Declared the module-level `pytest.mark.timeout(30)` timeout
  - [x] Confirmed the node fails because `pypost.core.daemon_config` is not implemented
  - [x] Independent review confirmed the intended missing-module failure
- [x] **STEP 4: Development**
  - [x] Implemented pure independent daemon path precedence and made the reviewed repro green
  - [x] Added safe directory validation, default initialization, and resolver matrix coverage
  - [x] Added backward-compatible independent storage directory injection without explicit writes
  - [x] Added strict immutable required-record snapshots and safe missing/invalid data errors
  - [x] Added strict settings loading with sanitized typed failures and preserved GUI fallback
  - [x] Added metrics listener readiness and unexpected-exit lifecycle signals
  - [x] Added Qt Core daemon composition, strict preflight, readiness, and idempotent shutdown
  - [x] Added daemon CLI, environment integration, console entry point, and Makefile launch target
  - [x] Removed upstream URL values from proxy lifecycle logs
  - [x] Split daemon storage and metrics lifecycle helpers to preserve SOLID module caps
  - [x] Updated isolated packaging smoke policy for the new console entry module
  - [x] Passed 82 focused daemon, storage, metrics, packaging, and compatibility checks
  - [x] Baseline-classified three unrelated repository guard failures at commit `082ff6aa`
  - [x] Fix iteration 1: preserved required collection IDs for malformed legacy filenames and
    translated malformed environment-variable container failures into correlated daemon errors
  - [x] Fix iteration 2: emitted one sanitized data diagnostic per affected server and redacted
    proxy URLs from timeout and connection-error logs
  - [x] Fix iteration 3: isolated metrics lifecycle state by start generation, suppressed stale
    worker callbacks/finalization, and moved bounded thread joins outside the lifecycle lock
  - [x] Fix iteration 4: completed explicit-timeout path, strict-storage, runtime-failure, CLI
    shutdown, lifecycle-generation, and proxy-privacy regressions
  - [x] Fix iteration 5: removed raw proxy failure details from logs/activity, added count-only
    skipped-record diagnostics, serialized lifecycle callbacks against stop/restart, isolated
- [x] **STEP 5: Code Cleanup**
  - [x] Fixed flake8 formatting and whitespace issues across modified modules and tests
  - [x] Verified line length <= 100 characters and zero unused imports / dead code
  - [x] Verified explicit timeout markers across all test files
  - [x] Passed static analysis, type checking, and focused test suite
  - [x] Added `ai-tasks/PYPOST-1046/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] Documented structured logging across daemon CLI, runtime, strict storage, and MCP proxy
  - [x] Documented privacy and secret masking (header sanitization, raw URL omission)
  - [x] Documented Prometheus metrics, MCP resource metrics, and health indicators
  - [x] Added `ai-tasks/PYPOST-1046/50-observability.md`
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Evaluated shortcuts taken (sys.exit wrapper, signal heartbeat, startup timeout default)
  - [x] Evaluated code quality issues (StorageManager single root, dynamic import, model copies)
  - [x] Evaluated missing tests and verified 100% per-test explicit timeout marker compliance
  - [x] Evaluated startup directory globbing and idle timer wakeup performance concerns
  - [x] Cataloged pre-existing baseline test failures as non-blockers with repro and Jira keys
  - [x] Defined planned follow-up improvements (CLI flags, zero-wake notifier, storage refactor)
  - [x] Added `ai-tasks/PYPOST-1046/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Documented headless daemon architecture, CLI entry point, and execution model
  - [x] Documented pure path configuration, precedence matrix, and strict validation
  - [x] Documented strict immutable storage snapshots and privacy-preserving error diagnostics
  - [x] Documented runtime coordination, metrics server, MCP proxy integration, and signal shutdown
  - [x] Documented troubleshooting, port conflict handling, and startup timeouts
  - [x] Added `doc/dev/daemon.md` and updated `doc/dev/README.md` and `doc/dev/architecture.md`
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1046/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1046/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_daemon_config.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1046/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1046/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1046/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/daemon.md`
- `doc/dev/README.md`
- `doc/dev/architecture.md`

### COMMIT

- Commit: `43b7f346` — `feat(daemon): PYPOST-1046 support headless daemon mode`
