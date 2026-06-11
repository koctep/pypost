# PYPOST-511: Data in text area should be collapsible for supported formats JSON/YAML/XML

## Goals

The request Body tab is where users author structured payloads. Deeply nested JSON, YAML, and XML
bodies can span hundreds of lines, making it hard to see the overall shape of the document or to
focus on one section while editing. Users must scroll past large blocks of nested content they are
not working on, which slows editing, increases mistakes, and makes payloads harder to review
before sending.

Collapsible sections let users hide nested content they do not need at the moment and reveal it
again when they do. This improves navigation and readability of large structured bodies without
changing the underlying payload text. The feature is part of the "Request Body Editor" sprint,
alongside line numbers (PYPOST-510, done), format selection, validation errors, and YAML-as-JSON
conversion.

## User Stories

- As an API user editing a large JSON body, I want to collapse nested objects and arrays so I can
  focus on the section I am changing without scrolling through unrelated content.
- As an API user reviewing a YAML or XML payload, I want to collapse nested blocks at any depth
  so I can scan the top-level structure quickly.
- As an API user who collapsed a section, I want to expand it again so I can inspect or edit the
  hidden nested values.
- As an API user working with a partially invalid body, I want collapse to be available only where
  the structure is recognizable so I am not misled by folding over broken syntax.
- As an API user who relies on line numbers, I want collapsed and expanded views to remain
  understandable so I can still orient myself in the document.

## Definition of Done

- The Body tab edit area supports collapsing and expanding nested sections when the body content
  is valid structured data in JSON, YAML, or XML.
- Users can collapse a nested section; its descendant lines are hidden from view but remain part
  of the body text (not deleted).
- Users can expand a previously collapsed section and see the full nested content again.
- Collapse and expand work at multiple nesting levels (objects/maps, arrays/lists, and equivalent
  XML element groupings).
- Collapsed sections are visually distinguishable from expanded ones (e.g. an indicator that
  content is hidden and how to reveal it).
- Collapsing and expanding do not corrupt the body text: saving, switching tabs, and sending the
  request use the complete underlying content regardless of what is currently hidden on screen.
- Collapse behavior does not break existing Body tab behavior: line numbers, JSON syntax
  highlighting, auto-indentation, paste auto-formatting, variable hover tooltips, and placeholder
  text.
- When content is not valid for the active format, or is plain unstructured text, the editor
  behaves as today with no collapse controls (or no effective collapse regions).
- Automated tests cover collapse/expand behavior for at least one supported format and verify
  that hidden content is preserved in the stored body text.

## Task Description

The Body tab uses a code-style editor for multi-line payloads. Users can already see line numbers
(PYPOST-510) and JSON-oriented editing aids, but every line of a deep structure is always visible.
There is no way to temporarily hide nested blocks to reduce visual clutter.

This task adds collapsible/expandable sections for structured bodies in JSON, YAML, and XML. The
editor should recognize nestable regions in valid content and let the user hide or show them on
demand.

### In Scope

- Collapse and expand controls for nested sections in valid JSON, YAML, and XML body content.
- Hiding descendant lines when a section is collapsed; restoring them on expand.
- Visual indication of collapsed vs expanded sections.
- Preservation of full body text through collapse state changes, save, and send.
- Compatibility with the existing Body tab editor and line-number gutter (PYPOST-510).
- Tests for collapse/expand and content preservation.

### Out of Scope

- Format selector UI and format-driven validation (PYPOST-513, PYPOST-512) — separate tasks;
  collapse must coexist with them but their implementation is not part of this task.
- YAML-as-JSON checkbox and paste conversion (PYPOST-514, PYPOST-515).
- Collapse for non-structured or free-form body text.
- Persisting collapse state across application restarts or when reopening a saved request (collapse
  state may be session-only; bodies reload fully expanded unless decided otherwise in
  architecture).
- "Collapse all" / "Expand all" bulk actions.
- Collapse in other editors (Script tab, response view).
- Changing how the body is formatted on send (e.g. minifying collapsed sections).

## Functional Requirements

- The body edit area must offer a way to collapse nested sections when the content is valid
  structured data in JSON, YAML, or XML.
- Collapsing a section must hide all lines belonging to that section and its nested descendants
  from the visible editor view.
- Expanding a collapsed section must restore visibility of the hidden lines unchanged.
- Collapse regions must be determinable from the document structure (matching open/close boundaries
  for the active format), not from arbitrary line selections.
