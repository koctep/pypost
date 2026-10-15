# PYPOST-1370: Background folding scanner for large documents

## Programming Language

Python

## Goals

PyPost is an API client used by software developers, QA engineers, and system architects to test, debug, and monitor HTTP, REST, WebSocket, and MCP services. In modern distributed systems and microservice architectures, API responses and request bodies frequently contain large payloads—ranging from hundreds of kilobytes to tens of megabytes of structured JSON, YAML, or XML (such as database export dumps, system telemetry streams, bulk product catalogs, and detailed API schemas).

To help users navigate and understand these complex structured documents, PyPost provides hierarchical code folding in both interactive editors (Request Body) and read-only viewers (Response View, WebSocket Stream View, MCP Tool Result View).

Currently, fold region discovery parses the document structure synchronously on the main application interface thread. For standard payloads under a few hundred kilobytes, this parsing is imperceptible. However, when users inspect or edit large documents exceeding 500 KB:

- **UI Thread Freezing and Frame Drops**: Synchronous AST parsing and token discovery consume substantial CPU time, causing the user interface to freeze momentarily or drop frames during document rendering and interaction.
- **Degraded Authoring Experience**: When typing or pasting in the Request Body editor, synchronous parsing blocks the main event loop, causing noticeable input lag, delayed cursor movement, and stuttering.
- **Disrupted Navigation and Inspection**: Scrolling, searching, or switching between request/response tabs locks up until parsing completes, frustrating users who need quick feedback.

The business goals of this task are:

- **Uncompromised UI Responsiveness**: Ensure the PyPost user interface remains completely fluid, responsive, and smooth at all times, even when handling multi-megabyte payloads.
- **Non-Blocking User Experience**: Decouple intensive document structure parsing from user interactions so that typing, scrolling, text selection, and window resizing occur without interruption or perceptible latency.
- **Seamless Progressive Enrichment**: Allow users to immediately inspect and interact with large documents, while code folding indicators appear cleanly once background analysis completes.
- **Enterprise-Grade Payload Handling**: Support real-world large payloads (such as bulk data exports and extensive API responses) reliably without application freezes or degradation.

## User Stories

- As an **API developer inspecting large API response payloads (>500 KB)**, I want the application window and document viewer to remain completely responsive during loading and rendering so that I can scroll, inspect, and select text without any lag or frozen UI frames.
- As an **API developer authoring or modifying large request bodies**, I want typing, deleting, and cursor navigation to respond instantaneously without pauses while structure scanning takes place.
- As an **API developer**, I want fold indicators (chevrons and margins) to appear accurately on large documents as soon as structural analysis completes, without disrupting my active reading or editing position.
- As an **API developer making rapid sequential edits to a document**, I want outdated structure scan requests to be cancelled or superseded so that system resources are not wasted computing folding data for obsolete revisions.
- As an **API developer triggering bulk actions like "Fold All" or "Unfold All"**, I want the action to execute predictably and reliably even if a background scan is currently in progress or recently initiated.
- As a **PyPost maintainer**, I want a clear threshold-based separation between fast synchronous scanning for small payloads and background scanning for large payloads so that small documents incur zero asynchronous coordination overhead while large documents protect the UI thread.
- As a **quality engineer**, I want comprehensive automated test coverage confirming that background scanning produces identical fold region structures to synchronous parsing, without introducing race conditions, memory leaks, or stale fold markers during concurrent document modifications.

## Definition of Done

This task is considered done when:

