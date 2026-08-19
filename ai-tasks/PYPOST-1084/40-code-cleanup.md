# Code Cleanup: PYPOST-1084

## Overview

Audited all files modified in PYPOST-1084 for dead code, formatting, typing, and style compliance.

## Checks Performed

1. **Flake8 / Style**:
   - `make lint` passes cleanly (flake8, markdown lint, link check).
   - Fixed extraneous blank lines in `pypost/ui/mcp_server_controller.py`.

2. **Dead Code & Unused Attributes**:
   - Removed `self._collections_provider` and `self._get_collections` assignments from `__init__`.
   - Removed private method `_collection_by_id` and its `getattr` probing / fallback loop.
   - Removed unused imports or parameters across modified call sites.

3. **Type Annotations**:
   - `collection_lookup: Callable[[str], Collection | None]` is explicitly typed in `McpServerSettingsController.__init__`.
   - All parameters in `for_window` factory and test doubles conform to the signature.

4. **Targeted Tests**:
   - `tests/test_mcp_server_controller.py` and `tests/test_main_window.py` (22 passed).
