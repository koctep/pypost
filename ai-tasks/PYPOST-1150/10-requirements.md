# PYPOST-1150: Fix test_metrics_protocol tracker protocol isinstance failure and establish protocol conformance

## Goals

Ensure robust contract adherence and protocol conformance across all metrics tracker implementations in PyPost. From a business and platform engineering perspective:
- **Observability Reliability & Trustworthiness**: Observability and metrics collection provide vital insights into application health, performance, user behavior, and error rates across PyPost's services, background workers, and user interface. If metrics trackers do not conform reliably to the metrics tracking protocol, services using the metrics interface can encounter runtime errors, dropped telemetry events, or type checking failures.
- **Architectural Decoupling & Interchangeability**: PyPost relies on the dependency inversion principle: application components depend on an abstract metrics tracking protocol (`MetricsTrackerProtocol`), not concrete implementations. Concrete trackers (`MetricsManager` for Qt desktop runtime, `NullMetrics` for headless or disabled telemetry, and `OtelMetricsTracker` for OpenTelemetry export) must remain drop-in interchangeable. Conformance must be guaranteed so swapping tracker implementations in production or testing never breaks tracking callers.
- **Elimination of Protocol Drift**: As new features and instrumentation events are added to the application (e.g., MCP client lifecycle, WebSocket sessions, template rendering), trackers can silently drift apart if protocol conformance is not continuously and rigorously verified across all tracker implementations.
- **CI Test Suite Integrity**: The test failure reported in PYPOST-1149 (`tests/test_metrics_protocol.py::test_metrics_manager_satisfies_tracker_protocol`) must be resolved with full evidence, ensuring the test suite passes cleanly and regression tests permanently guard against future tracker protocol drift.

## Programming Language

- **Python**

## User Stories

### US-1: Core Service Developer
**As an** engineer writing or maintaining core services, workers, or UI presenters,  
**I want** to depend on `MetricsTrackerProtocol` with the certainty that any injected metrics tracker (`MetricsManager`, `NullMetrics`, or `OtelMetricsTracker`) strictly fulfills the protocol contract,  
**So that** calls to track metrics never raise `AttributeError`, fail type checking, or behave inconsistently depending on which tracker is active.

### US-2: Systems Operator
**As an** operator configuring telemetry in desktop or production headless environments,  
**I want** all supported tracker implementations to conform to the same tracking contract without method drift,  
**So that** metrics collection remains complete and predictable regardless of whether metrics are handled by the local Qt manager, exported to OpenTelemetry, or bypassed with null metrics.

### US-3: CI / Test Automation Maintainer
**As a** CI pipeline maintainer,  
**I want** automated tests to verify protocol conformance across all metrics tracker implementations,  
**So that** any addition or alteration to the metrics tracking interface immediately flags missing or mismatched implementations in all trackers before merging.

## Definition of Done

1. **Acceptance Criteria 1: Tracker Protocol Conformance**:
   - `MetricsManager` satisfies `MetricsTrackerProtocol` via runtime protocol check (`isinstance(MetricsManager(), MetricsTrackerProtocol)` is `True`).
   - `NullMetrics` and `NULL_METRICS` satisfy `MetricsTrackerProtocol` (`isinstance` checks evaluate to `True`).
   - `OtelMetricsTracker` satisfies `MetricsTrackerProtocol` (`isinstance` checks evaluate to `True` when OpenTelemetry is available).
2. **Acceptance Criteria 2: Protocol Drift Prevention & Comprehensive Method Parity**:
   - Every method declared in `MetricsTrackerProtocol` is implemented by `MetricsManager`, `NullMetrics`, and `OtelMetricsTracker`.
   - Any method added to any tracker for metrics tracking purposes is reflected across all implementations and the protocol contract.
   - `NullMetrics` safe execution: All tracking methods on `NullMetrics` can be invoked without error and return expected no-op results.
3. **Acceptance Criteria 3: Automated Regression Guard**:
   - `tests/test_metrics_protocol.py` (and related metrics test suites) passes cleanly in the test runner.
   - Automated testing verifies that all tracker implementations conform to the protocol contract, protecting against future protocol drift.
4. **Acceptance Criteria 4: Technical Debt Ledger Reconciliation**:
   - The pre-existing tech-debt entry in `ai-tasks/PYPOST-1149/60-tech-debt.md` for `test_metrics_protocol.py::test_metrics_manager_satisfies_tracker_protocol` is updated or cross-referenced with the investigation findings.
5. **Acceptance Criteria 5: Quality Gate**:
   - Repository quality gates (`make check`, including linting, tests, and type checking) pass cleanly.

## Task Description

### Background
During the execution of PYPOST-1149 (parallel test runner orchestration), a pre-existing test failure was identified and logged in `ai-tasks/PYPOST-1149/60-tech-debt.md`:
- Node: `tests/test_metrics_protocol.py::test_metrics_manager_satisfies_tracker_protocol`
- Symptom: `MetricsManager` failed the runtime `isinstance(..., MetricsTrackerProtocol)` check.

