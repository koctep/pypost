# PYPOST-512: Text area should show errors in data according to the format

## Goals

When users edit structured request bodies (JSON, YAML, XML), invalid syntax is easy to miss until
a request fails or a downstream tool rejects the payload. Users need immediate, in-editor feedback
that points to where the body does not match the active format so they can fix syntax without
leaving the Body tab or guessing from a generic send error.

This task is part of the "Request Body Editor" sprint alongside line numbers (PYPOST-510, done),
collapsible sections (PYPOST-511, done), format selection (PYPOST-513, pending), and YAML-as-JSON
conversion.

## User Stories

- As an API user editing a JSON body, I want to see when my content is invalid JSON and where the
  problem is so I can fix syntax before sending the request.
- As an API user who introduced a typo while typing, I want validation to update as I edit so I
  know when the body becomes valid again.
- As an API user working with plain unstructured text, I do not want format validation noise when
  the body is not meant to be structured data.
- As an API user who relies on line numbers, I want error locations to refer to the same line
  numbers shown in the gutter so I can find the problem quickly.
- As an API user who will later choose YAML or XML as the body format, I expect validation to
  follow the selected format once that selector exists.

## Definition of Done

- The Body tab edit area validates content against the active body format and surfaces errors
  inline while the user edits.
- For JSON (the default format today), invalid syntax shows at least the error line and a human-
  readable message describing the problem.
- Valid JSON (including empty or whitespace-only body) shows no validation error.
- Validation updates after edits without requiring an explicit "validate" action.
- Error display does not alter body text: save, switch tabs, and send use the complete underlying
  content.
- Validation does not break existing Body tab behavior: line numbers, JSON syntax highlighting,
  folding, auto-indentation, paste auto-formatting, variable hover tooltips, and placeholder text.
- When the active format is plain text, no format validation errors are shown.
- Architecture supports plugging in YAML and XML validators when those formats are active
  (PYPOST-513); JSON validation is fully implemented now.
- Automated tests cover JSON validation error detection, line/column reporting, and editor display
  for at least one invalid and one valid case.

## Task Description

The Body tab uses a code-style editor for multi-line payloads. Users already see line numbers,
JSON highlighting, and collapsible sections for valid JSON, but invalid JSON is only hinted by
missing fold chevrons — there is no explicit error indication or message.

This task adds format-aware validation with inline error feedback. JSON is the implicit default
format until PYPOST-513 adds a format selector; YAML and XML validators may be stubbed but must
share the same extension point.

## Q&A

- Q: Why validate in the editor instead of only on send?
  A: Early feedback reduces failed requests and speeds editing; users fix syntax at the source.
- Q: How does this relate to folding (PYPOST-511)?
  A: Sibling feature. Invalid documents may show validation errors and no fold chevrons; both use
  logical document line numbers.
- Q: Is a format selector required before validation works?
  A: No for JSON-only usage today. Default format is JSON; PYPOST-513 will call `set_body_format()`
  later.
- Q: Should validation block sending the request?
  A: Out of scope — this task focuses on inline display; send behavior is unchanged.
- Q: What about multiple errors in one document?
  A: Show the first parse error (standard library behavior for JSON); multi-error reporting is a
  possible follow-up.
