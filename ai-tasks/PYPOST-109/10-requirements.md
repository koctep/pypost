# PYPOST-109: Avoid UI lag when pasting very large text into the body editor

## Goals

Pasting content into the request body editor should remain responsive. When users paste very large
text, the editor currently attempts to parse it as JSON on the main UI thread, which can freeze
the interface. This task removes that lag for oversized pastes while keeping existing paste
formatting for typical payload sizes.

## User Stories

- As an API developer, when I paste a very large body (for example a big log or payload), I want
  the editor to insert the text immediately without freezing so I can keep working.
- As an API developer, when I paste normal-sized JSON, I want the existing pretty-print and
  JSON→YAML paste behaviour unchanged.

## Definition of Done

- Paste of text larger than the agreed size threshold skips JSON parse/format and uses default
  insert (raw clipboard text).
- Paste at or below the threshold keeps current JSON formatting and YAML-as-JSON conversion.
- Automated tests cover large valid JSON and large non-JSON passthrough.
- Developer docs describe the large-paste behaviour.

## Task Description

Follow-up from PYPOST-12 technical debt: `CodeEditor.insertFromMimeData` calls `json.loads` on
every text paste. For very large clipboard content this blocks the UI thread. Mitigate by
bounding when paste-time JSON handling runs; optional async handling remains out of scope
(PYPOST-111).

## Q&A

- **Q:** What counts as "very large"? **A:** 100KB of pasted text, consistent with other large-body
  thresholds in the app (response search).
- **Q:** Should large valid JSON still be pretty-printed? **A:** No — skip formatting to avoid lag;
  users can reformat manually if needed.
- **Q:** Async parse for large JSON? **A:** Deferred to PYPOST-111.
