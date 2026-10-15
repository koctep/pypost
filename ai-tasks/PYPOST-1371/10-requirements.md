# PYPOST-1371: Stress & edge-case payload test suite

## Programming Language

Python

## Goals

PyPost is an API client used by software developers, QA engineers, and system architects to test, debug, and monitor HTTP, REST, WebSocket, and MCP services. During real-world network operations and API development workflows, incoming responses frequently deviate from clean, well-formed specifications. Payloads may arrive truncated due to prematurely terminated HTTP streams or socket disconnects, contain corrupt or malformed syntax (such as unbalanced XML tags, invalid YAML indentation, or dangling entity references), or reach massive sizes exceeding 10 MB (such as database dumps, bulk catalog exports, or extensive diagnostic traces).

When PyPost renders, scans, and folds structured documents (JSON, YAML, XML), these irregular payloads pose severe operational risks:

- **Application Crashes and Unhandled Exceptions**: Syntax scanners or format detection logic that fail to anticipate malformed or partial syntax can raise unhandled exceptions (e.g., parsing crashes, index errors, recursion limit errors), terminating the application or breaking the response viewer widget.
- **UI Freezes and Application Unresponsiveness**: Processing oversized payloads (>10 MB) without strict resource and time boundaries can exhaust CPU and memory resources or induce severe main-thread stalls, leaving the user interface completely unresponsive.
- **Silent Failure and Loss of User Work**: If the response viewer encounters corrupt data, it must not drop user context, discard response body text, or corrupt clipboard copies. Users must always be able to view and inspect raw response data even when structural folding or syntax highlighting cannot be computed.
- **CI Test Suite Stalls**: In continuous integration pipelines and automated regression gates, unconstrained stress tests can hang indefinitely or consume excessive memory if not governed by strict execution timeouts.

The primary business goals of this task are:

1. **Rock-Solid Application Stability**: Guarantee that PyPost never crashes, throws unhandled UI exceptions, or corrupts viewing state when presented with malformed, truncated, or hostile payloads.
2. **Graceful Error Handling and Degradation**: Ensure that when structured scanning or folding cannot parse a document, the application degrades gracefully to raw text presentation without alarming error popups or disrupted user workflows.
3. **Resilience to Extreme Payload Sizes (>10 MB)**: Validate that documents exceeding 10 MB are handled safely, with scanning either completing within predictable timeframes or safely deferring/skipping folding to protect system memory and interactive responsiveness.
4. **Deterministic and Time-Bounded Verification**: Deliver an automated test suite with explicit execution timeouts for all stress scenarios, preventing CI test hangs and ensuring automated quality gates remain fast, robust, and reliable.

## User Stories

- As an **API developer receiving an incomplete or truncated network response** (e.g., due to an interrupted connection or proxy timeout), I want PyPost to display the partial response text without crashing or popping modal errors, so that I can diagnose the premature connection termination.
- As an **API developer debugging an upstream service producing malformed XML or YAML** (e.g., unbalanced tags, improper indentation, or syntax errors), I want PyPost to safely render the raw text and gracefully omit or limit folding, so that I can identify the syntax error in the response content without viewer dysfunction.
- As an **API developer inspecting massive API payloads exceeding 10 MB** (e.g., batch exports, large database snapshots, or high-volume event streams), I want the application to remain stable, responsive, and bounded in resource usage, so that I can inspect the data without freezing my desktop environment.
- As a **QA engineer or PyPost maintainer**, I want a dedicated automated stress test suite covering edge-case and oversized payloads with explicit per-test timeouts, so that regressions in payload parsing, memory limits, or execution time are caught automatically in CI without risking hanging builds.
- As a **PyPost maintainer**, I want clear assertions that malformed payload processing does not leak memory, spawn orphaned background worker threads, or leave the editor in an inconsistent internal state.

## Definition of Done

This task is considered complete when:

