# PYPOST-1195: Fix WebsocketDraftObservability caplog assertions

## Goals

Restore confidence in the automated suite for blank WebSocket draft tab
persistence observability. Developers and CI must trust that
`TestWebsocketDraftObservability` correctly verifies that draft connection
ids are omitted from persisted open-tabs state and that saved WebSocket ids
are retained — without false failures from outdated log substring checks.

This debt was filed during PYPOST-1192 as a pre-existing NON-BLOCKER so the
suite gate can stay green after observability event names drifted.

## User Stories

- As a developer running `make test`, I need the WebsocketDraftObservability
  cases to pass when draft omit and saved-id persist logging still work, so
  I am not blocked by stale assertions.
- As a maintainer of WebSocket draft lifecycle observability, I need test
  expectations aligned with the emitted log event names and fields so
  regressions in omit/persist behavior remain detectable.
- As a sprint owner clearing Suite Failures Cleanup debt, I need these two
  node ids green without changing sibling tickets (FILE_CAPS, port-busy).

## Definition of Done

- `tests/test_tabs_presenter.py::TestWebsocketDraftObservability::test_save_tabs_state_logs_omitted_websocket_draft_id` passes under `make test`.
- `tests/test_tabs_presenter.py::TestWebsocketDraftObservability::test_save_tabs_state_logs_persisted_saved_websocket_id` passes under `make test`.
- Assertions still prove: draft id omitted from open-tabs persistence path;
  saved WebSocket id persisted; filter summary counts match the scenario;
  no sensitive URL/header payload leakage in those log lines.
- Developer-facing log event catalog (if it still names the old filter event)
  matches what the code emits.
- Sibling Suite Failures Cleanup items remain out of scope and untouched.
- Top-down artifacts for this task are complete and the issue can close.

## Task Description

### Problem

Two caplog assertions in `TestWebsocketDraftObservability` fail with
`assert any(...) is False`. Runtime logs emit the current filter summary
event and per-id omit/persist events, but the tests still look for outdated
substrings (notably a filter event name that no longer matches production).

Confirmed pre-existing at base commit `18a4d9d1` during PYPOST-1192.

### Functional requirements

1. When a blank WebSocket draft tab is opened and open-tabs state is saved,
   observability must record that the draft connection id was omitted, and
   tests must accept the current emit format for that fact and for the
   aggregate filter summary counts.
2. When a collection-backed (saved) WebSocket tab is open and state is saved,
   observability must record that the saved connection id was persisted, and
   tests must accept the current emit format for that fact and aggregate
   counts.
3. Negative checks that those log lines do not include URL or header
   payload material remain in force.
4. No change to product omit/persist rules is required unless production
   behavior itself is wrong relative to draft lifecycle docs; the primary
   defect is assertion drift.

### Non-functional requirements

- Fix must be covered by the existing targeted `make test` invocation.
- Changes stay minimal and local to the failing observability contract
  (tests and any mismatched event catalog docs).
- Do not alter FILE_CAPS, MCP port-busy, or other sibling failure areas.

### Constraints and assumptions

- Programming language: **Python**.
- Issue type: Debt; Medium; 2 story points.
- Sibling tickets out of scope: PYPOST-1194, PYPOST-1196; PYPOST-1181/1193
  already done.
- Repro command:
  `make test PYTEST_ARGS="tests/test_tabs_presenter.py -k WebsocketDraftObservability"`.

### Main entities (business)

- **WebSocket draft tab** — unsaved connection profile opened in the UI;
  must not be written into persisted open-tabs id list.
- **Saved WebSocket tab** — collection-backed connection; may appear in
  persisted open-tabs ids.
- **Open-tabs persistence observability** — INFO log events that record
  omit/persist decisions and aggregate filter counts without leaking
  connection URLs or headers.
- **Automated WebsocketDraftObservability suite** — regression net that
  asserts those events for draft-omit and saved-persist scenarios.

## Q&A

| Question | Answer |
| -------- | ------ |
| Why fix tests rather than revert log names? | Jira and PYPOST-1192 triage treat assertions as out of sync with current structured event names; production emit is the intended contract. |
| Is product omit/persist behavior in scope? | Only if green tests cannot be achieved without correcting a real behavioral bug; default scope is assertion (and docs) alignment. |
| Are other WebsocketDraftObservability tests in scope? | Only if they share the same stale filter-event substring; dirty-close cases that already pass stay untouched unless broken by this change. |