Historical investigation reveals that during earlier WebSocket metrics addition (PYPOST-1136), dynamic delegation (`__getattr__`) was introduced to `MetricsManager` to circumvent file size caps. Because Python's `@runtime_checkable` inspects class-level attributes rather than dynamic `__getattr__`, `isinstance` failed. Subsequently, PYPOST-1146 modularized `MetricsManager` using explicit mixins (`MetricsTrackingMixin`, `MetricsWebSocketMixin`), which restored class-level method definitions.

However, the protocol contract surface is extensive (40+ tracking methods across HTTP requests, responses, MCP client and server interactions, template evaluations, variable resolutions, encryption, and WebSocket sessions). To prevent future protocol drift and ensure architectural soundness, this task establishes protocol conformance across all three tracker implementations:
1. `MetricsManager` (PySide6/Qt desktop facade)
2. `NullMetrics` (Default safe no-op implementation)
3. `OtelMetricsTracker` (OpenTelemetry export implementation)

### Functional Requirements
1. **Runtime Conformance**: All metrics tracker implementations must satisfy runtime protocol checks for `MetricsTrackerProtocol`.
2. **Method Completeness**: Every method specified in `MetricsTrackerProtocol` must be implemented in `MetricsManager`, `NullMetrics`, and `OtelMetricsTracker`.
3. **No-Op Safety**: `NullMetrics` must provide safe no-op implementations for all protocol methods so that components running without telemetry enabled never raise exceptions.
4. **Resolution Helper Integrity**: `resolve_metrics` must return the provided tracker when present and default to `NULL_METRICS` when `None` is provided, preserving typing contracts.
5. **Drift Detection**: The test suite must include automated regression checks that detect any divergence in method availability among `MetricsTrackerProtocol`, `MetricsManager`, `NullMetrics`, and `OtelMetricsTracker`.

### Non-Functional Requirements
- **Reliability**: No metrics tracking call should ever fail unexpectedly due to missing attributes or unimplemented protocol methods.
- **Maintainability**: Clear protocol definitions and explicit tracker contracts avoiding fragile dynamic attribute delegation.
- **Test Execution**: Conformance verification tests must run efficiently within the test suite timeout constraints.

### System Boundaries and Scope
- **In Scope**:
  - Verification of protocol conformance for `MetricsManager`, `NullMetrics`, and `OtelMetricsTracker`.
  - Comprehensive protocol conformance and drift prevention tests in `tests/test_metrics_protocol.py` (and OTel metrics test suite).
  - Updating tech debt documentation in `ai-tasks/PYPOST-1149/60-tech-debt.md`.
- **Out of Scope**:
  - Modifying the underlying Prometheus or OpenTelemetry metric names, types, or label schemas (telemetry semantics remain unchanged).
  - Modifying unrelated test failures or audit baselines noted in other tickets (e.g., PYPOST-1111, PYPOST-1110, PYPOST-1151).
  - Redesigning Qt UI components or business logic callers of metrics.

### Main Entities
- **MetricsTrackerProtocol**: The abstract contract defining the required tracking operations across PyPost domains (HTTP, MCP, Templates, Encryption, WebSockets).
- **MetricsManager**: The Qt-aware facade that adapts GUI and backend signals to metrics registry operations for Prometheus scraping in the desktop client.
- **NullMetrics**: The no-op tracker used when metrics tracking is not configured or in unit tests where telemetry is irrelevant.
- **OtelMetricsTracker**: The OpenTelemetry-backed tracker translating protocol calls into OpenTelemetry counters and gauges.
- **Metrics Consumer**: Any service, worker, or UI component that receives a `MetricsTrackerProtocol` instance and records operational telemetry.

## Q&A

**Q1: Why did `tests/test_metrics_protocol.py` fail in PYPOST-1149?**  
**A1:** PYPOST-1136 introduced WebSocket metrics via `__getattr__` dynamic delegation in `MetricsManager` to keep file line counts within limits. Because Python's `@runtime_checkable` checks class attributes rather than instance dynamic lookup, `isinstance(MetricsManager(), MetricsTrackerProtocol)` returned `False`. While PYPOST-1146 subsequently split delegation into explicit mixins, comprehensive protocol conformance and drift protection across all trackers were not fully locked.

**Q2: Why must `OtelMetricsTracker` and `NullMetrics` be checked alongside `MetricsManager`?**  
**A2:** PyPost supports multiple environments: desktop with Prometheus (`MetricsManager`), headless/test without telemetry (`NullMetrics`), and production with OpenTelemetry (`OtelMetricsTracker`). If a method is added to `MetricsTrackerProtocol` and `MetricsManager` but omitted from `NullMetrics` or `OtelMetricsTracker`, calling code running in headless or OTel environments will crash at runtime with `AttributeError`. Conformance must be established across all three implementations.

**Q3: Does `@runtime_checkable` guarantee that signatures and arguments match?**  
**A3:** No. Python's runtime `isinstance` on a Protocol only verifies that the attribute exists and is callable; it does not check parameter names or types. Therefore, the specification requires both attribute presence and automated parity checks to prevent subtle parameter drift.

**Q4: Will existing metrics callers or Prometheus outputs change?**  
**A4:** No. This task focuses purely on contract compliance, method parity, and test integrity. The telemetry events, counters, gauges, and scraped outputs remain identical.
