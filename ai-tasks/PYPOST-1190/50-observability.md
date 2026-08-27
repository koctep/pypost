# Observability: PYPOST-1190

## Logging & Metrics

- Added structured INFO log events in `tabs_presenter_draft.py`:
  - `request_draft_clean_close request_id=<id>`: emitted when an unsaved, unmodified HTTP draft tab is closed without a prompt.
  - `request_draft_dirty_close_prompt request_id=<id> choice=<keep|discard>`: emitted when a modified HTTP draft tab prompts the user and records the user's choice.
- No sensitive URL or header data is logged.
- Verified by automated tests in `tests/test_tabs_presenter.py::TestWebsocketDraftObservability`.
