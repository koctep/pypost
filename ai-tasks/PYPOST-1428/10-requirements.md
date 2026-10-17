# PYPOST-1428: Extract RawTcpWireClient to Shared Test Helper

## Goals

In Model Context Protocol (MCP) server development, comprehensive testing requires exercising real operating system network sockets (TCP loopback) to validate physical transport mechanics such as packet fragmentation, burst pipelining, chunked transfer encoding, and Server-Sent Events (SSE) message parsing.

During the implementation of live wire IPC stress testing in [PYPOST-1416](file:///home/src/ai-tasks/PYPOST-1416/10-requirements.md), low-level socket driving and response parsing capabilities were developed locally inside a single monolithic test file (`tests/test_mcp_standalone_wire_ipc_repro.py`). While this satisfied the immediate testing requirements for standalone MCP servers, it introduced significant technical debt:
1. **Lack of Reusability**: Upcoming MCP transport test suites (such as MCP proxy wire stress tests, protocol compliance suites, and negative wire fuzzing tests) require identical low-level socket manipulation and wire framing capabilities. Leaving these utilities private to a single test file prevents reuse across the testing ecosystem.
2. **Duplication Risk and Cross-Test Coupling**: Without a canonical shared helper, developers creating future MCP tests would be forced to duplicate low-level networking logic or create cross-imports between test modules—a practice that violates test isolation and leads to fragile test suites.
3. **High Maintenance Overhead**: Transport framing bug fixes, performance optimizations (such as buffer memory optimizations), or protocol extensions would need to be replicated across multiple test locations rather than maintained in a single, well-tested shared utility.

The business goal of this task is to reduce technical debt by extracting the raw TCP wire client and response parsing utilities from `tests/test_mcp_standalone_wire_ipc_repro.py` into a standardized, reusable test helper module in `tests/helpers/raw_tcp_client.py`. This ensures high modularity, eliminates code duplication, promotes clean test architecture, and accelerates the development of upcoming MCP transport test suites.

## Programming Language

- **Implementation language**: Python

## User Stories

- As an **MCP Test Automation Engineer**, I want a centralized, reusable raw TCP wire client in `tests/helpers/` so that I can construct wire-level stress, fragmentation, and pipelining tests across multiple MCP test suites without duplicating low-level socket and framing logic.
- As an **MCP Feature Developer**, I want to import a standardized wire client and response parser into new transport test suites so that I can quickly verify protocol behaviors over real loopback sockets with minimal boilerplate.
- As a **Core Maintainer**, I want transport test harness utilities decoupled from individual test suites so that test files remain focused on scenario assertions, while shared wire mechanics can be maintained, optimized, and extended in one place.
- As a **CI / Quality Engineer**, I want the extraction to cause zero behavioral regressions in existing test suites and maintain full compatibility with repository quality gates (`make check`, `make lint`, `make typecheck`).

## Definition of Done

This task is considered complete when:
1. Reusable wire client and protocol parsing capabilities are extracted from `tests/test_mcp_standalone_wire_ipc_repro.py` and established as a dedicated shared test helper module in `tests/helpers/raw_tcp_client.py`.
2. The existing test suite `tests/test_mcp_standalone_wire_ipc_repro.py` is updated to consume the shared helper without any behavioral regression or loss of test coverage.
3. The shared helper module is properly exposed in the test helpers namespace (`tests/helpers/`) with comprehensive type annotations and docstrings.
4. All existing tests in `tests/test_mcp_standalone_wire_ipc_repro.py` and related MCP test suites pass cleanly.
5. All repository quality gates (`make check`, `make lint`, `make typecheck`, `make verify-ai-tasks`) pass with zero errors.

## Task Description

### Problem Statement

During PYPOST-1416, a raw TCP client and JSON-RPC response parser were implemented directly within `tests/test_mcp_standalone_wire_ipc_repro.py` to facilitate packet fragmentation, burst pipelining, and HTTP/SSE stream decoding. This inline definition created a monolithic test file (>680 lines) combining scenario assertions with low-level networking primitives.

Upcoming roadmap items—including MCP proxy wire stress tests (PYPOST-1417) and malformed protocol fuzzing (PYPOST-1430)—require the same wire injection and response parsing capabilities. Leaving these components trapped inside an individual test module prevents modular reuse and invites technical debt through code duplication.

### Scope

- **Extracting Shared Test Helper**:
  - Move the raw TCP client and protocol response parsing logic from `tests/test_mcp_standalone_wire_ipc_repro.py` into a new dedicated module `tests/helpers/raw_tcp_client.py`.
  - Expose the helper appropriately for clean importing across test suites.
- **Refactoring Existing Test Suite**:
  - Update `tests/test_mcp_standalone_wire_ipc_repro.py` to import and utilize the shared helper.
  - Verify that all existing wire stress tests continue to run and pass without behavioral alterations.
- **Type Safety and Documentation**:
  - Ensure complete type hints for static analysis compliance (`mypy`).
  - Document the helper module with clear docstrings explaining its role in wire transport testing.

### Out of Scope

- Implementing new networking features such as IPv6 support or TLS termination (tracked separately in PYPOST-1431 and future tickets).
- Modifying production runtime application code in `pypost/` (this task is strictly focused on test infrastructure and test debt reduction).
- Rewriting or altering existing test assertions or scenario logic in `tests/test_mcp_standalone_wire_ipc_repro.py`.
- Creating new stress test suites for other components (those belong to their respective feature tickets, e.g., PYPOST-1417).

### Functional Requirements

- **FR1 (Reusable Raw TCP Client Helper)**: Provide a shared client utility capable of connecting to loopback TCP sockets, supporting context management (`with` statements), constructing HTTP/1.1 formatted requests with custom headers, transmitting full and fragmented byte sequences, and reading framed HTTP/1.1 responses (including chunked transfer encoding and fixed content lengths).
- **FR2 (Protocol Response Parsing Helper)**: Provide a shared utility to parse structured JSON-RPC messages from raw response byte streams, supporting both standard JSON application payloads and Server-Sent Events (SSE `data:` streams).
- **FR3 (Modular Test Helper Integration)**: Enable any test suite across the repository to import the wire client and response parser from `tests/helpers/` without relying on cross-test module imports.
- **FR4 (Zero Behavioral Regression)**: Ensure that existing standalone MCP server wire stress tests in `tests/test_mcp_standalone_wire_ipc_repro.py` continue to execute identically and validate all wire stress contracts (fragmentation, pipelining, rapid re-binding).

### Non-Functional Requirements

- **NFR1 (Zero Test Flakiness)**: The refactored helper must maintain deterministic execution, preserving existing timeout contracts and socket handling to prevent intermittent failures in CI pipelines.
- **NFR2 (Static Analysis and Quality Compliance)**: The new helper module must fully adhere to PEP 8 standards, pass static analysis (`flake8`), pass type checks (`mypy`), and meet repository AI task verification checks (`make verify-ai-tasks`).
- **NFR3 (Maintainability and Readability)**: The extracted helper must provide descriptive docstrings and clear method contracts, reducing cognitive load for developers writing wire-level tests.

### Main Business Entities

| Business Entity | Description | Attributes (Business Perspective) |
| --- | --- | --- |
| **Shared Wire Test Helper** | A centralized test utility module providing low-level network transport testing capabilities across test suites. | Module path (`tests/helpers/raw_tcp_client.py`), exported symbols, documentation. |
| **Wire Protocol Client** | A test client instance facilitating physical socket communication with servers under test. | Target host, target port, connection timeout, active socket state, session identifier. |
| **Wire Response Parser** | A helper function decoding serialized wire response streams into structured messages. | Input byte payload, format compatibility (application/json, text/event-stream), parsed message output. |
| **Consumer Test Suite** | Any test suite requiring real TCP wire socket interaction to validate server behavior. | Test file path, scenario definitions, test execution results. |

### User Scenarios

#### Scenario 1: Existing Test Suite Consuming Shared Helper
During automated CI execution, `tests/test_mcp_standalone_wire_ipc_repro.py` runs its test suite. Instead of relying on local socket implementation code, it imports the client and parser from `tests/helpers/raw_tcp_client.py`. All tests execute seamlessly, validating packet fragmentation, 100-request pipelining bursts, and rapid socket re-binding without regression.

#### Scenario 2: Future MCP Test Suite Adopting Shared Helper
A developer working on a new MCP test suite (e.g., PYPOST-1417 MCP proxy wire stress tests) needs to inject fragmented JSON-RPC frames over a TCP socket. Rather than writing socket management and chunked response decoding logic from scratch, the developer imports `RawTcpWireClient` and `parse_jsonrpc_from_response` directly from `tests.helpers.raw_tcp_client`. The new tests are implemented quickly and reliably using proven wire testing infrastructure.

## Q&A

**Q: Why is extracting this helper prioritized as technical debt reduction?**  
A: Defining low-level network socket and protocol parsing logic inside an individual test file leads to code duplication across future test suites, creates monolithic test modules, and introduces maintenance divergence when wire handling logic needs fixes or improvements. Extracting it establishes a single source of truth for raw TCP testing in PyPost.

**Q: Why not import `RawTcpWireClient` directly from `tests/test_mcp_standalone_wire_ipc_repro.py` in other tests?**  
A: Cross-importing between test files is an anti-pattern. It couples unrelated test suites, complicates test runner discovery, and can lead to circular dependencies or unintended test execution side effects. Test utilities belong in `tests/helpers/`.

**Q: Does this task introduce any changes to production code?**  
A: No. This task modifies test infrastructure and test suites only. Production code under `pypost/` remains completely untouched.

**Q: Will existing test coverage or timing be impacted?**  
A: No. The extraction is a structural refactoring of test infrastructure. All existing test cases, assertions, timeout parameters, and wire behaviors remain preserved.