1. **Automated Stress Test Suite Implemented**: A comprehensive automated test suite is implemented in the repository test suite, targeting edge-case, malformed, truncated, and extreme-size (>10 MB) payloads.
2. **Truncated Payload Coverage**: Automated tests verify that truncated XML and YAML payloads (e.g., cut off at arbitrary byte boundaries, unclosed tags, truncated strings, incomplete mapping keys) are parsed without unhandled exceptions and degrade gracefully to plain text view.
3. **Malformed Payload Coverage**: Automated tests verify that syntactically malformed XML and YAML documents (e.g., mismatched closing tags, illegal indentation mixes, duplicate anchor declarations, invalid characters) do not trigger unhandled exceptions or destabilize the application.
4. **Extreme Payload (>10 MB) Coverage**: Automated tests verify that large payloads exceeding 10 MB (JSON, YAML, and XML) are processed safely without memory exhaustion, infinite loops, or application crashes.
5. **Strict Explicit Test Timeouts**: Every stress and edge-case test case declares an explicit execution timeout, ensuring tests fail deterministically if execution stalls and preventing CI hangs.
6. **Graceful Fallback Verification**: Tests confirm that upon parsing failure or payload size exceeding safe operational limits, the view preserves full raw text access, search capabilities, and copy functionality without corrupting the document buffer.
7. **Zero UI / Worker Thread Leaks**: Tests confirm that abortive or failed parsing on stress payloads cleanly terminates background scan tasks without leaving lingering background threads or accumulating uncollected memory.
8. **Repository Quality Gates Pass**: All repo quality gates (`make check`, including `lint`, `test`, `typecheck`, and `verify-ai-tasks`) pass cleanly without errors or warnings.

## Task Description

### Problem Statement

During normal HTTP and API operations, PyPost encounters a wide diversity of payloads. While standard happy-path tests validate valid JSON, YAML, and XML documents up to a few hundred kilobytes, edge-case and adversarial conditions frequently occur in production environments:

- **Truncated streams**: A server closes the socket mid-response, yielding partial XML tags (e.g., `<root><item id="1">...`) or truncated YAML blocks (e.g., `items:\n  - name: "alpha"\n    sub:`).
- **Malformed documents**: Broken server implementations emit invalid YAML or XML with syntax errors, mismatched tags, illegal control characters, or unclosed quotes.
- **Massive payloads (>10 MB)**: Large data transfers, such as database backups, machine learning training sets, or catalog exports, generate payloads ranging from 10 MB to 20+ MB.

Without dedicated stress and edge-case testing:
1. Parsers may raise uncaught exceptions (e.g., `yaml.YAMLError`, `xml.etree.ElementTree.ParseError`, `RecursionError`) that bubble up to GUI event handlers.
2. Parsers may enter high-complexity parsing loops (such as quadratic nesting traversal or entity expansion) that freeze execution indefinitely.
3. Test suites in CI risk hanging permanently if a parser deadlocks or stalls on a 10+ MB file, lacking explicit per-test timeouts.

This task establishes an automated stress and edge-case payload test suite to systematically validate stability, bounded execution time, and graceful degradation across all supported document types.

### Scope (In-Scope)

- Creation of automated stress tests validating parser behavior and viewer stability against:
  - Truncated XML documents (unclosed tags, truncated attributes, incomplete entity definitions, EOF mid-tag).
  - Truncated YAML documents (dangling keys, incomplete multiline strings, truncated list items, abrupt EOF).
  - Malformed XML documents (mismatched start/end tags, illegal XML characters, duplicate attributes, invalid root structures).
  - Malformed YAML documents (tab/space mixing errors, invalid indentation levels, unescaped reserved tokens, malformed anchors).
  - Large payloads (>10 MB) across JSON, YAML, and XML formats.
- Enforcing explicit test timeouts on every test case in the stress suite using pytest timeout mechanisms.
- Verification that parsing failures result in graceful fallback to plain text inspection with zero unhandled exceptions.
- Verification that background worker threads terminate cleanly upon encountering malformed or oversized content.
- Verification that search, text copy, and document presentation remain functional even when fold region discovery fails or is bypassed.

### Scope (Out-of-Scope)

