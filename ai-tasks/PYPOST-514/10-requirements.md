# PYPOST-514: Add checkbox "YAML as JSON" to convert body to JSON before sending

## Goals

Many HTTP APIs accept only JSON request bodies, while users often prefer authoring payloads in
YAML because it is more readable and less verbose. With the body format selector (PYPOST-513),
users can edit YAML in the Body tab, but the outgoing request still sends the body as raw YAML
text unless they manually rewrite it as JSON. That mismatch forces extra work and leads to failed
requests against JSON-only endpoints.

This task adds an optional "YAML as JSON" control so users can keep editing in YAML while the
application sends the equivalent JSON payload when they run the request. It completes the
"Request Body Editor" sprint capability for YAML authoring with JSON delivery.

## User Stories

- As an API user who writes request bodies in YAML, I want to send JSON to endpoints that expect
  JSON so I do not have to maintain two representations of the same payload.
- As an API user, I want a clear on/off choice for YAML-to-JSON conversion so I can send raw YAML
  when an endpoint accepts YAML or plain text.
- As an API user who saves a request, I want my YAML-as-JSON preference to persist so reopening the
  request restores my choice.
- As an API user with JSON or XML selected as the body format, I want the YAML-as-JSON option to
  have no effect on send so my request behaves predictably.
- As an API user whose YAML cannot be converted, I want clear feedback when I try to send so I can
  fix the body before the request goes out.
- As an API user editing the body, I want the text in the editor to stay in YAML after send so I
  can continue editing the same representation.

## Definition of Done

- The Body tab shows a "YAML as JSON" checkbox (or equivalent labeled control).
- When the checkbox is enabled and the body format is YAML, sending the request delivers the body
  as JSON derived from the YAML content in the editor.
- When the checkbox is disabled, send behavior is unchanged from today for all body formats.
- When the body format is not YAML, the checkbox does not alter the outgoing request.
- The checkbox state is stored on the request and restored when loading a saved request or tab
  state.
- Default state is unchecked for new requests and for requests that have no saved preference.
- The editor body text is not replaced with JSON on send; only the outgoing request uses the
  converted form when conversion applies.
- Invalid YAML with conversion enabled surfaces a user-visible error instead of sending a
  misleading payload.
- Existing Body tab behavior (format selector, folding, validation, line numbers, save, variable
  hover) is unchanged aside from the new control and send-time conversion.
- Automated tests cover checkbox persistence, send behavior when enabled/disabled with YAML format,
  and no effect when format is not YAML.

## Task Description

The request Body tab supports JSON, YAML, and XML via the format selector. YAML bodies are
currently sent as raw text. Users who target JSON APIs must either switch the format to JSON and
retype the payload or use external tools to convert YAML first.

This task adds an explicit opt-in to convert YAML body content to JSON at send time. The user
continues to view and edit YAML in the editor; conversion applies only to the outgoing HTTP
request when both the checkbox is on and the format is YAML.

### In Scope

- "YAML as JSON" checkbox on the Body tab.
- Send-time conversion from YAML to JSON when the option is enabled and format is YAML.
- Persist and restore the checkbox state on the request.
- User-visible error when conversion is requested but the YAML body is not convertible.
- Tests for persistence and send behavior.

### Out of Scope

- Converting pasted JSON to YAML in the editor (PYPOST-515).
- Changing body text in the editor on send or on checkbox toggle.
- Conversion when body format is JSON or XML.
- Blocking send on validation errors unrelated to conversion (existing behavior).
- YAML/XML folding or validation implementations (PYPOST-518, PYPOST-519).

## Q&A

- Q: Why add conversion at send instead of requiring users to pick JSON format?
  A: Users want YAML editing ergonomics (readability, less punctuation) while still hitting APIs
  that only accept JSON. Forcing JSON format removes YAML editor benefits.
- Q: When does conversion apply?
  A: Only when the body format is YAML and the "YAML as JSON" checkbox is enabled.
- Q: What happens to the text shown in the editor after send?
  A: It remains YAML. Conversion affects the outgoing request only, not the saved or displayed
  body text.
- Q: What if the YAML body is invalid when conversion is enabled?
  A: The user sees an error explaining that the body could not be converted; the request is not
  sent with a silently wrong payload.
- Q: How does this relate to PYPOST-515?
  A: PYPOST-515 handles paste-time JSON→YAML display when the checkbox is on. This task covers
  send-time YAML→JSON only.
