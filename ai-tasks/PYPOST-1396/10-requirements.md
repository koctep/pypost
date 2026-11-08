# PYPOST-1396: [PYPOST-1312] Background worker thread formatting for medium-size JSON response masking

## Goals

When developers and QA engineers test APIs with PyPost, response payloads frequently contain sensitive authentication tokens, passwords, customer Personally Identifiable Information (PII), or private secret keys. Through Epic [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312), PyPost provides presentation-layer field masking (`hidden_response_fields`) in the desktop response viewer. Sensitive values are visually masked by default to safeguard against accidental exposure during screen sharing, live demos, and collaborative pairing, while preserving in-place click-to-reveal toggling.

In typical usage, response payloads fall into three distinct operating bands:
1. **Small Payloads (< 50 KB)**: Format and render almost instantly (< 5 ms), producing no perceptible interruption to user interactions.
2. **Very Large Payloads (> 100 KB)**: Bypass heavy formatting and visual token tracking to avoid excessive memory and rendering overhead.
3. **Medium-Sized Payloads (50 KB to 100 KB)**: Contain rich, nested structures with dozens or hundreds of fields. When token parsing, formatting, and interactive span calculations are performed synchronously on the primary user interface thread, they cause noticeable UI stutter, input lag, and frame drops (15–60+ ms pauses). On slower or resource-constrained laptops, this can briefly freeze the user interface during rapid request execution or tab switching.

The business goals of this task are:
- **Maintain Fluid 60 FPS Desktop Responsiveness**: Ensure that inspecting and formatting medium-sized JSON responses (50 KB – 100 KB) with configured field masking never blocks or hitches the user interface thread.
- **Ensure Seamless Developer Experience Across Diverse Hardware**: Protect developer productivity on resource-constrained development machines and virtual desktops by preventing UI freezes while formatting sensitive payloads.
- **Preserve Complete Masking and Interactivity Parity**: Deliver the exact same security protection, visual masking affordances (masked indicators, tooltips), and click-to-reveal behavior as small payloads without visual discrepancies or data corruption.
- **Responsive Preemption and Cancellation**: Ensure that when a user rapidly sends new requests or switches views, ongoing background formatting operations are discarded cleanly, guaranteeing that obsolete data never overwrites current response views.

## Programming Language

- **Implementation language**: Python (for desktop GUI components, asynchronous worker orchestration, and automated test suites).

## User Stories

- As an **API Developer testing cloud microservices**, I want the PyPost desktop interface to remain silky smooth and responsive (allowing uninterrupted scrolling, typing, and tab switching) when receiving 50 KB – 100 KB responses with masked fields, so that my workflow is not interrupted by interface freezes or dropped inputs.
- As a **Presenter conducting live product demonstrations or screen shares**, I want medium-sized responses to display masked sensitive tokens reliably without freezing the UI on response arrival, so that private keys remain concealed and the presentation appears professional and responsive.
- As an **Active Power User rapidly executing requests in succession**, I want obsolete formatting computations from previous responses to cancel immediately when a new response arrives, so that stale response content never replaces or interferes with the latest request result.
- As a **Software Engineer running PyPost on a budget laptop or VM**, I want consistent user interface performance regardless of CPU speed when viewing medium-sized responses with sensitive field masking.
- As a **PyPost Maintainer**, I want clear separation between asynchronous presentation formatting and the main UI event loop, verified through automated tests without flaky race conditions or test timeouts.

## Definition of Done

This task is considered complete when:

1. **Non-Blocking UI Responsiveness**:
   - Processing, parsing, and token span formatting for medium-sized JSON payloads (between 50 KB and 100 KB) with configured `hidden_response_fields` does not freeze or block the primary application thread.
   - The user interface maintains responsive event processing (smooth cursor movement, scrolling, and window management) while formatting is in progress.

2. **Full Functional & Visual Parity**:
   - Formatted output for medium-sized payloads matches synchronous formatting output character-for-character.
   - All configured sensitive fields are masked by default with placeholder representations and visual styling.
   - Click-to-reveal interactivity, search integration, match counts, and code folding operate identically to small payload masking.

3. **Lifecycle Management & Clean Cancellation**:
   - If a new response is received, the view is cleared, or the active request tab changes while background formatting is active, the running formatting task is cancelled promptly.
   - Cancelled or obsolete background tasks do not update the view or emit stale signals after cancellation.
   - Successive rapid responses do not cause race conditions, leaked resources, or thread exhaustion.

4. **Payload Size Boundary Integrity**:
   - Payloads smaller than the medium-size threshold (< 50 KB) continue their established low-latency display path.
   - Payloads exceeding the large-document threshold (> 100 KB) continue their established bypass path, rendering raw content without interactive span overhead.
   - Payloads in the 50 KB – 100 KB range reliably utilize non-blocking background formatting.

5. **Error & Fallback Resilience**:
   - If payload parsing, token discovery, or formatting encounters malformed data or unexpected errors in the background worker, the system safely falls back to displaying the raw response text without crashing or hanging the interface.

6. **Automated Verification**:
   - Automated tests under `tests/` verify:
     - Non-blocking execution behavior and completion signal propagation.
     - Exact equivalence of masked output and token spans between background and direct formatting.
     - Cancellation of in-flight formatting when replaced by subsequent responses or cleared.
     - Graceful handling of malformed JSON and error conditions.
   - All tests declare required timeout markers per `do-testing` and `lsr-python`.

