# Roadmap: PYPOST-1436

## Task Metadata

- **Implementation language**: Python

## Step Status

- [x] **STEP 1: Requirements Gathering and Documentation**
  - [x] Create roadmap file and determine implementation language (Python)
  - [x] Gather business and functional requirements without technical implementation details
  - [x] Document non-functional requirements, constraints, entities, and user scenarios in `ai-tasks/PYPOST-1436/10-requirements.md`
  - [x] Acceptance gate review PASS
- [x] **STEP 2: High-Level Architecture Design**
  - [x] Research existing bind error handling and OS port preflight probing
  - [x] Design structured errno and Winsock normalization architecture in `pypost/core/server_bind.py`
  - [x] Design multi-family IPv4/IPv6 preflight probe architecture in `pypost/core/mcp_server_registry.py`
  - [x] Specify automated red repro test plan for Step 3 (`tests/test_server_bind_errno.py`)
  - [x] Document high-level architecture in `ai-tasks/PYPOST-1436/20-architecture.md`
  - [x] Acceptance gate review PASS
- [x] **STEP 3: Failing Repro Test**
  - [x] `tests/test_server_bind_errno.py`
  - [x] Acceptance gate review PASS
- [x] **STEP 4: Development**
  - [x] Implement `BindErrorClassification` enum (`PORT_IN_USE`, `ADDRESS_NOT_AVAILABLE`, `PERMISSION_DENIED`, `UNCLASSIFIED`) and errno frozen sets (`ERRNO_PORT_IN_USE`, `ERRNO_ADDR_NOT_AVAIL`, `ERRNO_PERMISSION_DENIED`) covering POSIX, BSD/macOS, and Windows Winsock WSA error codes in `pypost/core/server_bind.py`
  - [x] Implement robust `extract_errno` extracting numeric error codes from `errno`, `winerror`, and single/nested `args` tuples
  - [x] Implement `classify_bind_error` for deterministic classification without locale-sensitive substring checks
  - [x] Implement `detect_address_family` supporting bracketed/unbracketed IPv6 and IPv4 addresses and hostnames
  - [x] Implement `validate_host_and_port` with multi-family IPv4/IPv6 probe sockets and `SO_REUSEADDR`
  - [x] Refactor `format_bind_error` supporting dual-order argument signatures and classified error messages
  - [x] Update `MCPServerRegistry._validate_os_port` and `_detect_address_family` to delegate to `validate_host_and_port` and `detect_address_family` in `pypost/core/mcp_server_registry.py`
  - [x] Update `_wait_until_port_bindable` in `pypost/core/qt/mcp_server.py` to support multi-family IPv6 sockets
  - [x] Verify repro tests (`tests/test_server_bind_errno.py`) and existing tests (`tests/test_server_bind.py`, `tests/test_mcp_server_registry.py`, `tests/test_mcp_concurrent_teardown.py`) pass green
  - [x] Verify static analysis gates: `make lint`, `make typecheck`, `make verify-ai-tasks`
  - [x] Acceptance gate review PASS
- [x] **STEP 5: Code Cleanup**
  - [x] Run static analysis and linter checks (`make lint`, `make typecheck`)
  - [x] Verify line lengths (<= 100 chars), clean imports, absence of unused code/variables/debug prints in touched files (`server_bind.py`, `mcp_server_registry.py`, `qt/mcp_server.py`, `test_server_bind_errno.py`)
  - [x] Verify explicit timeout markers on tests per `do-testing` (`pytestmark = pytest.mark.timeout(30)`)
  - [x] Run test suite: `make test PYTEST_ARGS="tests/test_server_bind_errno.py tests/test_server_bind.py tests/test_mcp_server_registry.py tests/test_mcp_concurrent_teardown.py"` (4/4 passed)
  - [x] Run `make verify-ai-tasks` (passed)
  - [x] Create `ai-tasks/PYPOST-1436/40-code-cleanup.md`
  - [x] Acceptance gate review PASS
