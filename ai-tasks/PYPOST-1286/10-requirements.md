# PYPOST-1286: Eliminate flakiness in WebSocket stream export and template strict-conversion tests

## Goals

The PyPost engineering lifecycle relies on automated quality gates (`make check`, `make test`)
to guarantee application correctness, maintain developer velocity, and allow autonomous agents
to make rapid, verified contributions. When tests exhibit non-deterministic, flaky behavior
under multi-worker parallel execution, the integrity of these quality gates is compromised.

During task PYPOST-1285, two automated tests were identified as flaky under full-suite parallel
load (failing approximately 1 out of 2 runs in a 349-file parallel run, while consistently
passing when executed alone or in minimal isolated subsets):
1. `tests/test_websocket_stream_view_repro.py`:
   `test_stream_view_transcript_export_actions`
2. `tests/test_template_service.py::TestTemplateServiceRenderString`:
   `test_strict_conversion_keeps_literal_fallback_for_unrelated_failed_token`

This flakiness introduces critical business problems:
- **False Negative Gate Halts**: Automated continuous integration runs and autonomous agent
  runs (such as `sprint-task-runner`) halt when encountering intermittent failures, creating
  friction, delaying feature delivery, and consuming unnecessary compute resources.
- **Erosion of Gate Confidence**: When developers cannot trust that a failed test signals an
  actual code defect, the protective value of the test suite is undermined.
- **Masked Defects**: Flaky tests can mask genuine regressions introduced by other changes if
  intermittent failures are dismissed as background noise.
- **Unreliable Protocol & Template Contracts**: Both affected areas verify critical end-user
  functionality: WebSocket stream transcript export (enabling developers to save and review
  real-time network sessions) and strict template conversion fallback (ensuring safe interpolation
  in API requests). These contracts must be verified deterministically.

The goal of this task is to ensure both tests execute with 100% determinism, complete isolation,
and zero flakiness under full-suite parallel test load, without weakening or skipping any test
assertions.

## Programming Language

- **Implementation language**: Python (per `ai-tasks/PYPOST-1286/00-roadmap.md`). PyPost is a
  desktop application and API client built with Python and PySide6/Qt, with tests orchestrated
  via pytest. Task documentation uses English Markdown.

## Business Entities

- **CI Quality Gate (`make test`, `make check`)**: The verification barrier safeguarding code
  correctness prior to merge or release.
- **Parallel Test Orchestrator**: The multi-process execution harness
  (`scripts/run_parallel_tests.py`) that distributes test files across concurrent worker
  processes.
- **WebSocket Stream Transcript**: The exported artifact (JSON or Plain Text) containing
  recorded WebSocket frame events, timestamps, payloads, and session metadata.
- **Stream Export Operation**: The background task responsible for formatting and persisting
  WebSocket stream data without blocking the user interface.
- **Template Evaluation Service**: The core interpolation engine (`TemplateService`) that parses
  and substitutes dynamic expressions and environment variables into request definitions.
- **Strict-Conversion Fallback Policy**: The behavioral contract specifying that when an
  invalid conversion function fails, it must fail safely, but unrelated tokens must preserve
  their literal expression syntax fallback.

## User Stories

- As a **PyPost Developer and Autonomous Agent**, I want `make test` and `make check` to run
  cleanly and deterministically across all parallel workers, so that valid pull requests and
  workflow steps never fail spuriously.
- As an **API Developer using WebSockets**, I want transcript export functionality to be
  rigorously and deterministically verified in automated tests, so that I can rely on export
  files for session debugging without risk of underlying race conditions or hangs.
- As a **Developer composing Request Templates**, I want strict type conversion fallback
  behavior to be verified deterministically under all test execution conditions, ensuring my
  request templates evaluate reliably in production.
- As a **Release Engineer & Quality Guardian**, I want all tests across the 349-file suite to
  maintain 100% pass consistency across consecutive parallel runs, without masking issues via
  timeout increases, assertion weakening, or test skips.

## Definition of Done

This task is considered done when all the following acceptance criteria are satisfied:

1. **Deterministic Parallel Execution**: Both target tests pass with 100% consistency across
   consecutive full-suite parallel runs (`make test` across all 349 files with standard worker
   concurrency):
   - `tests/test_websocket_stream_view_repro.py`:
     `test_stream_view_transcript_export_actions`
   - `tests/test_template_service.py::TestTemplateServiceRenderString`:
     `test_strict_conversion_keeps_literal_fallback_for_unrelated_failed_token`
2. **Deterministic Isolated Execution**: Both target tests pass reliably when executed
   individually or in ad-hoc test subsets via `make test PYTEST_ARGS='...'`.
3. **Flakiness Eliminated**: The observed failure rate under full parallel load (previously
   observed at ~1 fail per 2 runs) is reduced to 0 across at least 3 consecutive verification
   runs.
4. **Hermetic Test Isolation**: Tests execute independently of execution order, previous test
   side-effects, or shared cross-test state.
