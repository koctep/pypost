# Requirements: PYPOST-1084

## Summary

Replace the `getattr` test-double fallback in `McpServerSettingsController` with direct injection of `collection_lookup: Callable[[str], Collection | None]`.

## Background & Motivation

In `McpServerSettingsController` (`pypost/ui/mcp_server_controller.py`), the private method `_collection_by_id` probed `self._collections_provider()` with `getattr(..., "collection_by_id", None)` and fell back to linear search across `self._get_collections()`. This pattern was inherited verbatim from the pre-extraction `MainWindow` implementation to accommodate test doubles that passed `collections_provider=lambda: None`.

`CollectionsPresenter` already provides a clean `collection_by_id(collection_id: str) -> Collection | None` method (`pypost/ui/presenters/collections_presenter.py:149`), and `MCPServerRegistry` expects `collection_lookup: Callable[[str], Collection | None]` directly.

By replacing `collections_provider` and `get_collections` parameters in `McpServerSettingsController.__init__` with `collection_lookup: Callable[[str], Collection | None]`, we eliminate duck-typing/probing, simplify the controller's dependency surface, and improve type safety.

## Requirements

1. **Direct Injection**:
   - `McpServerSettingsController.__init__` must accept `collection_lookup: Callable[[str], Collection | None]`.
   - Remove `collections_provider` and `get_collections` parameters from `McpServerSettingsController.__init__`.
   - Forward `collection_lookup` directly to `MCPServerRegistry`.
   - Remove `_collection_by_id` private method and unused attributes (`_collections_provider`, `_get_collections`).

2. **Factory Wiring (`for_window`)**:
   - Update `McpServerSettingsController.for_window` to pass `collection_lookup=lambda collection_id: window.collections.collection_by_id(collection_id)`.

3. **Call Sites & Test Doubles**:
   - Update `tests/test_main_window.py` test double `_make_mcp_controller` to supply `collection_lookup=lambda _id: None`.
   - Update all `McpServerSettingsController` instantiations in `tests/test_mcp_server_controller.py` to supply `collection_lookup`.
   - Replace test `test_collection_by_id_uses_presenter_and_fallback` with a test verifying `collection_lookup` is passed through to `MCPServerRegistry`.

4. **Verification**:
   - Targeted unit tests pass.
   - Flake8 / linting passes cleanly.
   - Full test suite passes (modulo pre-existing known flakiness).
