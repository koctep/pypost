# PYPOST-513: Add data type selector (JSON/YAML/XML) for body tab

## Goals

Users editing request bodies need to declare whether the payload is JSON, YAML, or XML so the
editor can apply the right structure tools (folding, validation) and the HTTP client can send the
body correctly. Today the Body tab assumes JSON implicitly; YAML and XML bodies get JSON-oriented
behavior, which is misleading and limits format-specific features built in PYPOST-511 and
PYPOST-512.

This task adds an explicit format choice on the Body tab as part of the "Request Body Editor"
sprint.

## User Stories

- As an API user editing a YAML body, I want to select YAML as the format so the editor treats
  my content as YAML rather than JSON.
- As an API user editing an XML body, I want to select XML so I can use format-specific editor
  features when they become available.
- As an API user who saves a request, I want the chosen body format to persist so reopening the
  request restores my format choice.
- As an API user switching format, I want folding and validation to follow the selected format
  without changing my body text.
- As an API user sending a request, I want JSON bodies to be serialized as JSON and other formats
  sent as raw data, consistent with existing send behavior.

## Definition of Done

- The Body tab shows a selector for JSON, YAML, and XML.
- Changing the selector updates the active body format in the code editor (folding and validation
  registries).
- The selected format is stored on the request (`body_type`) and restored when loading a saved
  request or tab state.
- Default format is JSON for new requests and for requests with unknown legacy `body_type` values.
- Existing Body tab behavior (line numbers, highlighting, send, save, variable hover) is unchanged
  aside from format-driven folding/validation.
- Automated tests cover selector wiring, persistence through `get_request_data_from_ui`, and
  `set_body_format` invocation on the editor.

## Task Description

The Body tab uses `CodeEditor` with folding (PYPOST-511) and validation (PYPOST-512). Both
features expose `set_body_format(BodyFormat)` but nothing in the UI sets the format yet. Users
cannot choose YAML or XML even though the model field `RequestData.body_type` exists.

This task adds the format selector UI and connects it to the editor and request model.

### In Scope

- JSON / YAML / XML selector on the Body tab.
- Wire selector to `CodeEditor.set_body_format()`.
- Load and save `RequestData.body_type`.
- Tests for selector behavior and persistence.

### Out of Scope

- Full YAML/XML folding and validation implementations (PYPOST-518, PYPOST-519).
- YAML-as-JSON conversion checkbox (PYPOST-514, PYPOST-515).
- Format-specific syntax highlighters beyond existing JSON highlighter.
- Plain-text body format in the selector.
- Blocking send on validation errors.

## Q&A

- Q: Why only JSON, YAML, XML in the selector?
  A: These are the structured formats supported by the body editor sprint; plain text remains
  out of scope for this selector.
- Q: How does this relate to `body_type` on send?
  A: `body_type` already controls JSON serialization in `http_client`; the selector writes the
  same field (`json`, `yaml`, `xml`).
- Q: What happens for legacy `body_type="text"` requests?
  A: The selector defaults to JSON for display and editor behavior; saving updates `body_type`
  to the user's explicit choice.
