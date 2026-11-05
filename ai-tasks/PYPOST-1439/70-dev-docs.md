# PYPOST-1439: Developer Documentation

## Overview

Documented process vs thread MCP execution mode (`mcp_execution_mode`), supervisor / worker /
IPC contracts, DEBUG env gates, and STOP→SIGTERM→SIGKILL escalation delivered in Phase 2.

## Documentation Artifacts

### Created

| File | Description |
| --- | --- |
| `doc/dev/mcp_process_isolation.md` | Process vs thread mode, architecture, configuration, IPC contracts, stop escalation, DEBUG/`TEST_ECHO` gates, troubleshooting, tests |
| `ai-tasks/PYPOST-1439/70-dev-docs.md` | Task-local summary of Step 8 |

### Updated

| File | Description |
| --- | --- |
| `doc/dev/mcp_process_supervisor_evaluation.md` | Phase 2 marked implemented (PYPOST-1439) with pointers to isolation doc and tests |
| `doc/dev/mcp_concurrent_multiserver.md` | Cross-link item 8 + Related Documentation entry for process mode |
| `doc/dev/README.md` | TOC entries under MCP and Testing |

## Key Topics Documented

1. **`mcp_execution_mode`**: `thread` (default) vs `process`; registry construction-time selection.
2. **Supervisor / worker / IPC**: `McpProcessSupervisor`, `mcp_worker_process`, versioned messages.
3. **Env gates**: `PYPOST_MCP_ALLOW_DEBUG_IPC`, `PYPOST_MCP_TEST_ECHO_VARS`.
4. **Stop escalation**: IPC STOP → SIGTERM → SIGKILL within ~2.0s.
