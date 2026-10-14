# PYPOST-1379: [PYPOST-1312] Interactive click-to-reveal response masking in GUI ResponseView

## Goals

When testing and debugging APIs, responses frequently include sensitive data such as authentication tokens, passwords, session cookies, API secrets, and Personally Identifiable Information (PII). When developers work in collaborative environments—such as presenting API demonstrations, sharing their screens on calls, pair programming, or working in shared spaces—displaying sensitive response attributes in plain text creates an immediate risk of confidential data leakage.

Parent Epic [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312) ("Hide selected response fields: click-to-reveal in UI, permanently masked in MCP output") addresses this security risk across both desktop GUI and AI agent integrations:
- For automated AI coding agents via MCP, values are permanently redacted to prevent ingestion into LLM context windows or persistent traces (implemented in [PYPOST-1378](https://pypost.atlassian.net/browse/PYPOST-1378) / MASK-2).
- For human developers using the desktop GUI, users require confidentiality by default while retaining the ability to selectively inspect, verify, and copy secrets as part of normal development workflows.

This task ([PYPOST-1379](https://pypost.atlassian.net/browse/PYPOST-1379), MASK-3) delivers interactive response masking for the desktop GUI `ResponseView`:
1. **Default Presentation Masking**: Automatically mask configured hidden response fields in the response viewer by default, replacing sensitive values with visual placeholder indicators.
2. **Interactive Click-to-Reveal**: Enable users to left-click directly on any masked value to instantly reveal the true value in-place, and click again to re-mask it.
3. **Seamless Subsystem Coexistence**: Ensure that masking and in-place toggling operate reliably alongside streaming response chunk appending, syntax highlighting, document search and match counting, hierarchical code folding, text selection, and context menu actions ("Set Variable", "Copy").
4. **Streaming Response Coexistence**: Ensure that in-flight chunk appending during streaming responses safely coexists without crashing or corrupting masking state, and that complete masking presentation applies cleanly when the response stream completes.
5. **Data Integrity & Performance**: Guarantee that masking is strictly a presentation-layer transformation that never corrupts or mutates raw in-memory response data, while maintaining smooth, freeze-free UI responsiveness even for large payloads.

## Programming Language

- **Implementation language**: Python (PyPost desktop GUI layer, Qt widget components, and UI test suites).

## User Stories

- As an **API Developer / Presenter**, I want configured sensitive response fields to appear masked by default when an API response is displayed, so that confidential tokens, credentials, and PII are not exposed during screen shares, video recordings, or casual observation.
- As a **Developer / Tester**, I want to click directly on any masked field in the response viewer to reveal its actual value, and click it again to toggle it back to masked, so that I can quickly inspect secrets without leaving the editor or performing cumbersome workarounds.
- As a **API Developer**, I want masked values to have an intuitive visual cue indicating that they are interactive and clickable, so that I immediately know which values can be revealed.
- As a **Developer Inspecting Streaming APIs**, I want streaming response chunks to append safely in-flight without crashing or corrupting masking state, and to see complete masking presentation applied cleanly once streaming completes, so that sensitive fields in streaming endpoints remain protected.
- As a **User Navigating Responses**, I want document search (finding text, navigating next/previous matches, and match count indicators) to work accurately whether fields are currently masked or revealed, without search index desynchronization.
- As a **Power User**, I want to select a revealed value in the response body and use the context menu to copy it or set it as an environment variable, so that my everyday debugging and variable extraction workflows remain fluid.
- As a **Developer Reading Complex Payloads**, I want JSON syntax highlighting and block code folding to remain structurally intact, visually consistent, and free of glitching or re-rendering loops when toggling values.
- As a **Desktop User**, I want the response viewer to remain completely responsive without freezing or lagging when inspecting large response payloads that exceed standard size thresholds.

## Definition of Done

This task is considered complete when:

1. **Default Masking in GUI ResponseView**:
   - When an HTTP response is displayed for a request that has configured hidden response fields, all matching fields in the response body are masked by default using a standard placeholder (`***`).
   - Non-matching fields and structure remain displayed in clear text.
2. **In-Place Click-to-Reveal and Re-Mask**:
   - Left-clicking on a masked placeholder value toggles the display to show the true, unmasked value in-place.
   - Left-clicking on a revealed value toggles it back to the masked placeholder state.
   - Toggling is scoped specifically to the clicked value and does not unintentionally toggle other masked fields.
3. **Visual Affordance**:
   - Masked and interactive values provide visual feedback (such as cursor shape change on hover or styling cues) to signify that they are clickable.
4. **Streaming Response Coexistence**:
   - During in-flight chunk appending for streaming responses, appending incoming data safely coexists without crashing or corrupting masking state.
   - When the response stream completes, complete masking presentation applies cleanly to all matching configured hidden fields.
5. **Syntax Highlighting Coexistence**:
   - Syntax highlighting remains valid and accurate for both masked and revealed states.
   - No infinite re-highlighting loops or syntax corruption occur upon toggling.
6. **Search and Match Count Coexistence**:
   - Text search, find-next, find-previous, and match counting accurately find matching text in the current presentation state without crashes or position drift.
   - Revealed values become immediately searchable as plain text upon being revealed.
7. **Code Folding & Context Menu Coexistence**:
   - Document code folding regions remain aligned and functional when fields are toggled between masked and revealed states.
   - Text selection and context menu actions ("Set Variable", "Copy", "Select All") function correctly on both masked and revealed content.
   - Selecting a revealed value and using "Set Variable" extracts the authentic secret value into the variable assignment.
8. **In-Memory Response Data Immutability**:
   - The underlying in-memory response data (`ResponseData`) and history entries are not mutated by masking or toggling operations.
9. **Large-Document Responsiveness**:
   - Response payloads exceeding the large-document threshold retain performant fallback behavior without freezing the UI thread.
10. **Comprehensive Automated Test Coverage**:
    - A complete PySide6 UI test suite verifies default masking, click-to-reveal toggling, streaming response coexistence, search coexistence, code folding stability, context menu actions, and edge cases.
11. **Quality Gates**:
    - All repository quality checks (`make lint`, `make typecheck`, `make verify-ai-tasks`, `make test`) pass cleanly.

## Task Description

### Problem Statement

During API development, responses routinely contain confidential secrets (e.g., Bearer tokens, passwords, API keys, session identifiers). In PyPost, response bodies are displayed in the desktop GUI's `ResponseView`. Previously, response bodies were rendered entirely in plain text, presenting a continuous risk of accidental disclosure during screen sharing, demos, and pairing sessions.

While [PYPOST-1377](https://pypost.atlassian.net/browse/PYPOST-1377) established the request configuration model and editor UI for declaring hidden response fields, and [PYPOST-1378](https://pypost.atlassian.net/browse/PYPOST-1378) established permanent redaction for MCP agent tools, the desktop GUI requires a dedicated presentation layer:
- Values must appear masked by default to protect user confidentiality.
- Unlike automated agents, human users need a frictionless, in-place mechanism to inspect and toggle values on demand.
- Rich document features—including regex-based syntax highlighting, incremental search, match indexing, code folding gutters, context menu actions, and streaming response handling—must coexist harmoniously with dynamic text toggling without desynchronization, visual artifacts, or UI freezes.

### Scope

- **In Scope**:
  - Masked rendering of response body fields matching the request's configured `hidden_response_fields` in GUI `ResponseView`.
  - In-place click-to-reveal and click-to-re-mask interactive toggle upon left-clicking masked values.
  - Clear visual affordance indicating clickability of masked fields.
  - Safe coexistence with streaming responses (safe in-flight chunk appending without crashing or corrupting masking state, and clean application of complete masking presentation when response stream completes).
  - Seamless coexistence with syntax highlighting (no re-highlighting loops or broken tokens).
  - Seamless coexistence with the response search bar (search input, next/prev navigation, match count reporting).
  - Seamless coexistence with code folding (preserving fold regions and indentation structure).
  - Seamless coexistence with context menu actions ("Set Variable", "Copy") on selected text.
  - Performance safeguards and fallback behavior for large response documents exceeding size thresholds.
  - In-memory response data immutability.
  - Comprehensive automated PySide6 GUI test suite covering all interaction states and edge cases.
- **Out of Scope**:
  - Request configuration model, persistence, and RequestEditor UI table (completed in **PYPOST-1377** / MASK-1).
  - MCP tool output permanent masking and agent security boundary (completed in **PYPOST-1378** / MASK-2).
  - End-to-end integration contracts spanning both GUI and MCP boundaries simultaneously (addressed in **PYPOST-1380** / MASK-4).
  - Response header masking in the GUI (the GUI currently does not render response headers).

### Functional Requirements

- **FR-1 Default Presentation Masking**:
  - When a response is loaded into the response viewer for a request with configured hidden response fields, all matching JSON body values must be rendered in a masked state by default.
  - Masked values must use the standard placeholder text (`***`).
  - Matching keys, non-sensitive sibling fields, and overall JSON structure must remain clearly visible and properly formatted.

- **FR-2 In-Place Click-to-Reveal and Re-Mask Toggle**:
  - Left-clicking on a masked value must instantly replace the placeholder with the authentic, unmasked value in-place.
  - Left-clicking on a revealed value must immediately toggle it back to the masked placeholder (`***`).
  - Toggling one field must not affect the revealed/masked state of other fields in the document.
  - Clicking on unmasked text, field keys, whitespace, or structural punctuation must not trigger reveal or toggle actions.

- **FR-3 Visual Affordance & Hover Feedback**:
  - Interactive masked values must provide immediate visual feedback (e.g. mouse hover cursor change or subtle visual styling) so users intuitively understand that the value can be clicked to toggle.

- **FR-4 Streaming Response Coexistence**:
  - During in-flight chunk appending of streaming responses, appending incoming data chunks must safely coexist with the viewer without crashing, stalling, or corrupting masking state.
  - When the response stream completes, complete masking presentation must apply cleanly to all matching configured hidden fields in the final response body.

- **FR-5 Syntax Highlighting Coexistence**:
  - Syntax highlighting must remain valid, correctly tokenized, and visually consistent across both masked and revealed states.
  - Replacing text during in-place toggling must not cause infinite syntax highlighting loops, flashing, or color corruption.

- **FR-6 Search and Navigation Coexistence**:
  - Searching for text using the search bar must operate consistently with masked values.
  - When a value is in its masked state, searching for the placeholder (`***`) or surrounding text matches normally.
  - When a value is revealed, its plain text content must become immediately findable by search.
  - Search match counts ("X of Y matches" or "Y matches") and next/previous match navigation must remain strictly synchronized without index drift after toggling values.

- **FR-7 Code Folding Coexistence**:
  - Folding regions (foldable blocks and gutter chevrons) must remain intact and functionally correct when values are toggled in place.
  - In-place value toggling on a line must not corrupt line numbering, fold boundaries, or the folded/unfolded states of surrounding blocks.

- **FR-8 Selection and Context Menu Integration**:
  - Right-clicking on selected response text must open the standard context menu ("Set Variable", "Copy", "Select All").
  - If a user selects a revealed secret value and invokes "Set Variable", the emitted action must carry the authentic, unmasked secret.
  - If a user selects text and invokes "Copy", the copied clipboard content must reflect the text as currently selected in the viewer.

- **FR-9 Large-Document Performance Fallback**:
  - If the response document exceeds the established large-document size threshold (e.g. 100 KB), the viewer must preserve performant fallback behavior.
  - The application must prioritize UI responsiveness and avoid freezing or stalling the user interface.

- **FR-10 In-Memory Response Data Immutability**:
  - Masking and toggling operations must remain strictly visual presentation transformations.
  - The underlying in-memory response model (`ResponseData`), execution results, and history records must never be modified by GUI interactions.

### Non-Functional Requirements

- **NFR-1 Responsiveness & UI Fluidity**: Toggling a masked value must execute instantaneously (< 50ms) with zero perceivable delay or screen flicker.
- **NFR-2 Usability & Discoverability**: Visual cues and interaction patterns must feel natural and predictable to users familiar with modern developer tools.
- **NFR-3 Visual Integrity**: Masked placeholders and revealed text must align cleanly with surrounding formatted code without introducing formatting glitches or misalignments.
- **NFR-4 Robustness & Fault Tolerance**: Malformed JSON, non-JSON text bodies, empty responses, and non-string scalar types (numbers, booleans, nulls) must be handled safely without unhandled exceptions or broken UI states.
- **NFR-5 Testability & Automation**: All GUI interaction scenarios (default masking, click toggle, streaming response coexistence, search, folding, context menus) must be fully verifiable via automated PySide6 QTest suites with explicit timeout markers.

## Main System Components / Business Domain

| Business Entity | Description |
| --- | --- |
| **GUI Response View** | The desktop user interface component responsible for displaying HTTP execution results, status metrics, and response body text. |
| **Hidden Field Selector** | A user-configured rule or path specifying which response fields contain confidential data that must be masked by default. |
| **Masked Response Value** | A presentation state where a sensitive value is replaced with a visual placeholder (`***`) in the response body. |
| **Revealed Response Value** | An interactive state where a sensitive value is temporarily displayed in clear text following an explicit user click. |
| **In-Place Toggle Interaction** | The direct user action (left-click) that switches an individual sensitive value between masked and revealed states without page reload. |
| **Raw Response Entity** | The authentic, unmutated HTTP response payload stored in memory and history records for auditing, post-scripts, and data consistency. |
| **Search & Navigation Subsystem** | The integrated search toolbar and match counting engine allowing users to locate and cycle through text within the response viewer. |
| **Syntax Highlighting & Code Folding** | Editor presentation engines providing token-based syntax coloring and block-level code folding for structured response formats. |
| **Streaming Response Handling** | The mechanism delivering and appending live incremental response data chunks to the response viewer before completion. |

## Q&A

- **Q: Why does the desktop GUI provide click-to-reveal, while MCP output masking is permanent?**
  - **A:** Desktop GUI users are authenticated developers working directly on their own workstations. They need to inspect secrets during local debugging, testing, and variable extraction. Masking in the GUI protects against passive visual observation (screen shares, shoulder-surfing, demos) while allowing authorized user interaction. In contrast, MCP clients are external automated AI agents where secrets must be permanently redacted to prevent ingestion into remote model contexts or logs.

- **Q: What placeholder is displayed for masked values?**
  - **A:** The standard placeholder `***`, ensuring visual consistency across both the GUI and MCP sanitization surfaces in PyPost.

- **Q: What happens if a user clicks on non-masked text or structural characters (like brackets or colons)?**
  - **A:** Nothing. Click-to-reveal is strictly scoped to the exact character spans of masked values. Clicks outside those spans behave as standard editor text cursor placement.

- **Q: Does toggling a value in the GUI mutate the response data in memory or history?**
  - **A:** No. Masking and toggling are strictly visual presentation transformations. The raw in-memory `ResponseData` and saved history records remain authentic and unmodified.

- **Q: How does response masking coexist with streaming responses?**
  - **A:** During in-flight chunk appending, incoming streaming data safely appends to the viewer without crashing, stalling, or corrupting masking state. When the stream completes, complete masking presentation cleanly applies to all matching configured hidden fields.

- **Q: What happens when a user selects a revealed secret and uses "Set Variable"?**
  - **A:** The system extracts the authentic secret value that is currently revealed and emits the variable setting request with that value, enabling seamless workflow integration.

- **Q: How does the response view behave when payloads exceed the large-document threshold?**
  - **A:** For very large payloads (exceeding 100 KB), the viewer prioritizes UI thread responsiveness, falling back to lightweight rendering without freezing or stalling the GUI.

- **Q: Are non-JSON responses (e.g. plain text or HTML) masked in the GUI?**
  - **A:** Masking targets structured response fields defined by selectors. If a response is non-JSON or malformed, it passes through gracefully without crashing the viewer, while standard editor search and display capabilities continue to operate.