- The complete body text, including lines hidden by collapse, must remain available for
  `toPlainText`-equivalent retrieval, save, and request send.
- Collapse and expand must not remove, reorder, or alter characters in the underlying body text.
- When content cannot be parsed as valid structured data for the applicable format, collapse
  controls must not misrepresent structure (no folding over unrecognized or broken regions).
- Existing editing operations (typing, paste, delete, undo/redo) must remain usable; collapse
  state must not block normal text editing.
- Line numbers (PYPOST-510) must remain usable: numbering and alignment should stay coherent with
  visible lines during collapse and expand (exact presentation of numbers for hidden lines is an
  architecture detail; users must not lose orientation).
- JSON syntax highlighting, auto-indent, bracket-aware enter/dedent, JSON paste formatting,
  variable hover tooltips, and MCP placeholder behavior must continue to work.

## Non-functional Requirements

- **Usability**: collapse/expand affordances must be discoverable and consistent across JSON, YAML,
  and XML; collapsed sections must clearly signal that content is hidden.
- **Performance**: collapsing and expanding large bodies (thousands of lines) must not cause
  noticeable lag during routine editing and scrolling.
- **Reliability**: collapse state is a view concern only; the saved and sent body must always
  match the user's full textual content.
- **Maintainability**: the solution must not block planned sprint features (format selector,
  validation error display at specific lines).
- **Compatibility**: behavior must be consistent across supported desktop platforms.

## Constraints and Assumptions

- The application is a Python 3.10+ desktop app; implementation language is Python.
- The Body tab editor remains a plain-text editing surface; collapse hides lines in the view rather
  than replacing the editor with a tree widget.
- Line numbers are already shown in the body editor (PYPOST-510).
- JSON is the primary format today; YAML and XML support may depend on sibling sprint tasks, but
  collapse requirements apply equally once those formats are in use.
- Format selection may be implicit (e.g. JSON-only until PYPOST-513) or explicit later; collapse
  applies per the format the body is treated as.
- Project markdown and 100-character line length rules apply to artifacts.

## Main Entities and Interactions

- **Request body**: multi-line structured or unstructured text payload edited in the Body tab.
- **Body editor**: the editing surface where the user types, pastes, and views the payload.
- **Format**: JSON, YAML, or XML — determines how nestable sections are identified.
- **Nestable section**: a bounded block of structured content (object, array, or XML element
  subtree) that can be collapsed or expanded.
- **Collapse state**: whether a given nestable section is shown in full or with descendants hidden
  from view.
- **User**: edits the body and uses collapse to navigate and focus within large structured
  payloads.

Interaction overview:

1. User opens a request and switches to the Body tab with structured JSON, YAML, or XML content.
2. The editor shows nestable sections with a way to collapse each section.
3. User collapses a section; nested lines disappear from view but remain in the body text.
4. User expands the section when needed; hidden lines reappear unchanged.
5. User saves or sends the request; the full body text is used regardless of current collapse
   state.

## Q&A

- Q: Why is collapsible data needed in the body editor (business reason)?
  A: Large nested payloads are hard to read and edit when every line is always visible. Users
  waste time scrolling and lose context. Collapse reduces clutter so users can focus on the
  part of the payload they are changing, similar to familiar code editors.
- Q: Which formats support collapse?
  A: JSON, YAML, and XML when the content is valid structured data for that format. Invalid or
  non-structured text has no collapse regions.
- Q: Does collapsing delete or minify content?
  A: No. Hidden lines stay in the body text. Save and send always use the complete content.
- Q: Should collapse state be saved with the request?
  A: Out of scope for persistence across sessions. Bodies reload expanded unless architecture
  chooses short-lived in-memory state only for the current editing session.
- Q: How does this relate to line numbers (PYPOST-510)?
  A: Line numbers are already present. Collapse must not break the gutter; users still need
  trustworthy orientation while sections are hidden. PYPOST-510 explicitly deferred folding markers
  in the gutter to this task.
- Q: How does this relate to validation errors (PYPOST-512)?
  A: Sibling task. Collapse must not prevent future inline error display at specific lines;
  invalid documents may simply offer no collapse until parseable.
- Q: Is a format selector required before collapse works?
  A: Not necessarily for JSON-only usage today, but YAML and XML collapse apply when those formats
  are active. PYPOST-513 is a separate task; this task defines collapse behavior for all three
  supported formats.
