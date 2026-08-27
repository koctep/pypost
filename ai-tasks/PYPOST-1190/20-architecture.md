# Architecture: PYPOST-1190

## Overview

PYPOST-1190 extends the draft lifecycle and dirty-close prompt architecture from WebSocket and MCP Client tabs to HTTP `RequestTab` instances.

## Design Details

1. **`pypost/core/request_persisted_fields.py`**:
   - Define `_FACTORY_DRAFT_ID = "request-factory-draft"`.
   - Implement `factory_request_draft() -> RequestData`.
   - Implement `request_draft_fields_equal(a: RequestData, b: RequestData) -> bool`.

2. **`pypost/ui/presenters/tab_dirty.py`**:
   - Implement `is_request_draft_dirty(tab: RequestTab) -> bool` using `tab.request_editor.get_request_data_from_ui()` and `factory_request_draft()`.
   - Update `is_tab_dirty(tab: RequestTab) -> bool` so that when `tab.persisted_baseline is None`, it returns `is_request_draft_dirty(tab)`.

3. **`pypost/ui/presenters/tabs_presenter_draft.py`**:
   - Implement `confirm_close_request_draft(parent: QWidget, tab: object, *, request_id_is_saved: Callable[[str], bool] | None = None, prompt_close: PromptClose | None = None) -> bool`.
   - Check if tab is `RequestTab`, verify if it is saved (`persisted_baseline is not None` or `request_id_is_saved(req.id)`).
   - If clean, log `request_draft_clean_close` and return `True`.
   - If dirty, invoke `closer(parent, title)` and log `request_draft_dirty_close_prompt` with choice.

4. **`pypost/ui/presenters/tabs_presenter_close.py`**:
   - In `close_workspace_tab`, invoke `confirm_close_request_draft`. If it returns `False`, abort closing immediately.

5. **`tests/test_tabs_presenter.py`**:
   - Add tests for closing dirty HTTP draft (Keep vs Discard).
   - Add tests for closing clean HTTP draft without prompt.
   - Add observability tests verifying structured log output for HTTP draft close.
