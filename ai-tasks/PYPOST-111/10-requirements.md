# PYPOST-111: Async JSON check on paste for large data volumes

## Goals

Users pasting large JSON into the request body editor should get formatted (or YAML-converted)
content without freezing the UI. PYPOST-109 skipped parse/format above 100KB to avoid lag; this
task restores formatting for large valid JSON while keeping the editor responsive.

## User Stories

- As an API developer, when I paste a large valid JSON payload, I want it inserted immediately
  and pretty-printed shortly after without blocking the editor.
- As an API developer with **YAML as JSON** enabled, I want large pasted JSON to become YAML in
  the background the same way small pastes do today.
- As an API developer, when I paste large non-JSON text, I want immediate insert with no extra
  work or errors.

## Definition of Done

- Paste above 100KB that looks like JSON (`{` or `[` after leading whitespace) inserts raw text
  on the UI thread, then formats asynchronously when `json.loads` succeeds.
- Paste above 100KB that does not look like JSON uses default insert only (no background worker).
- Edits to the pasted region before async completion leave user text unchanged.
- Small pastes (≤100KB) keep synchronous behaviour from PYPOST-109/515.
- Automated tests cover large JSON async format and large JSON→YAML async conversion.
- Developer docs describe async large-paste behaviour.

## Task Description

Follow-up from PYPOST-12 / PYPOST-109 technical debt. Move JSON parse and format for oversized
pastes off the main thread while preserving immediate clipboard insertion.

## Q&A

- **Q:** Should invalid large JSON be formatted? **A:** No — raw text remains after background
  parse fails.
- **Q:** Cancel in-flight format on a new paste? **A:** Yes — only the latest paste generation
  may replace editor text.
