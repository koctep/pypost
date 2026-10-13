# PYPOST-1365: JSON/YAML/XML code folding in ResponseView

## Programming Language

Python

## Goals

API responses frequently contain extensive, deeply-nested structured payloads (JSON, YAML, or XML)
spanning hundreds or thousands of lines. Inspecting such responses in `ResponseView` currently
requires tedious continuous scrolling, making it difficult for users to grasp overall data
hierarchies, isolate specific keys or nested collections, or compare sibling branches.

Adding code folding to `ResponseView` empowers users to collapse and expand structured blocks on
demand. This substantially improves readability and navigational efficiency when analyzing large
responses without altering the underlying response content or degrading essential viewing
features (such as search, text copying, context menus, and syntax highlighting).

## User Stories

- As an API developer inspecting a deeply nested response, I want to collapse objects, arrays, and
  nested elements so that I can focus on relevant sections without excessive scrolling.
- As an API developer inspecting a structured response, I want clear visual gutter indicators and
  double-click actions so that I can easily toggle block folding.
- As an API developer reviewing a large response document, I want "Fold All" and "Unfold All"
  actions so that I can quickly collapse the entire document structure or restore full visibility.
- As an API developer searching response content, I want text search (Ctrl+F) and match navigation
  to continue working reliably regardless of whether sections are folded or unfolded.
- As an API developer reviewing varied responses, I want PyPost to automatically detect JSON, YAML,
  and XML formats while leaving unstructured or plain-text responses unaffected.
- As a maintainer, I want comprehensive automated test coverage for response folding so that
  regressions in response inspection and view actions are prevented.

## Definition of Done

- [ ] `ResponseView` supports folding and unfolding structured blocks for JSON, YAML, and XML
      payloads.
- [ ] Format detection automatically determines whether the response body is JSON, YAML, XML, or
      plain/unstructured text based on response headers (`Content-Type`) or payload structure.
- [ ] Non-structured and plain-text response formats remain completely unaffected, displaying
      without folding affordances or errors.
- [ ] Gutter indicators visually depict fold state (collapsed vs. expanded) and respond to
      user clicks / double-clicks to toggle folding of the corresponding block.
- [ ] Convenient bulk folding actions ("Fold All" and "Unfold All") are available to collapse and
      expand all foldable regions across the response document.
- [ ] Existing view features—including Ctrl+F text search, navigation between matches, context
      menu actions, text selection, clipboard copy, and syntax highlighting—continue to work
      seamlessly without regressions.
- [ ] Code folding is non-destructive: folding hides blocks from view without modifying, truncating,
      or mutating the underlying response text.
- [ ] Automated test suite covers format detection, block folding and unfolding, bulk actions,
      interaction with search/copy, and non-structured payload handling.
- [ ] `make check` passes cleanly.

## Task Description

PyPost's response inspection view (`ResponseView`) currently displays the response body in a
read-only text area. While request payloads authored in the Body tab support code folding for
structured data (JSON/YAML/XML), response payloads lack code folding capabilities. As responses are
frequently larger and more deeply nested than requests, lack of code folding creates significant
navigation friction.

This task introduces code folding to `ResponseView` for JSON, YAML, and XML response bodies,
incorporating gutter folding indicators, double-click folding, bulk "Fold All" / "Unfold All"
capabilities, and automatic format detection based on `Content-Type` headers or body payload
structure.

### Scope (In)

- Folding and unfolding of nested blocks in structured JSON, YAML, and XML response payloads.
- Gutter folding indicators reflecting fold status (collapsed vs. expanded).
- User interaction affordances: gutter indicator click / double-click folding.
- Document-level "Fold All" and "Unfold All" actions.
- Automatic payload format recognition (via `Content-Type` header inspection or payload structure
  detection fallback).
- Graceful handling of non-structured formats (plain text, HTML, raw binary/unrecognized) without
  folding controls or presentation anomalies.
- Full preservation and seamless interoperation of existing `ResponseView` capabilities:
  - Search (Ctrl+F), match indexing, match counting, and Next/Previous navigation.
  - Context menu actions (Copy, Select All, Set Variable).
  - Syntax highlighting.
  - Status metadata (Status code, Time, Size).
- Comprehensive automated test coverage and quality gate verification (`make check`).

### Scope (Out)

- Modifying the request Body tab folding behavior or introducing format conversion to responses.
- Persisting response fold state across application restarts or tab switches.
- In-place editing of response content (response view remains strictly read-only).
- Folding arbitrary non-structured text or custom unsupported formats (e.g. CSV, GraphQL, Protobuf).

