# Technical Debt Analysis: PYPOST-1189

## Debt Assessment

- **Scope Completed**: All test gaps identified in item 5 of `ai-tasks/PYPOST-1158/60-tech-debt.md` have been locked with automated tests in `tests/test_tabs_presenter.py`.
- **Remaining Follow-ups**:
  - `PYPOST-1190`: Wire unsaved HTTP tab close to Discard/Keep prompt.
  - `PYPOST-1191`: Reuse one `WebSocketRegistry` per `save_tabs_state`/`close_tab`.
  - `PYPOST-1161`: Save / `persisted_baseline` for WebSocket tabs.
