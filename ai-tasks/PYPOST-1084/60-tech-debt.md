# Technical Debt Analysis: PYPOST-1084

## Resolved Debt

- **D6 / F8 from PYPOST-1071**: `McpServerSettingsController._collection_by_id` duck-typing fallback probing `collections_provider()` with `getattr` has been removed and replaced with direct injection of `collection_lookup: Callable[[str], Collection | None]`.

## New Debt Introduced

- **None**: The refactoring strictly reduces complexity and removes dead fallback code.

## Follow-up Tasks

- Pre-existing findings remain tracked under their respective Jira issues (PYPOST-1085, PYPOST-1087, PYPOST-1090, PYPOST-1091, PYPOST-1088, PYPOST-1110, PYPOST-1111).
