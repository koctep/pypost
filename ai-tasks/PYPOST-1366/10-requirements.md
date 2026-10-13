# PYPOST-1366: JSON/YAML/XML code folding in WebSocket stream view

## Programming Language

Python

## Goals

WebSocket streams frequently transmit complex, structured message payloads (JSON, YAML, or XML)
spanning dozens, hundreds, or thousands of lines. When users inspect incoming or outgoing messages
in the WebSocket stream inspection view, reading and analyzing such payloads in an uncollapsible
view creates significant visual noise, requires continuous scrolling, and makes isolating nested
fields or structures cumbersome.

Adding structured code folding to the WebSocket stream view payload inspection area empowers users
to collapse and expand objects, arrays, and elements on demand. This substantially improves
inspection productivity and navigational clarity when working with real-time streaming data,
while preserving all critical stream inspection capabilities—including live stream reception,
message searching and filtering, follow-tail, line wrapping, hex inspection mode, and text
copying—without performance or usability degradation.

## User Stories

- As a developer inspecting WebSocket messages, I want structured JSON, YAML, and XML payloads to
  display collapsible code blocks so that I can fold irrelevant data and focus on nested fields of
  interest.
- As a developer inspecting a structured WebSocket message, I want clear visual gutter indicators
  and double-click actions so that I can easily toggle block folding directly in the detail view.
- As a developer analyzing a complex message payload, I want "Fold All" and "Unfold All" actions so
  that I can quickly collapse the entire hierarchy or restore full visibility with a single action.
- As a developer monitoring an active WebSocket stream, I want message streaming, follow-tail,
  filtering, and text search to continue operating smoothly without degradation or interruption
  when code folding is enabled.
- As a developer examining varied message formats, I want the viewer to seamlessly detect
  structured formats (JSON, YAML, XML) and support toggling between line-wrapped, unwrapped, and hex
  display modes without corrupting payload state.
- As a maintainer, I want comprehensive automated test coverage for code folding in the WebSocket
  stream view to guarantee stability and prevent regressions across future releases.

## Definition of Done

- [ ] WebSocket stream payload inspection pane supports folding and unfolding structured blocks for
      JSON, YAML, and XML payloads.
- [ ] Format detection automatically identifies JSON, YAML, and XML payloads, while leaving plain
      text, binary, or non-structured frames unaffected.
- [ ] Gutter indicators visually depict fold state (collapsed vs. expanded) and respond to user
      clicks or double-clicks to toggle folding of the corresponding block.
- [ ] Document-level "Fold All" and "Unfold All" actions are accessible in the stream detail
      inspection interface.
- [ ] Streaming of incoming messages, follow-tail behavior, stream filtering, and search navigation
      operate cleanly without degradation or UI stalls.
- [ ] Existing viewer actions—including word wrap toggle, hex mode toggle, copy button, set
      variable button, and text selection—continue to function seamlessly.
- [ ] Code folding is purely visual and non-destructive: folded blocks remain part of the underlying
      payload and are fully preserved when copying text, toggling modes, or exporting transcripts.
- [ ] Automated tests cover format detection, fold/unfold toggles, bulk folding actions, line
      wrapping compatibility, search interaction, and non-structured frame handling.
- [ ] All repository quality checks pass (`make check`).

## Task Description

The WebSocket stream view provides real-time monitoring and inspection of WebSocket messages.
Within the view, a message detail inspection pane displays the payload of the currently selected
stream message entry.

Currently, the detail inspection pane displays text payloads inside a standard text viewer without
line numbering, gutter indicators, or block folding. For large JSON payloads (or YAML/XML messages),
developers must scroll extensively to inspect message contents. In contrast, HTTP response viewing
and the request body viewer offer rich code folding with gutter indicators and bulk fold/unfold
operations.

This task enhances the WebSocket stream payload viewer by introducing block folding for JSON, YAML,
and XML frames, providing gutter fold indicators, double-click folding, and "Fold All" / "Unfold
All" controls, while maintaining full compatibility with stream buffering, search, line wrapping,
and export workflows.

### Scope (In)

- Folding and unfolding of structured blocks in JSON, YAML, and XML WebSocket payloads within the
  stream detail inspection pane.
- Gutter fold indicators displaying collapse/expand state for structured blocks.
- Interaction controls: gutter indicator clicks, double-click block folding, and bulk "Fold All" /
  "Unfold All" actions.
- Automatic payload format detection (JSON, YAML, XML, plain text, or binary).
- Seamless interoperation with existing stream features:
  - Live message streaming and stream buffer updates.
  - Follow-tail and pause/resume states.
  - Directional, kind, and text search filtering.
  - Word wrap toggling and hexadecimal view mode switching.
  - Payload copy, variable assignment, and transcript export.
- Automated test coverage validating folding interactions, bulk actions, and mode transitions.
- Verification through `make check`.