- [x] **STEP 6: Observability**
  - [x] Audit structured event logging and syslog level mapping across `server_bind.py`, `mcp_server_registry.py`, and `qt/mcp_server.py`
  - [x] Implement structured logging for address family detection (DEBUG), preflight socket probing (DEBUG), successful validation (INFO), port contention/permission warnings (WARNING), and unclassified socket errors (ERROR)
  - [x] Add structured warning event logging in `MCPServerRegistry._validate_os_port` (`logger.warning("mcp_server_registry_port_validation_failed", ...)`)
  - [x] Audit exception handling and provenance preservation (`raise ValueError(...) from exc`), verifying numeric errno codes and strerror retention without credential leakage
  - [x] Document metrics applicability and port contention counters (`mcp.registry.bind.port_in_use_total`, `mcp.registry.bind.permission_denied_total`)
  - [x] Add unit test suite `TestObservabilityLogging` in `tests/test_server_bind_errno.py` verifying structured log emission
  - [x] Create `ai-tasks/PYPOST-1436/50-observability.md`
  - [x] Acceptance gate review PASS
- [x] **STEP 7: Technical Debt Analysis**
  - [x] Analyze shortcuts taken (none; structured errno extraction, POSIX/BSD/WSA code sets, IPv6 socket preflight probing, dual-order signature support)
  - [x] Analyze code quality issues (standalone socket transport tests specifically verifying live IPv6 socket server communications across client-server pairs)
  - [x] Analyze missing tests (e.g. end-to-end IPv6 socket transport coverage across `RawTcpWireClient` and standalone MCP servers)
  - [x] Analyze performance concerns (DNS resolution overhead if non-literal hostnames are passed to preflight probe)
  - [x] Document follow-up tasks and draft field specifications linking existing sprint follow-up tickets: [PYPOST-1431](https://pypost.atlassian.net/browse/PYPOST-1431), [PYPOST-1432](https://pypost.atlassian.net/browse/PYPOST-1432)
  - [x] Classify all follow-up items as NON-BLOCKER (zero blockers, all acceptance criteria satisfied, all tests green)
  - [x] Create `ai-tasks/PYPOST-1436/60-tech-debt.md`
  - [x] Acceptance gate review PASS
- [x] **STEP 8: Dev Docs**
  - [x] Document structured errno normalization and OS port preflight error classification in `doc/dev/mcp_server_registry.md`
  - [x] Document `BindErrorClassification`, POSIX/WSA errno mappings, and `extract_errno` multi-source numeric extraction
  - [x] Document multi-family IPv4/IPv6 address family detection (`detect_address_family`) and socket preflight probing (`validate_host_and_port`) with `SO_REUSEADDR`
  - [x] Document elimination of locale-fragile substring matching in `format_bind_error` and dual-argument order compatibility
  - [x] Document test execution commands for `tests/test_server_bind_errno.py`
  - [x] Verify line length (<= 100 characters) and lint with `make lint` and `make verify-ai-tasks`
  - [x] Acceptance gate review PASS
- [x] **COMMIT: Commit Changes**

## Status Legend

- `[ ]` — step not started
- `[/]` — step in progress
- `[x]` — step completed and accepted (acceptance gate passed)

See the `td-roadmap` skill for who writes which mark and when.

## Artifacts

### STEP 1: Requirements

- `ai-tasks/PYPOST-1436/10-requirements.md`

### STEP 2: Architecture

- `ai-tasks/PYPOST-1436/20-architecture.md`

### STEP 3: Failing Repro

- `tests/test_server_bind_errno.py`

### STEP 4: Development

- Source code
- Tests
- Documentation updates

### STEP 5: Code Cleanup

- `ai-tasks/PYPOST-1436/40-code-cleanup.md`

### STEP 6: Observability

- `ai-tasks/PYPOST-1436/50-observability.md`

### STEP 7: Technical Debt

- `ai-tasks/PYPOST-1436/60-tech-debt.md`

### STEP 8: Dev Docs

- `doc/dev/`

### COMMIT

- No artifact recorded here beyond the `[x]` mark above. Branch name and commit hash are reported
  in chat only, never written to this file.
