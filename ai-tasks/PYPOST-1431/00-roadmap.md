# Roadmap: PYPOST-1431

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] `ai-tasks/PYPOST-1431/10-requirements.md`
  - [x] Acceptance gate review PASS
- [x] **STEP 2: High-Level Architecture Design**
  - [x] `ai-tasks/PYPOST-1431/20-architecture.md`
  - [x] Acceptance gate review PASS
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_mcp_standalone_wire_ipv6.py`
  - [x] Acceptance gate review PASS
- [x] **STEP 4: Development**
  - [x] Implement IPv6 support in `tests/helpers/raw_tcp_client.py` and `tests/helpers/port_allocation.py`
  - [x] Verify Step 3 repro tests pass over IPv6 loopback (`tests/test_mcp_standalone_wire_ipv6.py`)
  - [x] Verify wire IPC and fuzzing regression suites pass (`tests/test_mcp_standalone_wire_ipc_repro.py`, `tests/test_mcp_wire_fuzzing_negative.py`, `tests/test_raw_tcp_client_helper.py`)
  - [x] Validate quality gates (`make lint`, `make typecheck`, `make verify-ai-tasks`)
  - [x] Acceptance gate review PASS
- [x] **STEP 5: Code Cleanup**
  - [x] Static analysis, linting, and typing checks (`make lint`, `make typecheck`)
  - [x] Formatting, line length verification (<= 100 chars), clean imports, and unused code check
  - [x] Test timeout marker verification per `do-testing`
  - [x] Test suite execution (`make test`)
  - [x] Create `ai-tasks/PYPOST-1431/40-code-cleanup.md`
  - [x] Acceptance gate review PASS
- [x] **STEP 6: Observability**
  - [x] Logging audit: verify structured event logging on socket connection, address family detection, socket errors, and disconnects
  - [x] Syslog severity level mapping: DEBUG (address family resolution, raw frame transfer), INFO (successful connections), WARNING (transient socket errors), ERROR (fatal connection rejections)
  - [x] Diagnostics and security audit: verify bracketed vs unbracketed address formatting preserves diagnostic context with zero token/secret leakage
  - [x] Metrics applicability analysis: document transport connection metrics by address family (`mcp.client.raw_tcp.connect_total{family="ipv6"}`)
  - [x] Create `ai-tasks/PYPOST-1431/50-observability.md`
  - [x] Acceptance gate review PASS
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze shortcuts taken: none (structured address family detection, clean bracket stripping, RFC 3986 Host formatting, IPv6 SO_REUSEADDR port allocation, environment capability gating)
  - [x] Analyze code quality issues: none (strict linting, typing, line length limits, timeout markers per `do-testing`)
  - [x] Identify missing test coverage: dual-stack simultaneous IPv4 and IPv6 client connection concurrency against a multi-homed server listener (NON-BLOCKER)
  - [x] Identify performance concerns: memory allocation and buffer copy overhead during socket buffer accumulation in RawTcpWireClient (NON-BLOCKER)
  - [x] Document follow-up tasks: link [PYPOST-1432](https://pypost.atlassian.net/browse/PYPOST-1432) (Zero-Copy Memory Optimization for RawTcpWireClient) as NON-BLOCKER
  - [x] Create `ai-tasks/PYPOST-1431/60-tech-debt.md`
  - [x] Acceptance gate review PASS
- [x] **STEP 8: Dev Docs**
  - [x] Document IPv6 socket transport coverage under PYPOST-1431 in `doc/dev/mcp_standalone_wire_ipc_stress.md`
  - [x] Document `RawTcpWireClient` address family detection, clean host stripping, and bracketed Host header formatting
  - [x] Document IPv6 port allocation in `tests/helpers/port_allocation.py` (`_can_bind` with `AF_INET6` and `SO_REUSEADDR`)
  - [x] Document environment capability checking with `is_ipv6_loopback_supported()`
  - [x] Document test execution commands for `tests/test_mcp_standalone_wire_ipv6.py`
  - [x] Verify line length and quality gates (`make lint`, `make verify-ai-tasks`)
  - [x] Acceptance gate review PASS
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1431/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1431/20-architecture.md`

### STEP 3: Failing Repro

- Automated red test(s) under `tests/` (or N/A note in roadmap)

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1431/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1431/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1431/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/mcp_standalone_wire_ipc_stress.md`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