## Assumptions and Constraints

- **Read-Only Semantics**: `ResponseView` is an inspection panel; folding must never enable editing
  or alter the immutable response body.
- **Underlying Text Preservation**: Folding alters view visibility only; operations reading text
  (such as clipboard copy, search scans, and variable extractions) access the authentic response
  body data.
- **Format Detection Reliability**: When response `Content-Type` headers are absent or generic
  (e.g., `text/plain` or `application/octet-stream`), format detection gracefully examines body
  payload structure to determine if JSON, YAML, or XML folding applies.
- **Performance & Responsiveness**: Large response bodies (e.g., exceeding 100 KB) must not stall
  or crash the user interface during format detection, folding scans, or fold toggling.
- **Make-Only Tooling**: All test executions, linting, and quality verification must be conducted
  strictly via `make` targets (`make check`, `make test`, `make lint`).
- **Documentation Standards**: Lines in all documentation and task artifacts must not exceed 100
  characters.

## Main Entities and Interactions

- **Response View (`ResponseView`)**:
  - *Attributes*: Status bar, search bar, structured body viewer, gutter area.
  - *Business Role*: Presents HTTP response status, execution metadata, and payload content to
    the user.
- **Response Data (`ResponseData`)**:
  - *Attributes*: Status code, response headers (including `Content-Type`), elapsed time, size,
    and body content.
  - *Business Role*: Encapsulates the execution result received from the HTTP client.
- **Fold Region (`FoldRegion`)**:
  - *Attributes*: Region identifier, start line/block, end line/block, collapse state.
  - *Business Role*: Represents a collapsible logical block (object, array, element) within the
    structured document.
- **Format Detector**:
  - *Attributes*: Header inspect rules, payload structure heuristics, detected format type.
  - *Business Role*: Determines the active structured format (JSON, YAML, XML, or None) for
    incoming response data.
- **Fold Actions**:
  - *Attributes*: Toggle fold, Fold All, Unfold All.
  - *Business Role*: User interactions allowing immediate expansion or collapsing of regions.

### Interaction Flow

1. User sends an HTTP request; response data arrives containing headers and body.
2. `ResponseView` receives `ResponseData` and determines the content format using `Content-Type`
   or body inspection.
3. If JSON, YAML, or XML is detected, structure folding is initialized for the document:
   - Gutter displays folding indicators for nestable blocks.
   - User can click/double-click indicators to fold or unfold specific blocks.
   - User can trigger "Fold All" or "Unfold All" to manipulate the entire document.
4. If non-structured text is received, folding controls remain inactive and content displays
   normally.
5. User can search (Ctrl+F) and copy text seamlessly regardless of current fold state.

## Non-Functional Requirements

- **Usability**: Fold indicators in the gutter must clearly communicate block boundaries and
  current state (expanded vs. collapsed).
- **Performance**: Folding scans and expand/collapse transitions must be responsive, even on large
  payloads exceeding 100 KB.
- **Non-Destructive Integrity**: Text selections, copy actions, and variable assignments must
  consistently capture actual payload text rather than omitting folded lines or altering data.
- **Robustness**: Ill-formed payloads or format detection mismatches must fail gracefully without
  raising uncaught exceptions or blanking the response display.

## Q&A

**Q: Why is code folding needed in ResponseView?**  
**A:** Real-world API responses frequently span thousands of lines with deep nesting. Code folding
allows users to collapse irrelevant blocks and inspect target data efficiently without overwhelming
visual clutter.

**Q: How is format detection performed for responses?**  
**A:** Primarily via the response `Content-Type` header (e.g., `application/json`,
`application/xml`, `application/x-yaml`, `text/xml`). When headers are absent, ambiguous, or
generic, payload structure heuristics detect valid JSON, YAML, or XML syntax.

**Q: What happens if a response body is invalid or malformed JSON/YAML/XML?**  
**A:** If structure parsing fails, no folding regions are presented and the payload is displayed as
plain text without errors or broken folding affordances.

**Q: How does code folding interact with text search (Ctrl+F)?**  
**A:** Search operates across the full document text. Matching within folded regions must remain
functional and accessible (e.g., finding occurrences and navigating to them without concealing
matches).

**Q: Are "Fold All" and "Unfold All" bulk operations required?**  
**A:** Yes, bulk operations allow users to immediately view top-level structure or restore the
complete document view without toggling each block individually.
