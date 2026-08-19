# PYPOST-1088: Fix Linux errno hardcoding and encryption-migration test-order flakiness

## Goals

Continuous integration and developer workflows require reliable, deterministic, and cross-platform test suites. Currently, the test suite suffers from pre-existing failures and flakiness across two distinct areas:
1. Server startup error message assertions fail on Linux systems due to platform-specific error code assumptions in tests.
2. Encryption migration and CLI tests experience order-dependent flakiness and state interference when executed concurrently or in varying sequences.

Resolving these issues ensures that automated quality gates provide accurate signals, prevents false test failures on Linux development environments and CI runners, and guarantees that data encryption migration tooling can be reliably verified without test order sensitivity.

**Implementation language**: Python (quality and test suite reliability remediation within the existing Python codebase; no new runtime language or stack is introduced).

## User Stories

- As a developer running tests on Linux, I want server bind error verification tests to pass reliably so that platform-specific error code differences do not cause false CI failures.
- As a maintainer running full or partial test suites, I want encryption migration and CLI tests to execute deterministically in any order without test pollution or flakiness, so that I can trust regression testing for sensitive data migration features.
- As a release engineer, I want automated quality gates to execute cleanly across all supported operating systems so that builds and releases are not blocked by fragile test assertions or shared test state.

## Definition of Done

- Server bind error message formatting tests execute and pass reliably across all supported operating systems (including Linux) without relying on platform-specific literal error numbers.
- Encryption migration service tests and encryption migration CLI tests execute deterministically and pass regardless of execution order, whether executed individually, sequentially, or within a combined full-suite run.
- The 4 pre-existing test failure node IDs (`test_format_mcp_bind_error_addr_in_use`, `TestFormatBindError::test_metrics_addr_in_use_message`, `test_cli_re_encrypt_dry_run` / CLI stats tests, and `test_bulk_re_encrypt_dry_run_projects_active_kid` / plaintext handling tests) pass cleanly and consistently.
- All modified test cases adhere to project testing conventions, including explicit execution timeouts.
- No regression is introduced to existing runtime server bind handling or encryption migration business capabilities.

## Task Description

During full-suite test runs, four pre-existing test failures were identified across two root causes:
1. Hardcoded platform-specific error code assumptions in test setup for MCP and metrics server bind failure formatting, preventing expected user-friendly error formatting on Linux.
2. Execution order dependence and environment/state sensitivity in encryption migration unit and CLI test cases, causing alternating failures when run together.

This task resolves both sources of test instability to achieve a clean, portable, and order-independent test suite.

### Out of Scope

- Redesigning production server bind error handling logic or user-facing message text.
- Modifying encryption algorithms, key formats, or on-disk storage schemas beyond test reliability requirements.
- Broad refactoring of unrelated CLI commands or server managers.

## Non-Functional Requirements

- **Determinism**: Tests must produce identical pass/fail outcomes regardless of execution sequence or random seed.
- **Portability**: Test assertions must be compatible across Linux, macOS, and other target operating systems.
- **Isolation**: Test fixtures and cases must maintain clean isolation without leaking state or filesystem artifacts across test runs.
- **Performance**: Test execution must remain fast and bounded by explicit timeout limits.

## Main Entities

- **Server Bind Error Reporter**: Component responsible for translating low-level network bind failures into clear, user-facing error guidance.
- **Encryption Migration Service**: Core domain service managing batch re-encryption, key identifier tracking, and data integrity verification for stored environments.
- **Encryption Migration CLI**: Command-line interface allowing operators to inspect, verify, and re-encrypt stored application data.
- **Test Harness / Quality Suite**: Automated verification framework running unit, integration, and CLI test scenarios across multiple target environments.

## User Scenarios

1. **Linux Developer Verification**: A developer runs the server manager and metrics test suites on a Linux workstation; all bind error message assertions pass without platform mismatch errors.
2. **Full Suite Execution**: A CI pipeline or developer runs the entire test suite in default or randomized order; encryption migration and CLI tests complete successfully without flakiness or cross-test interference.
3. **Targeted Sub-Suite Execution**: A maintainer runs only the encryption migration CLI and service test modules together; both modules pass completely and deterministically.

## Q&A

| Question | Answer |
| --- | --- |
| Why is fixing test flakiness and platform-specific error handling considered a business priority? | Flaky and platform-dependent tests degrade trust in automated CI gates, slow down engineering velocity, and risk masking genuine regressions in critical subsystems like server management and data encryption. |
| Does this task alter production user experience or encryption behavior? | No, production behavior remains intact; the changes ensure test fixtures, assertions, and isolation accurately and reliably validate intended runtime behavior across all platforms. |