1. **Non-Blocking UI Execution**: Fold region discovery and structural parsing for documents exceeding 500 KB do not execute on the main UI thread; the UI maintains full fluidity (no dropped frames or input lag during typing, scrolling, or tab switching).
2. **Threshold-Based Activation**: Payloads exceeding the 500 KB threshold automatically utilize background processing for fold region discovery, while smaller payloads continue to be processed with minimal overhead.
3. **Equivalence of Scan Results**: Fold regions, hierarchy levels, line ranges, and block headers identified via background scanning are 100% identical to those produced by synchronous scanning across all supported formats (JSON, YAML, XML).
4. **Thread Safety & Data Integrity**: Document modifications occurring while a background scan is active do not cause race conditions, crashes, memory corruption, or desynchronized line/block mappings.
5. **Superseded Scan Cancellation**: When document content changes while a background scan is in flight, the obsolete scan is cancelled or superseded, and only results corresponding to the latest document revision are applied to the view.
6. **State Preservation Across Scans**: Existing collapsed or expanded fold states are preserved after background scan completion for all fold regions whose structural boundaries have not changed.
7. **Predictable Bulk Action Behavior**: Invoking bulk operations (such as "Fold All", "Unfold All", or format re-detection) behaves consistently and deterministically when background scans are pending, active, or complete.
8. **Preservation of Existing Capabilities (Zero Regressions)**: All existing editor and viewer features—including syntax highlighting, variable autocompletion, search match reveal, sensitive field masking, and gutter chevron presentation—continue to operate without regression.
9. **Automated Verification**: Automated tests verify non-blocking execution, correct fold discovery for large payloads (>500 KB), cancellation of stale scans under rapid document updates, and stability across supported formats.
10. **Quality Gate Compliance**: Repository quality gates (`make check`, including linting, typechecking, and task artifact verification) pass cleanly.

## Task Description

### Problem Statement

In PyPost, folding controllers inspect document contents to identify collapsible blocks (such as JSON objects and arrays, YAML mappings and lists, and XML tags). Currently, this scan runs on the application UI thread after an edit debounce period.

For documents under 500 KB, parsing completes in a few milliseconds and is imperceptible. However, when payloads exceed 500 KB—and especially multi-megabyte payloads—AST parsing and line-offset traversal take hundreds of milliseconds or several seconds. Because this computation runs on the UI thread, it completely blocks the Qt event loop. As a result:

- The application window becomes unresponsive ("beachball" / frozen window).
- Keystrokes typed while editing are delayed or buffered unevenly.
- Scrolling jumps erratically once parsing finishes.
- Frame rates drop to zero during the scan duration.

This creates a degraded experience for developers dealing with production API payloads. Offloading fold region discovery for documents exceeding 500 KB to a background worker ensures that the UI thread remains completely fluid.

### Scope (In-Scope)

- Offloading fold region discovery for large documents exceeding 500 KB to background execution.
- Maintaining fast, lightweight scanning behavior for small documents below the threshold.
- Cancelling or superseding in-flight background scans when the document changes before analysis finishes.
- Safely delivering completed scan results back to the presentation layer without freezing the interface.
- Preserving user-expanded and user-collapsed states across background scan updates.
- Ensuring predictable behavior for bulk operations ("Fold All", "Unfold All") in the presence of background scanning.
- Supporting all structured formats currently handled by PyPost folding (JSON, YAML, XML, and plain text).
- Automated unit, integration, and concurrency verification tests.

### Scope (Out-of-Scope)

- Concrete concurrency architecture and thread primitive selections (deferred to Step 2: Architecture).
- Changes to the underlying AST grammar or parsing logic for JSON, YAML, or XML.
- Changes to syntax highlighting engines or color palettes.
- Alterations to format detection heuristics (`detect_body_format`).
- Visual redesigns of gutter chevrons, line numbers, or editor layout.

### Functional Requirements

- **FR-1: Size Threshold Evaluation**: The system must evaluate the document size before initiating a scan. Documents exceeding the 500 KB threshold must be processed asynchronously in the background. Documents below or equal to 500 KB may be processed using standard lightweight execution.
- **FR-2: Non-Blocking User Interaction**: While a background scan is in progress, all user interactions—including typing, cursor movement, text selection, vertical and horizontal scrolling, and window resizing—must remain completely responsive and uninterrupted.
- **FR-3: Background Result Application**: Upon completion of a background scan, the discovered fold regions must be seamlessly integrated into the editor or viewer, updating gutter fold indicators without causing visual flicker, jumpy scrolling, or loss of user focus.
- **FR-4: Invalidation and Cancellation of Stale Scans**: If the document content changes while a background scan is actively executing, the system must invalidate or cancel the obsolete scan so that obsolete results are discarded and resources are freed.
- **FR-5: Fold State Continuity**: Previously collapsed or expanded fold regions must retain their state when background scan results arrive, provided their structural boundaries remain valid.
- **FR-6: Coordination with Bulk Fold Actions**: When a user triggers "Fold All" or "Unfold All", the system must ensure the intended fold state is applied reliably, coordinating gracefully with any running or pending background scans.
- **FR-7: Cross-Format Consistency**: Background scanning must support all structured formats handled by PyPost (JSON, YAML, XML) and deliver identical fold hierarchies to those generated in standard scanning.

