# Requirements: PYPOST-1190

## Task Metadata

- **Issue**: PYPOST-1190
- **Title**: [PYPOST-1158] Wire unsaved HTTP tab close to Discard/Keep prompt
- **Language**: Python
- **Type**: Debt / Feature Completion
- **Source**: `ai-tasks/PYPOST-1158/60-tech-debt.md` (item 6)

## Problem Statement

When closing tabs in `TabsPresenter`, WebSocket draft tabs prompt with a Discard / Keep dialog via `prompt_unsaved_draft_tab_close` when dirty. Unsaved HTTP request tabs previously closed without any prompt even if the user had unsaved changes, because blank HTTP tabs have `persisted_baseline is None` and lacked a dirty-state definition against factory defaults.

## Functional Requirements

- **FR-1**: Factory HTTP Draft Definition
  - Provide `factory_request_draft()` and `request_draft_fields_equal()` in `pypost.core.request_persisted_fields` comparing persisted editor fields (`name`, `url`, `method`, `headers`, `params`, `body`, `body_type`, `yaml_as_json`, `post_script`, `expose_as_mcp`, `mcp_description`, `mcp_params`, `retry_policy`).
- **FR-2**: HTTP Draft Dirty Detection
  - `is_request_draft_dirty(tab)` in `pypost.ui.presenters.tab_dirty` returns `True` when editor contents differ from `factory_request_draft()`.
  - `is_tab_dirty(tab)` delegates to `is_request_draft_dirty(tab)` when `tab.persisted_baseline is None`.
- **FR-3**: Prompt on Unsaved Dirty HTTP Tab Close
  - When closing an unsaved HTTP tab (`persisted_baseline is None` and not saved in collections) that is dirty, display `prompt_unsaved_draft_tab_close(parent, title)`.
  - If user selects "Discard", tab is closed and `request_draft_dirty_close_prompt` is logged with `choice=discard`.
  - If user selects "Keep the tab", tab remains open and `request_draft_dirty_close_prompt` is logged with `choice=keep`.
- **FR-4**: Clean and Saved HTTP Tabs Skip Prompt
  - Clean unsaved HTTP tabs (`is_request_draft_dirty` is `False`) close directly without prompt and log `request_draft_clean_close`.
  - Collection-backed HTTP tabs (`persisted_baseline is not None` or `find_request(id) is not None`) close directly without prompt.

## Acceptance Criteria

1. Closing a dirty blank HTTP tab prompts with Discard / Keep dialog.
2. Selecting Keep keeps the HTTP tab open at its current index; selecting Discard closes the tab.
3. Closing a clean blank HTTP tab closes immediately without prompt.
4. Closing a collection-backed HTTP tab closes immediately without prompt.
5. All test suites pass cleanly.
