# Observability: PYPOST-1189

## Logging & Metrics

- No new metrics or log events were added for this test-only task.
- Existing logging in `tabs_presenter_draft.py` (`websocket_draft_clean_close`, `websocket_draft_dirty_close_prompt`, `websocket_draft_omitted_from_open_tabs`, `websocket_saved_tab_persisted_in_open_tabs`) continues to function as expected and remains validated by `TestWebsocketDraftObservability`.