### Scope (Out)

- Modifying the list/table virtualization and filtering model of the message stream itself
  (folding applies to the detail payload pane, not the message list rows).
- Persisting folded/unfolded block states across selections of different stream messages.
- Allowing in-place editing of WebSocket message payloads (the stream inspector remains strictly
  read-only).
- Adding custom folding grammars for arbitrary unsupported non-structured formats (e.g., CSV, SQL).

## Assumptions and Constraints

- **Read-Only Inspection**: WebSocket stream payloads are historical records of network
  transmissions; folding must preserve read-only integrity and never allow payload modification.
- **Data Fidelity**: Collapsing or expanding blocks must never mutate, truncate, or alter the
  underlying message content. Copying, exporting, or setting variables from the payload must always
  reflect authentic message data.
- **Performance Under Streaming**: High-throughput message streaming or selection updates must not
  experience UI lag, stutter, or memory leaks due to fold scanning or gutter painting.
- **Line Wrap Compatibility**: Toggling word wrap on and off must preserve fold state and layout
  geometry without visual clipping or gutter misalignment.
- **Make-Only Tooling**: All test executions, static analysis, and validation must be executed
  exclusively via `make` targets (`make check`, `make test`, `make lint`).
- **Documentation Standards**: Lines in all documentation and task artifacts must not exceed 100
  characters.

## Main Entities and Interactions

- **Stream Inspector**:
  - *Attributes*: Message list, toolbar, filter controls, search bar, detail splitter.
  - *Business Role*: Manages the overall WebSocket monitoring view, message feed, and inspector
    layout.
- **Message Detail Inspection Pane**:
  - *Attributes*: Selected entry metadata, action toolbar (Copy, Set Var, Wrap, Hex, Fold All,
    Unfold All), code viewing component.
  - *Business Role*: Displays and formats the selected message's payload for in-depth inspection.
- **Stream Message Entry**:
  - *Attributes*: Timestamp, direction (in/out), frame opcode/kind, payload content, size.
  - *Business Role*: Represents a single recorded WebSocket message or lifecycle event.
- **Code Viewing Component**:
  - *Attributes*: Gutter area, folding controller, syntax format, text document.
  - *Business Role*: Renders code lines with line numbers and interactive fold indicators.
- **Folding Controller**:
  - *Attributes*: Fold regions list, collapsed states, block boundaries.
  - *Business Role*: Computes collapsible block hierarchies and controls block visibility.
- **Format Detector**:
  - *Attributes*: Payload syntax analysis, detected format type (JSON, YAML, XML, PLAIN).
  - *Business Role*: Identifies the message payload format to activate appropriate fold rules.

### Interaction Flow

1. User selects a message from the WebSocket message list, or an incoming message arrives while
   following the tail.
2. The message detail inspection pane receives the stream message entry and detects the payload
   format (JSON, YAML, XML, or plain/binary).
3. If a structured format is detected:
   - Folding indicators appear in the gutter alongside line numbers.
   - User can click or double-click gutter indicators to collapse or expand individual blocks.
   - User can trigger "Fold All" or "Unfold All" to manipulate the entire payload view.
4. If a non-structured or binary payload is displayed (or Hex mode is active), folding controls
   remain inactive and text displays normally.
5. User can toggle word wrap, search within the stream, copy text, or export transcripts without
   interference from fold states.

## Non-Functional Requirements

- **Usability**: Visual fold indicators in the gutter must clearly communicate block boundaries and
  current state (expanded vs. collapsed).
- **Performance**: Payload formatting and fold scanning must execute quickly (< 50 ms for typical
  frames) without freezing the UI or delaying message streaming.
- **Robustness**: Invalid, truncated, or malformed JSON/YAML/XML payloads must gracefully fall back
  to standard plain text display without raising exceptions or breaking the detail view.
- **Consistency**: The user experience, gutter appearance, and keyboard/mouse interaction models
  must remain consistent with existing code folding in the HTTP response view.

## Q&A

**Q: Why is code folding needed in the WebSocket stream view?**  
**A:** WebSocket messages often carry large JSON or XML data structures. Code folding allows
developers to collapse verbose nested objects and inspect critical fields without endless
scrolling.

**Q: Does folding affect incoming message streaming or follow-tail behavior?**  
**A:** No. Folding applies to the detail inspection pane of the selected message. Incoming stream
processing, message logging, and follow-tail scrolling continue unaffected.

**Q: How does folding interact with word wrapping and Hex mode?**  
**A:** Toggling word wrapping dynamically reflows text while maintaining block collapse states. When
Hex mode is enabled, folding affordances are temporarily disabled since raw hex representations do
not follow structured code block hierarchies.

**Q: What happens if a WebSocket payload is malformed or not JSON/YAML/XML?**  
**A:** The payload is treated as plain text; no folding regions or chevrons are displayed, and the
content is presented normally without error.
