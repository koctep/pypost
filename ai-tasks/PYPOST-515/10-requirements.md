# PYPOST-515: Paste JSON into YAML body when "YAML as JSON" is enabled

## Goals

PYPOST-514 lets users author YAML bodies that are sent as JSON when **YAML as JSON** is checked.
Users often copy JSON from API docs, browser devtools, or other tools. Pasting that JSON into a
YAML editor forces manual reformatting. This task closes that gap so paste matches the user's
chosen authoring mode.

## User Stories

- As an API developer with **YAML as JSON** enabled, I want pasted JSON to appear as YAML in the
  body editor so I can keep editing in YAML without manual conversion.
- As an API developer with **YAML as JSON** disabled, I want pasted JSON to stay formatted as JSON
  (existing behavior) so JSON-first workflows are unchanged.
- As an API developer on a non-YAML body format, I want paste behavior unchanged regardless of the
  checkbox state.

## Definition of Done

- When body format is YAML and **YAML as JSON** is checked, pasting valid JSON inserts YAML text.
- When **YAML as JSON** is unchecked or format is not YAML, JSON paste keeps existing pretty-print
  behavior.
- Non-JSON paste is unchanged (plain text inserted as-is).
- Converter and paste paths have automated tests.
- Dev docs describe paste-time conversion alongside send-time conversion.

## Task Description

PYPOST-514 added the checkbox and send-time YAML→JSON conversion. `CodeEditor` already intercepts
paste via `insertFromMimeData` and pretty-prints JSON. This task wires that hook to convert
JSON→YAML when the editor is in YAML mode and `yaml_as_json` is enabled, reusing the shared
`yaml_as_json` flag on `RequestData`.

## Q&A

- **Q:** Should invalid JSON paste be converted?
  **A:** No — fall back to default paste (same as today for non-JSON).
- **Q:** Does paste affect send behavior?
  **A:** No — paste only changes editor content; send-time conversion remains as in PYPOST-514.
