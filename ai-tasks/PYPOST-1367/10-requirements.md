# PYPOST-1367: JSON/YAML/XML code folding in MCP result view

## Programming Language

Python

## Goals

Model Context Protocol (MCP) tool execution results frequently contain deeply nested structured
payloads (such as JSON data, configuration snippets in YAML, or XML responses) spanning hundreds
or thousands of lines. Currently, the MCP tool execution result inspection pane
presents content in a plain, uncollapsible text view. Reviewing large or complex tool responses
requires repetitive scrolling, obscuring payload hierarchy and making it tedious to inspect or
compare nested data blocks.

Introducing code folding for structured formats (JSON, YAML, and XML) directly in the MCP result
view empowers users to collapse and expand nested objects, lists, and elements on demand. This
significantly improves readability, hierarchy comprehension, and navigational efficiency while
preserving existing result inspection capabilities—including elapsed execution time display, error
indicators, content sanitization, plain text rendering, and clipboard actions.

## User Stories

- As a user executing MCP tools, I want structured JSON, YAML, and XML results to feature
  collapsible code blocks so that I can fold irrelevant data and focus on nested fields of
  interest without overwhelming visual clutter.
- As a user inspecting structured MCP tool outputs, I want clear visual gutter indicators and
  double-click actions so that I can easily toggle block folding directly in the result view.
- As a user analyzing extensive MCP outputs, I want convenient "Fold All" and "Unfold All" actions
  so that I can quickly collapse the entire hierarchy or restore full visibility in a single step.
- As a user executing varied MCP tools, I want plain text responses or non-structured outputs to
  continue displaying cleanly as before without visual anomalies or unwanted folding controls.
- As a user inspecting tool execution errors or diagnostic notices, I want error details and
  execution status to remain prominent and unaffected by folding mechanics.
- As a maintainer, I want comprehensive automated test coverage for MCP result folding to ensure
  reliable behavior and prevent regressions across future changes.

## Definition of Done

- [ ] MCP result view supports interactive folding and unfolding of structured blocks for JSON,
      YAML, and XML payloads.
- [ ] Visual gutter indicators reflect the fold state (collapsed vs. expanded) of structured
      blocks.
- [ ] Gutter indicators respond to user clicks and double-clicks to toggle folding of the target
      block.
- [ ] Bulk "Fold All" and "Unfold All" actions are accessible in the MCP result view interface to
      collapse and expand all foldable blocks across the document.
- [ ] Non-structured and plain text MCP tool outputs render normally without folding indicators or
      functional regressions.
- [ ] Execution metadata (such as elapsed time, in-progress notices, and error indicators) continues
      to display reliably alongside result payloads.
- [ ] Code folding is non-destructive and purely visual: underlying result text is fully preserved
      for copying and downstream inspection.
- [ ] Automated tests cover format handling, fold/unfold toggles, bulk actions, and non-structured
      rendering.
- [ ] Quality gate checks pass cleanly via `make check`.

## Task Description

The MCP client view enables users to discover and execute MCP server tools and inspect call results.
Execution outputs—including text blocks, structured content, and execution error payloads—are
presented inside the MCP result view.

Currently, this pane renders results using a basic read-only text viewer without line numbers,
gutter indicators, or block collapse affordances. When an MCP tool returns comprehensive JSON data,
structured configurations, or XML trees, navigating the output requires continuous scrolling.
Other inspection panes across the application (such as the HTTP response viewer and WebSocket
stream inspector) already offer structured block folding with gutter chevrons, double-click toggles,
and bulk folding controls.

This task extends structured code folding to the MCP result view for JSON, YAML, and XML content,
providing gutter fold indicators, double-click folding, and "Fold All" / "Unfold All" controls,
while preserving plain text presentation for unstructured responses.

### Scope (In)

- Folding and unfolding of structured blocks in JSON, YAML, and XML payloads within the MCP result
  view.
- Gutter fold indicators displaying collapse and expand states for structured blocks.
- User interaction controls: gutter click and double-click block folding.
- Document-level "Fold All" and "Unfold All" bulk actions in the result view.
- Automatic structured format detection (JSON, YAML, XML, or plain text) for MCP tool output
  payloads.
- Preservation of existing result view functionality:
  - Progress and in-flight status indicators.
  - Elapsed execution time presentation.
  - Call tool error notices and structured error payloads.
  - Sensitive text sanitization and content block aggregation.
  - Text selection and clipboard copying.