5. **Robust Concurrency & Lifecycle Handling**: Asynchronous background operations in the
   WebSocket stream view export cleanly complete, manage busy states, and clean up worker
   resources without timing hazards, thread leaks, or uncoordinated event loop polling.
6. **Preservation of Test Coverage & Assertions**: All existing test assertions in both test cases
   remain fully enforced. No assertions may be removed, relaxed, commented out, or marked with
   skip or xfail annotations.
7. **Clean Quality Gates**: The repository passes `make check`, `make lint`, `make typecheck`,
   and `make verify-ai-tasks` with zero errors or warnings.
8. **Line Length Compliance**: All task documentation and code files strictly adhere to the
   repository standard of <= 100 characters per line.

## Task Description

### Problem Statement

During triage of task PYPOST-1285 (sprint 2019), a full test run (`make test` across 349 files)
intermittently failed on two specific tests:

1. `tests/test_websocket_stream_view_repro.py`:
   `test_stream_view_transcript_export_actions`
2. `tests/test_template_service.py::TestTemplateServiceRenderString`:
   `test_strict_conversion_keeps_literal_fallback_for_unrelated_failed_token`

When run in isolation (or with small batches of selected test files), both tests pass cleanly.
The failures only manifest under full parallel load where multi-worker CPU/IO contention occurs
and multiple test files execute in arbitrary sequence.

The root causes identified for investigation are:
- **WebSocket Export Test Flakiness**: The export actions invoke asynchronous background worker
  threads (`WebSocketStreamExportWorker`) that process file export off the main thread. Under
  parallel CPU and I/O load, sequential export actions (JSON followed by text) can encounter
  timing races between file creation, worker completion signals, busy-state flag resets, and
  event-loop process-until waits, leading to skipped exports or timeouts.
- **Template Strict-Conversion Fallback Flakiness**: The template evaluation engine verifies
  strict type conversions and literal fallback when unrelated tokens fail. Under parallel
  execution or specific file ordering, cross-test state mutations (such as global function
  registries, template environment caches, or resolver singletons) can perturb evaluation
  outcomes, causing unexpected conversion errors instead of literal fallback.

### Scope Boundaries

#### In Scope

- Requirements definition for deterministic, flake-free execution of both affected test cases.
- Ensuring reliable test execution under multi-worker parallel execution (`make test`) and
  isolated execution.
- Ensuring asynchronous worker lifecycle, thread cleanup, and wait synchronization are fully
  deterministic under heavy load.
- Ensuring template evaluation, function resolution, and caching mechanisms are completely
  isolated and resilient against cross-test contamination.
- Verifying stability across multiple consecutive test suite runs.

#### Out of Scope

- Modifying the public business behavior or file formats of WebSocket transcript exports.
- Altering the user-facing template syntax or strict conversion rules of TemplateService.
- Reworking the architecture of the parallel test runner itself (`scripts/run_parallel_tests.py`).
- Deleting, skipping, or weakening any assertions in the test suite.

### Constraints and Assumptions

- All commands and verifications must strictly run via `make` targets (`make test`, `make check`,
  etc.) per `AGENTS.md`. Direct invocation of pytest or other tools is prohibited.
- Bounded timeouts must be respected per repository testing guidelines.
- No code or architectural changes are implemented during this requirements phase.
- All artifact lines must be strictly <= 100 characters.

### Non-Functional Requirements

- **Determinism**: Test execution outcomes must be 100% reproducible regardless of concurrency,
  CPU load, or test suite execution order.
- **Hermetic Isolation**: Zero shared mutable state across test cases or test workers; all
  fixtures and services must clean up completely.
- **Robustness**: Asynchronous operations must handle timing variations without race conditions,
  busy-state collisions, or orphaned background threads.

## Q&A

- **Q: Why are these test failures considered debt rather than standard test bugs?**
  **A**: The production features (exporting WebSocket transcripts and rendering template
  fallbacks) function correctly, but the test automation exhibits flakiness under high parallel
  worker contention. Fixing this resolves test infrastructure fragility and ensures trustworthy CI.

- **Q: Why not simply mark the flaky tests as `@pytest.mark.flaky` or `@pytest.mark.xfail`?**
  **A**: Marking tests as flaky or xfail masks potential synchronization bugs, thread leaks, or
  global state pollution, allowing real regressions to slip through. The repository standard
  requires deterministic tests that pass 100% of the time.

- **Q: What is the failure rate observed for these tests?**
  **A**: Approximately 1 failure in 2 full-suite parallel runs during PYPOST-1285. In isolation,
  both tests pass 100% of the time.

- **Q: Does this task require modifying production code or only test code?**
  **A**: If flakiness is caused by production race conditions (such as uncoordinated thread
  state transitions or thread cleanup leaks in the export worker), production code may be
  refined in Step 4. If flakiness is caused by test fixture isolation or wait helpers, test code
  will be updated. Step 1 defines the functional and non-functional requirements without
  prescribing the implementation.

- **Q: What is the verification threshold for declaring flakiness resolved?**
  **A**: Both tests must pass reliably in isolation and across multiple consecutive full-suite
  parallel test executions under high load without a single failure.