### Non-Functional Requirements

- **NFR-1 Fluidity & Responsiveness**: The main user interface thread must never be blocked by fold region parsing for large documents. Frame rates and input responsiveness must remain consistent during scanning.
- **NFR-2 Concurrency Safety**: The background scanning workflow must be free of race conditions, deadlocks, data races, and unhandled exceptions when documents are modified concurrently.
- **NFR-3 Resource Efficiency**: Superseded scans must be aborted promptly to avoid queueing unnecessary CPU work during rapid typing or frequent document updates.
- **NFR-4 Scalability**: The system must smoothly handle payloads of several megabytes (e.g. 5 MB to 20 MB) without crashing, running out of memory, or destabilizing the application.
- **NFR-5 Backward Compatibility**: Existing public interfaces, signals, and properties relied upon by editors, viewers, and tests must remain backward compatible.

### Constraints and Assumptions

- The solution runs within PyPost's Python/Qt application environment on Linux, macOS, and Windows.
- Large documents may be loaded into either interactive editors (`CodeEditor`) or read-only viewers (`FoldableCodeView`).
- Document parsing relies on existing standard library or third-party format parsers (e.g., standard JSON, PyYAML, ElementTree).

### Main System Entities & Domain Interactions

| Domain Entity | Responsibility |
| --- | --- |
| **Document Content** | The textual payload (request body or response body) undergoing editing or inspection. |
| **Structure Scanner** | Domain component responsible for parsing document syntax and extracting hierarchical fold regions. |
| **Scan Coordinator** | Component that evaluates document size thresholds, schedules background or synchronous scans, and manages cancellation of obsolete scan tasks. |
| **Background Scan Worker** | Execution unit that performs CPU-intensive AST parsing and fold region extraction off the main UI thread. |
| **Fold State Manager** | Maintains the active list of fold regions, tracks user collapsed/expanded states, and coordinates visibility updates. |
| **Gutter Presentation** | Visual component displaying line numbers and fold chevrons, reflecting the latest confirmed fold regions. |

## Q&A

- **Q1: Why is 500 KB chosen as the threshold for background execution?**
  - **A**: Parsing payloads smaller than 500 KB typically finishes within single-digit milliseconds, where synchronous processing has negligible impact on user perception and avoids thread dispatch overhead. For payloads exceeding 500 KB, AST parsing times scale with document complexity and quickly exceed human perception thresholds (16–100 ms), resulting in noticeable UI stutter and dropped frames. The 500 KB threshold ensures that responsiveness is preserved where it matters most without unnecessary overhead for small payloads.

- **Q2: Does this requirements document specify whether to use `QThread`, worker pools, or `concurrent.futures`?**
  - **A**: No. In accordance with the Top-Down development methodology, specific architectural choices, class hierarchies, and threading primitives belong strictly in Step 2 (`20-architecture.md`). This document specifies *what* capabilities and behaviors are required from the business and user experience perspective, not *how* they are implemented.

- **Q3: What should happen if a user types rapidly while a background scan is running?**
  - **A**: Each document edit increments the document revision. Any active or pending background scan working on an older revision is superseded or cancelled. Once the user pauses typing (or the document settles), a new scan is scheduled for the current content, ensuring that obsolete computation is discarded.

- **Q4: What should happen if a user clicks "Fold All" before background parsing completes on a large document?**
  - **A**: The system should record the user's intent to collapse all blocks so that when the background scan delivers the discovered fold regions, they are immediately collapsed, or it should ensure that the scan completes gracefully before applying the fold state, without freezing the interface.

- **Q5: Will background scanning alter the visual appearance of the editor or gutter?**
  - **A**: No visual design changes are introduced. Gutter width calculation, line numbers, and chevron indicators will render identically to today's appearance; the enhancement is entirely focused on eliminating UI freezes and maintaining complete responsiveness during parsing.
