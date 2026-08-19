# Roadmap: PYPOST-1088

## Task Metadata

- **Implementation language**: Python
- **Branch name**: *[recorded by the commit procedure — reference only, do not switch]*

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1088/10-requirements.md`
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1088/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_mcp_server_manager.py::test_format_mcp_bind_error_addr_in_use` and `tests/test_metrics_server_startup.py::TestFormatBindError::test_metrics_addr_in_use_message` (hardcoded macOS errno 48 vs Linux POSIX errno 98)
  - [x] `tests/test_encryption_migration.py` and `tests/test_encryption_migrate_cli.py` (`MtimeFileCache` stale cache race during rapid rotation and sub-millisecond `st_mtime` equality)
- [x] **STEP 4: Development**
  - [x] Iteration 1: Fix errno.EADDRINUSE portability in server bind error tests (`tests/test_mcp_server_manager.py`, `tests/test_metrics_server_startup.py`)
  - [x] Iteration 2: Add `MtimeFileCache.clear()`, expose `clear_registry_cache()` and `clear_spec_cache()`, and add autouse cache-reset test fixture in `tests/conftest.py`
  - [x] Iteration 3: Invalidate registry cache on test key rotation and backdate mtime via `os.utime` for plaintext re-encryption test (`tests/test_encryption_migration.py`, `tests/test_encryption_migrate_cli.py`, `tests/test_key_sources_chain_coverage.py`)
- [x] **STEP 5: Code Cleanup**
  - [x] `ai-tasks/PYPOST-1088/40-code-cleanup.md`
- [x] **STEP 6: Observability**
  - [x] `ai-tasks/PYPOST-1088/50-observability.md`
  - [x] Analyzed: cross-platform `errno.EADDRINUSE` logging (48 macOS / 98 Linux) in `format_bind_error` / `format_mcp_bind_error`
  - [x] Analyzed: `MtimeFileCache.clear()` state transitions observable via DEBUG logs in `env.py` / `secret_store.py`
  - [x] Analyzed: `_reset_key_source_caches` autouse fixture — cache clear traced through pytest fixture lifecycle in CI
  - [x] Analyzed: `os.utime` mtime backdating in `test_encryption_migration.py` — observable via `st_mtime` assertion before/after
- [x] **STEP 7: Technical Debt Analysis**
  - [x] `ai-tasks/PYPOST-1088/60-tech-debt.md`
  - [x] Repro command re-run 8x against the working tree: 4 target node ids passed 8/8; encryption-only pair re-run 5x more in isolation, 42/42 passed each time — root cause (2) flakiness confirmed resolved
  - [x] Baseline `git worktree` cross-check at pre-task commit `3e4cc8b8`: full repro failed on every one of 6 runs (2-5 encryption-test failures each) — confirms the fix, not chance, resolves it
  - [x] NON-BLOCKER — pre-existing flake newly found: `tests/test_mcp_server_manager.py::test_port_busy_emits_start_failed` (unrelated to this task's diff, confirmed pre-existing via baseline worktree; not yet ticketed — see `60-tech-debt.md`)
  - [x] Timeout-marker BLOCKER check: no blocker — all touched/added tests covered by module-level `pytestmark`
- [x] **STEP 8: Dev Docs**
  - [x] `doc/dev/testing.md` — documented the errno portability fix (macOS `48` literal → symbolic `errno.EADDRINUSE`) in the existing PYPOST-716 port-busy test paragraph
  - [x] `doc/dev/environment_encryption_at_rest.md` — new "File-backed registry caching (`MtimeFileCache`)" subsection: `clear()` / `clear_registry_cache()` / `clear_spec_cache()` entry points, the same-tick stale-cache race they fix, the `_reset_key_source_caches` autouse fixture, and the documented (not fixed) `env.py` vs `secret_store.py` loader guard asymmetry (PYPOST-1112 follow-up); added `tests/test_key_sources_chain_coverage.py` to the Tests file list with a note on its new coverage
  - [x] `doc/dev/encryption_key_migration.md` — Tests section cross-reference: why `test_encryption_migration.py` / `test_encryption_migrate_cli.py` call `clear_registry_cache()` after mid-test key rotation
- [ ] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1088/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1088/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1088/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1088/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1088/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- Commit hash and message (Conventional Commits + JIRA ID)
