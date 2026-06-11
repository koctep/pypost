# PYPOST-510: Body edit area should have line numbers

## Goals

The request Body tab is the primary place where users author structured payloads (JSON today;
YAML/XML planned within the "Request Body Editor" sprint). Without line numbers, users cannot
quickly locate a specific position in the payload: validation errors, API error responses, and
teammate feedback commonly reference line numbers, but the editor gives no visual anchor to find
them. Displaying line numbers alongside the body text makes payload editing, debugging, and
communication about payload content faster and less error-prone, and it lays the groundwork for
upcoming sprint features that point users at exact lines (validation errors, collapsible
structured data).

## User Stories

- As an API user editing a request body, I want to see line numbers next to the text so I can
  quickly locate a specific line in a long payload.
- As an API user whose payload is rejected by a server or validator, I want to find the line
  referenced in the error message so I can fix the problem without counting lines manually.
- As a user collaborating with teammates, I want to refer to body content by line number so we can
  discuss payloads unambiguously.
- As a user editing or scrolling through a large body, I want line numbers to stay aligned with
  their lines at all times so the gutter remains trustworthy.

## Definition of Done

- The Body tab edit area displays a line-number gutter alongside the text content.
- Line numbers start at 1 and increase by one per line of text.
- Line numbers stay correct and aligned while typing, pasting, deleting, scrolling, and resizing.
- The gutter is visually distinct from the editable text area and is not editable itself.
- Line numbers do not interfere with existing Body tab behavior: JSON syntax highlighting,
  auto-indentation, paste auto-formatting, variable hover tooltips, and placeholder text.
- The gutter width adapts to the number of digits needed (e.g. 9 → 10 lines, 99 → 100 lines)
  so numbers are never clipped.
- Automated tests cover line-number display and its behavior on content changes.

## Task Description

The Body tab in the request editor uses a plain-text code editor widget with JSON highlighting,
auto-indent, and variable awareness, but it renders no line numbers. Users editing multi-line
payloads have no way to identify a line position visually. This task adds a line-number display
alongside the body text content.

This task is part of the "Request Body Editor" sprint, which also covers a format selector
(JSON/YAML/XML), YAML-as-JSON conversion, validation errors, and collapsible structured data.
Those sibling features are out of scope here, but line numbering should not preclude them
(validation errors will likely reference the lines this task makes visible).

### In Scope

- A line-number gutter in the Body tab edit area of the request editor.
- Correct numbering across all editing operations (typing, paste, delete, undo/redo).
- Correct alignment during scrolling and window resizing.
- Gutter sizing that adapts to the line count.
- Tests for the line-number behavior.

### Out of Scope

- Format selector, YAML/XML support, validation errors, and collapsible data (separate sprint
  tasks).
- Line numbers in other editors (Script tab, response view) — may be considered later.
- Current-line highlighting, clickable gutter actions (breakpoints, folding markers).
- A user setting to toggle line numbers on/off.
- Word-wrap interaction (the body editor uses no line wrapping today).

## Functional Requirements

- The body edit area must display a line number for each line of the body text.
- Numbering must start at 1 and reflect the actual number of lines in the document, including a
  single "1" for an empty body.
- Line numbers must update immediately when lines are added or removed by any editing operation.
- Line numbers must remain vertically aligned with their corresponding lines while scrolling.
- The gutter must be read-only; clicking or typing in it must not modify the body text.
- The gutter must not obscure body text, the placeholder hint, or variable hover tooltips.
- Existing editing behavior (auto-indent, bracket dedent, JSON paste formatting, syntax
  highlighting) must be unaffected.

## Non-functional Requirements

- **Usability**: numbers must be legible and visually separated from the text content; styling
  must fit the existing application look.
- **Performance**: editing and scrolling must remain smooth for large bodies (thousands of
  lines); line numbering must not introduce perceptible input lag.
- **Maintainability**: the solution must not block the planned sprint features (validation error
  line references, collapsible structured data).
- **Compatibility**: behavior must be consistent across supported desktop platforms.

## Constraints and Assumptions

- The application is a Python 3.10+ desktop app; implementation language is Python.
- The Body tab editor remains a plain-text editing surface; this task only adds a visual
  line-number display, not editor replacement.
- No user-configurable toggle is required; line numbers are always shown in the body editor.
- Project markdown and 100-character line length rules apply to artifacts.

## Main Entities and Interactions

- **Request body**: multi-line text payload the user edits in the Body tab.
- **Body editor**: the editing surface in the request editor's Body tab where the payload is
  typed, pasted, and displayed.
- **Line-number gutter**: read-only visual column showing one number per body line, kept in sync
  with the body content and scroll position.
- **User**: edits the body and uses line numbers to locate, fix, and discuss payload content.

Interaction overview:

1. User opens a request and switches to the Body tab.
2. The editor shows the body text with a line-number gutter on the side.
3. As the user types, pastes, or deletes content, the gutter updates to match the line count.
4. As the user scrolls, the numbers stay aligned with their lines.
5. When an external message (e.g. a server error) references a line, the user finds it by its
   number in the gutter.

## Q&A

- Q: Why are line numbers needed in the body editor (business reason)?
  A: Users debugging payloads and reading validation/server errors need to locate content by line;
  without a gutter they must count lines manually, which is slow and error-prone. The sprint's
  upcoming validation-error feature will reference lines, making the gutter a prerequisite for a
  coherent editing experience.
- Q: Should line numbers be toggleable in settings?
  A: No. They are always on in the body editor; a toggle can be added later if users ask for it.
- Q: Should the Script tab or response view get line numbers too?
  A: Out of scope. Tech-debt note `doc/dev/tech-debt/PYPOST-10.md` already tracks the Script tab
  editor's limitations; reuse there can be a follow-up.
- Q: Does numbering count wrapped visual rows or logical lines?
  A: Logical lines. The body editor does not wrap lines, so the distinction is currently moot.
