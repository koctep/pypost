# PYPOST-1376: Decompose epic PYPOST-1312 into child tasks

## Goals

Epic [PYPOST-1312](https://pypost.atlassian.net/browse/PYPOST-1312) ("Hide selected response fields: click-to-reveal in UI, permanently masked in MCP output") introduces critical data protection capabilities into PyPost. Users working with sensitive APIs (e.g. handling tokens, passwords, customer PII) need their sensitive response fields masked by default in the desktop GUI, with quick click-to-reveal inspection, while AI coding agents interacting through the Model Context Protocol (MCP) must have those same sensitive fields permanently redacted with zero reveal capability.

This task ([PYPOST-1376](https://pypost.atlassian.net/browse/PYPOST-1376)) exists to decompose parent epic PYPOST-1312 into granular, implementable, and independently verifiable child Jira tasks (each sized ≤ 5 Story Points), each scoped for a full Top-Down cycle (Steps 1–8), and assign them all to the active sprint (**Sprint 2032: Hide Selected Response Fields**).

**Business Goal:** Provide the engineering team and sprint planners with clearly bounded, low-risk, estimable work packages that together fulfill all acceptance criteria of epic PYPOST-1312 (configuration persistence, MCP permanent masking, GUI click-to-reveal, and end-to-end regression testing) without monolithic tickets blocking sprint delivery.

## Programming Language

- **This task (PYPOST-1376):** Markdown planning artifacts and Jira process management.
- **Child implementation stories under PYPOST-1312:** Python (PyPost data models, Qt GUI components, MCP server runtime, and pytest suites).

## User Stories

- As a **sprint planner**, I want epic PYPOST-1312 broken down into well-estimated child tasks (≤ 5 Story Points each) linked to the epic and added to Sprint 2032, so that work is transparently tracked and can proceed in parallel.
- As an **API developer**, I want to configure specific response fields to be hidden for any given request, so that sensitive data (such as bearer tokens or credentials) is not displayed openly in the UI during normal work or screen-sharing.
- As a **desktop user**, I want masked fields in the response viewer to be clickable to reveal their underlying values on demand, so that I can inspect actual data whenever necessary without losing syntax highlighting or search capabilities.
- As a **security-conscious administrator / user**, I want response fields configured as hidden to be permanently masked when requests are invoked as MCP tools by AI agents, with no mechanism for agents to reveal or bypass the mask.
- As a **developer implementing the epic**, I want child tasks organized by cohesive architectural boundaries (model & persistence, MCP sanitization, GUI interaction, and integration contracts) so that each task has crisp acceptance gates and testable criteria.

## Definition of Done

PYPOST-1376 is considered done when:

1. Epic PYPOST-1312 scope, technical constraints, and risk factors are thoroughly analyzed.
2. Natural, cohesive work slices are identified, each sized ≤ 5 Story Points following the Fibonacci sequence (1, 2, 3, 5).
3. Decomposition documentation is recorded in `ai-tasks/PYPOST-1312/decomposition-notes.md`.
4. Child Jira tasks are created in Jira, linked as children to parent epic `PYPOST-1312`, and added to active `Sprint 2032` (executed in Step 4).
5. All required Step 1 artifacts exist (`ai-tasks/PYPOST-1376/00-roadmap.md` and `ai-tasks/PYPOST-1376/10-requirements.md`).
6. Quality gates (`make check`) pass cleanly.

## Task Description

### Problem Statement

In modern API development, HTTP responses frequently include secrets, tokens, authentication cookies, and personally identifiable information (PII). Currently in PyPost:
- Response bodies are displayed in plain text in the GUI's `ResponseView`.
- MCP tools execute requests and return responses directly to calling AI agents without request-specific field masking (only general heuristic redaction).
- There is no mechanism in `RequestData` or collection persistence to designate specific response fields as sensitive or hidden.
- Uncontrolled exposure poses data leakage risks both visually (in desktop GUI presentations or screen-sharing) and programmatically (in MCP tool calls to AI agents).

### Scope (This Decomposition Task)

- Analyze all requirements and acceptance criteria of parent epic PYPOST-1312.
- Define 4 focused child tasks covering:
  1. Request configuration model, persistence, copy policy, and request editor UI.
  2. Permanent MCP response sanitization and output masking.
  3. Interactive click-to-reveal response viewer masking in GUI.
  4. End-to-end integration contracts, edge-case test matrix, and developer documentation.
- Formulate acceptance criteria, dependencies, deliverables, and Fibonacci story point estimates (all ≤ 5 SP) for each child task.
- Document the decomposition plan in `ai-tasks/PYPOST-1312/decomposition-notes.md`.
- In Step 4, create the corresponding Jira tickets, link them to `PYPOST-1312`, and assign them to `Sprint 2032`.

### Out of Scope (This Decomposition Task)

- Modifying PyPost production code, models, or UI widgets directly (implementation belongs in child stories MASK-1 to MASK-4).
- Altering other backlog epics or unrelated sprints.
- Adding response header display to the GUI (GUI currently does not display response headers; headers masking in GUI is deferred).

### Functional Requirements (Decomposition)

- **FR1:** The decomposition must split epic PYPOST-1312 into child stories where every story has an estimate of ≤ 5 SP.
- **FR2:** The child tasks must collectively satisfy all 5 acceptance criteria of epic PYPOST-1312:
  1. Configurable response fields to hide.
  2. Masked display with click-to-reveal in the GUI response viewer.
  3. Permanent masking in MCP tool output without any reveal mechanism.
  4. Underlying stored response data remains unaltered.
  5. Test coverage for GUI mask + click-to-reveal and MCP permanent masking.
- **FR3:** All created child Jira tasks must be associated with parent epic `PYPOST-1312` and assigned to `Sprint 2032`.

### Non-Functional Requirements

- **NFR-1 Granularity:** Story points must follow the Fibonacci scale (1, 2, 3, 5), strictly capping any single ticket at 5 SP.
- **NFR-2 Slicing Integrity:** Each child story must be independently testable and capable of executing a full Top-Down cycle (Steps 1–8).
- **NFR-3 Safety & Backward Compatibility:** Model extensions must not break existing saved collections, requests, or tab isolation semantics.
- **NFR-4 Performance & Stability:** GUI click-to-reveal masking must not degrade large-document handling, code folding, or syntax highlighting.

### Main Business Entities

| Entity | Description |
| --- | --- |
| **Request Configuration (`RequestData`)** | Persisted representation of an HTTP request, including configured hidden response fields |
| **Hidden Field Selector** | Specification (key name or path) identifying which fields in the response body must be hidden |
| **Masked Response Presentation** | Formatted display where sensitive values are replaced with a visual mask (`***`) |
| **Click-to-Reveal Interaction** | GUI user interaction allowing on-demand unmasking of specific field values in the viewer |
| **MCP Tool Response Sanitizer** | MCP boundary service enforcing permanent redaction of configured hidden fields for agents |
| **Raw Response Data (`ResponseData`)** | Unmodified response body and metadata stored in runtime memory and request history |

---

### Proposed Child Story Breakdown (under PYPOST-1312)

| Provisional ID | Jira Key | Summary | SP | Dependencies | Scope Description |
| --- | --- | --- | --- | --- | --- |
| **MASK-1** | `TBD` | Request model, persistence, and RequestEditor UI for hidden response fields | 3 | None | `RequestData` field, copy policy, collection backward compatibility, and editor UI table |
| **MASK-2** | `TBD` | Permanent MCP output masking for hidden response fields | 3 | MASK-1 | Sanitizer extension, `format_structured_tool_result` integration, permanent agent redaction |
| **MASK-3** | `TBD` | Interactive click-to-reveal response masking in GUI ResponseView | 5 | MASK-1 | Masked value rendering, click-to-reveal toggle, highlighter and search coexistence |
| **MASK-4** | `TBD` | Integration test suite, edge-case coverage, and developer documentation | 3 | MASK-1, MASK-2, MASK-3 | End-to-end contract tests, edge-case matrix, example collection fixtures, dev docs |

**Total Epic Effort:** 14 SP across 4 child stories.

---

## Q&A

**Q: Why is click-to-reveal GUI masking estimated at 5 SP while MCP masking is 3 SP?**  
A: MCP masking operates purely on structured data serialization (`format_structured_tool_result`), transforming strings or JSON dictionaries prior to output. GUI masking in `ResponseView`, by contrast, operates inside a read-only `FoldableCodeView` (`QTextEdit`) that must concurrently support `JsonHighlighter` syntax highlighting, interactive mouse clicking on specific text spans, Ctrl+F search navigation and match counting, context menu actions ("Set Variable" from selection), streaming body appending, and the large-document (>100KB) fallback path. This makes MASK-3 the highest-risk component of the epic.

**Q: Why are response headers excluded from GUI masking?**  
A: As noted in the epic description, the PyPost GUI currently does not render HTTP response headers in `ResponseView` (only status code, elapsed time, and size). Body masking addresses the user-facing GUI requirement. If response headers are added to the GUI in the future, header masking can be extended under a separate story.

**Q: When will Jira tickets be created?**  
A: Following the established Top-Down pattern (as demonstrated in PYPOST-1368 and PYPOST-1336), Step 1 defines requirements and decomposition notes. Step 2 formulates the architectural design and Jira ticket drafts. Step 4 performs the Jira issue creation, epic linking to PYPOST-1312, and assignment to Sprint 2032.