- Automated test coverage validating folding interactions, bulk actions, and format handling.
- Verification through `make check`.

### Scope (Out)

- Modifying MCP tool invocation logic, server transport handling, or parameter schema forms.
- Persisting folded or unfolded block states across different tool executions or tab switches.
- Editing MCP tool result payloads (the result view remains strictly read-only).
- Adding custom folding grammars for arbitrary unstructured formats (such as CSV or log streams).

## Assumptions and Constraints

- **Read-Only Inspection**: MCP tool outputs represent recorded execution results; code folding
  must maintain read-only semantics and never allow modifying output content.
- **Data Integrity**: Collapsing or expanding blocks must never mutate, truncate, or alter the
  underlying result text. Clipboard copying or external inspections must access the complete
  payload.
- **Unstructured Compatibility**: Plain text responses, multi-block mixed content, and
  non-structured strings must render cleanly without broken folding affordances or errors.
- **Performance**: Formatting and fold scanning must execute promptly without freezing the user
  interface or delaying execution result display.
- **Make-Only Tooling**: All test executions, static analysis, and quality validations must be
  executed exclusively via `make` targets (`make check`, `make test`, `make lint`).
- **Documentation Standards**: Lines in all documentation and task artifacts must not exceed 100
  characters.

## Main Entities and Interactions

- **MCP Result View**:
  - *Attributes*: Result header, progress indicator, elapsed time label, result code viewer,
    bulk fold actions.
  - *Business Role*: Presents tool execution progress, timing metadata, errors, and payload content
    to the user.
- **Tool Execution Result**:
  - *Attributes*: Content blocks (text, image, audio), structured content, error flags, elapsed
    seconds.
  - *Business Role*: Encapsulates the output received from executing an MCP tool.
- **Fold Region**:
  - *Attributes*: Region identifier, start block/line, end block/line, collapsed state.
  - *Business Role*: Represents a collapsible logical unit (object, array, element) within the
    structured document.
- **Format Detector**:
  - *Attributes*: Syntax detection rules, detected format type (JSON, YAML, XML, PLAIN).
  - *Business Role*: Determines the format of the tool result content to apply appropriate folding
    rules.
- **Fold Actions**:
  - *Attributes*: Toggle fold, Fold All, Unfold All.
  - *Business Role*: User operations allowing immediate expansion or collapsing of regions.

### Interaction Flow

1. User executes an MCP tool; the result view transitions to the in-progress state.
2. The tool execution completes, delivering output payload data and elapsed execution time.
3. The MCP result view formats the payload content (incorporating errors or structured blocks) and
   detects whether the content is JSON, YAML, XML, or plain text.
4. If a structured format is detected:
   - Folding indicators appear in the gutter alongside line numbers.
   - User can click or double-click gutter indicators to collapse or expand individual blocks.
   - User can trigger "Fold All" or "Unfold All" to manipulate the entire result document.
5. If non-structured or plain text content is displayed:
   - Folding controls remain inactive and content displays normally as plain text.
6. User can inspect, select, and copy result text without interference from folding states.

## Non-Functional Requirements

- **Usability**: Visual fold indicators in the gutter must clearly communicate block boundaries and
  current state (expanded vs. collapsed).
- **Performance**: Formatting and fold scanning must execute smoothly without noticeable latency,
  even on substantial tool output payloads.
- **Robustness**: Malformed or partial JSON/YAML/XML payloads must gracefully fall back to standard
  plain text presentation without throwing unhandled exceptions.
- **Consistency**: Gutter visual appearance and user interaction behavior must align with code
  folding in the HTTP response view and WebSocket stream view.

## Q&A

**Q: Why is code folding needed in the MCP result view?**  
**A:** MCP tool results often return verbose, deeply-nested JSON or structured records. Code folding
allows users to collapse unneeded blocks and inspect target sections without endless scrolling.

**Q: How does the view distinguish between structured and unstructured responses?**  
**A:** Content is analyzed by format detection logic. When valid JSON, YAML, or XML structures are
recognized, code folding is activated; otherwise, the content is rendered as plain text.

**Q: What happens if an MCP tool returns an error message or non-JSON string?**  
**A:** The error message or string is rendered as plain text without folding indicators, preserving
existing visual presentation.

**Q: How do "Fold All" and "Unfold All" actions function in the result view?**  
**A:** "Fold All" collapses all detected foldable blocks across the entire result payload, while
"Unfold All" expands every block back to its fully visible state.