- Redesigning the underlying third-party parsing libraries (e.g., PyYAML, Python's standard `xml.etree.ElementTree`, or `json` module).
- Implementing new format parsers (e.g., CSV, Protocol Buffers, Avro).
- Implementing streaming parsers for infinite or chunked network streams (this task tests payload inspection within the application widgets and scanners).
- User interface visual redesigns.

### Functional Requirements

- **FR-1: Truncation Tolerance**: The structure scanning and format detection systems must handle truncated XML and YAML payloads without raising unhandled exceptions or corrupting document state.
- **FR-2: Malformed Syntax Resilience**: When presented with syntactically corrupt or invalid XML or YAML, the system must catch all parser errors internally, log appropriate debug diagnostics, and safely return an empty or partial fold structure.
- **FR-3: Large Payload (>10 MB) Safety**: Payloads exceeding 10 MB must be processed within strict execution bounds without causing excessive memory consumption, UI freezing, or process crashes.
- **FR-4: Uncompromised Raw Text Inspection**: In any edge-case or failure scenario, the authentic raw text of the payload must remain fully accessible for viewing, text selection, clipboard copying, and search.
- **FR-5: Deterministic Execution Timeouts**: All stress test cases must execute under explicit test timeout constraints, guaranteeing that tests either complete successfully or fail within the timeout limit.

### Non-Functional Requirements

- **NFR-1 Stability & Zero Crashes**: No stress payload—regardless of size or level of corruption—shall cause an unhandled exception or crash the application process.
- **NFR-2 Execution Boundedness**: All stress tests must complete well within their assigned timeouts under standard CI environments.
- **NFR-3 Resource Efficiency**: Stress testing with 10+ MB documents must not cause uncontrolled memory growth or persistent worker thread leaks.
- **NFR-4 Test Maintainability**: Stress tests must be deterministic, self-contained, reproducible, and generate synthetic test fixtures programmatically to avoid checking multi-megabyte binary blobs into the git repository.

### Constraints and Assumptions

- Tests are implemented in Python using the repository's standard testing framework (`pytest`).
- All test files must strictly adhere to the project's quality standards, including PEP 8 formatting, flake8 linting, and mypy type annotations.
- Every test function must declare an explicit `@pytest.mark.timeout(...)` decorator or class/module-level `pytestmark` in accordance with repository testing standards.
- Synthetic large payloads (>10 MB) should be generated dynamically in fixtures or test helpers rather than stored as static repository assets.

### Main System Entities & Domain Interactions

| Domain Entity | Responsibility |
| --- | --- |
| **Payload Stress Fixtures** | Programmatic generators that construct truncated, malformed, and large (>10 MB) payloads for test execution. |
| **Format Detector** | Evaluates payload content and headers, gracefully handling invalid syntax without crashing. |
| **Structure Scanner** | Parses document text to identify hierarchical blocks, catching syntax errors and returning safe fold models. |
| **Fold Controller & Worker** | Orchestrates synchronous and asynchronous parsing, managing worker lifecycle and timeout bounds. |
| **Stress Test Suite** | Automated test suite exercising scanners, workers, and view widgets under extreme payload conditions with explicit timeouts. |

## Q&A

- **Q1: Why is this task needed if code folding for JSON/YAML/XML is already implemented?**
  - **A**: The initial code folding implementation focused on well-formed, standard-sized payloads. Production network traffic routinely delivers corrupt, partially downloaded, or very large payloads. Without dedicated stress tests, edge cases can cause silent crashes, infinite parsing loops, or UI freezes in production.
- **Q2: Why must payloads > 10 MB be tested specifically?**
  - **A**: Modern APIs frequently return large data sets (e.g., bulk exports or telemetry). Document sizes exceeding 10 MB push parsers to their limits in memory usage and CPU time. Verifying behavior at >10 MB guarantees that the application scales safely and does not crash or exhaust system resources.
- **Q3: Why are explicit test timeouts mandatory?**
  - **A**: Stress tests involving complex syntax parsing or multi-megabyte payloads have a risk of exponential backtracking or thread stalls if a regression is introduced. Explicit timeouts ensure that any regression fails immediately and loudly in CI rather than hanging the build pipeline.
- **Q4: Should multi-megabyte test files be committed to the repository?**
  - **A**: No. Storing 10+ MB files in git bloats repository history and degrades clone performance. All large and stress payloads should be generated programmatically during test execution.
- **Q5: Does this requirements document specify specific data structures, thread pools, or mock objects?**
  - **A**: No. Following the Top-Down development methodology, architectural details, test fixture implementations, and class designs belong in Step 2 (`20-architecture.md`). This document defines the business goals, user stories, scope, and functional requirements.
