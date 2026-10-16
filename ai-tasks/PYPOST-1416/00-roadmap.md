# Roadmap: PYPOST-1416

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Create roadmap file and determine implementation language
  - [x] Gather business and functional requirements without technical implementation details
  - [x] Document non-functional requirements, constraints, entities, and user scenarios
  - [x] Acceptance gate review passed
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Research MCP standalone server transports, wire framing, and stdio subprocess IPC
  - [x] Design live wire socket and stdio IPC stress test harness architecture
  - [x] Define Step 3 failing repro test strategy
  - [x] Create `ai-tasks/PYPOST-1416/20-architecture.md`
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_mcp_standalone_wire_ipc_repro.py` (live wire IPC and stdio transport stress suite)
    - [x] Implement `RawTcpWireClient` and assert TCP packet fragmentation over Streamable HTTP (`/mcp`)
    - [x] Assert 100-request pipelined burst stress over raw TCP wire
    - [x] Implement non-blocking `stdout`/`stderr` concurrent drainers for 50-request stdio bursts with large payloads (>64KB)
    - [x] Assert rapid teardown under active wire load and immediate socket re-binding without `EADDRINUSE`
    - [x] Quality gates verified: `make lint`, `make typecheck`, `make verify-ai-tasks`
- [x] **STEP 4: Development**
  - [x] Iteration 1: Live wire stress harness verification and standalone MCP server transport validation
    - Verified `tests/test_mcp_standalone_wire_ipc_repro.py` comprehensively exercises raw TCP wire socket communication (packet fragmentation down to 1-byte chunks, pipelined burst of 100 requests over keep-alive connection, non-blocking stdio drainers for 50 requests with >64KB payloads, rapid shutdown under load and immediate port re-binding).
    - Verified standalone MCP server implementation (`MCPServerManager` and `MCPServerImpl`) robustly handles raw wire-level socket communication and stdio subprocess IPC without transport-level stalls or socket descriptor leaks.
    - Verified all Step 3 repro tests pass GREEN: `make test PYTEST_ARGS='tests/test_mcp_standalone_wire_ipc_repro.py'` (4/4 tests passed in 3.22s).
    - Verified related standalone execution tests pass GREEN: `make test PYTEST_ARGS='tests/test_mcp_standalone_execution_repro.py'`.
    - Verified broader MCP test suite passes cleanly: `make test PYTEST_ARGS='tests/test_mcp*.py'` (46 passed, 1 skipped).
    - Quality gates verified: `make lint`, `make typecheck`, `make verify-ai-tasks`.
- [x] **STEP 5: Code Cleanup**
- [x] **STEP 6: Observability**
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze shortcuts, code quality issues, missing tests, and performance concerns
  - [x] Document technical debt in `ai-tasks/PYPOST-1416/60-tech-debt.md`
- [x] **STEP 8: Dev Docs**
  - [x] Update `doc/dev/mcp_server_registry.md` to cover live wire IPC and stdio transport stress testing architecture
  - [x] Document raw TCP loopback testing against Streamable HTTP (`/mcp`) and SSE (`/sse`)
  - [x] Document packet fragmentation resilience (1-byte and multi-byte chunks, chunked HTTP/SSE reassembly)
  - [x] Document pipelined burst throughput (100 requests over single keep-alive TCP connection)
  - [x] Document OS pipe stdio IPC with non-blocking drainers avoiding >64KB buffer deadlocks and clean stdin EOF exit
  - [x] Document socket lifecycle teardown and rapid port re-binding without `EADDRINUSE` under active load
  - [x] Document test execution guide for `tests/test_mcp_standalone_wire_ipc_repro.py`
  - [x] Create `ai-tasks/PYPOST-1416/70-dev-docs.md` summary artifact
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1416/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1416/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1416/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1416/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1416/60-tech-debt.md`

### STEP 8: Dev Docs

- `ai-tasks/PYPOST-1416/70-dev-docs.md`
- `doc/dev/mcp_server_registry.md`
- `doc/dev/mcp_standalone_wire_ipc_stress.md`
- `doc/dev/mcp.md`
- `doc/dev/README.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