7. **Quality Standards Compliance**:
   - All repository checks (`make lint`, `make typecheck`, `make test`, `make verify-ai-tasks`) pass cleanly without errors or regressions.

## Task Description

### Problem Statement

In PyPost, sensitive response fields are masked in the desktop GUI using `ResponseMaskController` and formatted via `JsonMaskFormatter`. This identifies sensitive tokens matching user-defined selectors, replaces their text with masked placeholders (`"***"`), and records exact character spans for interactive click-to-reveal.

For small payloads (< 50 KB), this process finishes in milliseconds, well within a single UI frame (16.6 ms for 60 FPS). For very large payloads exceeding 100 KB (`LARGE_DOC_CHAR_THRESHOLD`), the application automatically bypasses pretty-printing and interactive token tracking to protect the interface from heavy rendering loads.

However, medium-sized payloads between 50 KB and 100 KB represent a critical performance gap:
- They are small enough to be viewed with interactive masking, but large enough (often hundreds or thousands of JSON lines and keys) that AST parsing, string allocation, and token position indexing take tens of milliseconds.
- Running this workload directly on the main user interface thread causes noticeable frame drops, stuttering animations, delayed mouse clicks, and perceived sluggishness.

To resolve this, the workload must be performed in the background away from the main user interface thread, delivering the completed formatting and token coordinates back to the UI when ready.

### Scope

- **In Scope**:
  - Offloading JSON response formatting and sensitive token coordinate calculation for payloads between 50 KB and 100 KB to background worker execution.
  - Coordinating lifecycle events: dispatching formatting, updating the UI upon completion, and cancelling obsolete in-flight tasks upon view reset or new response arrival.
  - Ensuring consistent visual affordances, click-to-reveal toggling, and search integration for completed background formatting.
  - Adding automated tests covering asynchronous formatting workflows, cancellation, and edge cases.

- **Out of Scope**:
  - Modifying the core selector matching engine (`JsonSelectorEngine`) or selector grammar.
  - Changing MCP server tool response sanitization (`McpResponseSanitizer`), which already executes in a headless process.
  - Altering the large-document threshold policy (> 100 KB bypass).
  - Redesigning unrelated UI components or non-JSON response handlers.

### Constraints and Assumptions

- **Main Thread UI Ownership**: In desktop GUI frameworks, all widget tree mutations, document edits, and cursor updates must occur exclusively on the main UI thread. Background workers must calculate data and coordinates off-thread, returning results for main-thread application.
- **Raw Data Immutability**: The underlying in-memory response data (`ResponseData`) and request history must remain immutable and unredacted.
- **Zero Memory Leaks**: Background worker threads and tasks must be deterministically cleaned up when finished or cancelled, preventing zombie threads or resource accumulation over long application sessions.
- **Hermetic Automated Testing**: Tests must execute reliably in CI environments without depending on live network connections or timing-sensitive sleep delays.
- **Repository Tooling Compliance**: All development, linting, and test execution must follow `AGENTS.md` and use `make` targets.

### Business Entities & Relationships

```
+-------------------------------------------------------+
|                 Response Viewer                        |
|  - Displays response status, headers, and body         |
|  - Coordinates active presentation state              |
+-------------------------------------------------------+
                           |
                           | 1 requests formatting
                           v
+-------------------------------------------------------+
|             Background Formatting Session             |
|  - Manages active off-thread formatting task           |
|  - Handles cancellation of stale tasks                |
|  - Delivers ready results to main UI thread           |
+-------------------------------------------------------+
                           |
                           | 1 performs work on
                           v
+-------------------------------------------------------+
|               Masking Presentation Data               |
|  - Formatted text with masked placeholders            |
|  - Token coordinate spans for click-to-reveal         |
|  - Selector match state and fallback flags            |
+-------------------------------------------------------+
```

## Q&A

- **Q: Why is the 50 KB to 100 KB range specifically selected?**
  - **A**: Empirical profiling demonstrates that payloads below 50 KB format in under 5 ms on standard processors, which is well within the 16.6 ms frame budget for 60 FPS and does not create noticeable user interface lag. Payloads above 100 KB already bypass interactive token masking due to document rendering constraints. The 50 KB to 100 KB range is where synchronous formatting causes perceptible UI stutter on modest workstations.

- **Q: Will the user experience any visual difference in how masked fields look or behave?**
  - **A**: No. The visual presentation (masked placeholders, underlines, tooltips) and interaction (click to toggle between masked and unmasked values) remain completely identical. The improvement is purely responsive: the application window remains fluid, responsive to clicks, and smooth while the payload is processed.

- **Q: What happens if the user runs another request while a medium-sized response is being formatted?**
  - **A**: The running background formatting task is cancelled immediately. When the new response arrives, a fresh formatting session begins for the new response. The obsolete task's results are discarded and will never overwrite the active display.

- **Q: What happens if the response payload has malformed JSON syntax?**
  - **A**: If background parsing encounters invalid JSON, the system catches the condition and immediately delivers the raw text to the view, ensuring the user always sees the raw response without error dialogs or application hangs.

- **Q: Does this affect MCP tools or CLI operations?**
  - **A**: No. MCP tools and CLI operations run in headless environments without a graphical user interface event loop; this enhancement is focused strictly on the desktop GUI response viewer.
