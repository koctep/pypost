# PYPOST-1089: Validate McpToolParam.default Type and Add Editable Default Column to McpParamsTable

## Goals

Following the introduction of optional MCP tool parameter defaults in PYPOST-1054, two architectural gaps were documented in tech debt:
1. `McpToolParam` does not validate that a declared `default` matches the declared `type` (e.g. `type="boolean"` with `default="fifty"` previously constructed without error).
2. `McpParamsTable` in the request editor has no visible or editable "Default" column; it preserved defaults in an internal dict keyed by parameter name, meaning renaming a parameter silently dropped its default on `get_data()`.

This task aims to:
1. Enforce strict type validation in `McpToolParam` so that non-None defaults must be type-compatible with the declared `type`.
2. Add a 5th "Default" column to `McpParamsTable` in the request editor, allowing users to view and edit default values.
3. Ensure default values persist and survive parameter renaming in `McpParamsTable`.

## User Stories

- **As an API Author / Collection Designer**, I want invalid defaults (such as a string default on an integer param) to fail validation immediately at model instantiation so that malformed configurations cannot reach runtime MCP servers.
- **As a User in the Request Editor**, I want to see and edit the default value for optional MCP tool parameters in a dedicated table column, and I want that default value preserved even if I rename the parameter.

## Definition of Done

1. **`McpToolParam` Default Type Validation**:
   - `string`: default must be `str`.
   - `integer`: default must be `int` (and not `bool`).
   - `number`: default must be `int` or `float` (and not `bool`).
   - `boolean`: default must be `bool`.
   - `integer_or_string`: default must be `int` or `str` (and not `bool`).
   - `array`: default must be `list`.
   - `object`: default must be `dict`.
   - `None` is permitted for all types.
   - Incompatible defaults raise `ValueError` at construction time.
   - **Note**: `number_or_string` is **not** a declared MCP param type in the codebase
     (`_MCP_PARAM_TYPES` in `pypost/models/models.py`). It was listed here in error and
     is excluded from the validation scope.
2. **`McpParamsTable` 5th Column (Default)**:
   - Header labels: `["Name", "Type", "Description", "Required", "Default"]`.
   - Populated from `spec.default` during `set_data()`.
   - Read and parsed into typed values during `get_data()`.
   - Renaming a parameter's Name cell preserves its Default value in `get_data()`.
3. **Automated Testing**:
   - Unit tests verify valid and invalid default types for all supported MCP param types.
   - UI unit tests verify `McpParamsTable` display, editing, and rename survival.
4. **Code Quality**:
   - `make lint` passes. All tests pass with explicit timeout markers.

## Task Description

- **Problem**: Lack of type cross-checks on `McpToolParam.default` permits invalid schema configurations, and `McpParamsTable` lacks an editable Default column, silently dropping defaults when parameter names are modified in the UI.
- **Business Objective**: Prevent invalid MCP tool defaults and provide a full-featured UI for viewing and editing parameter defaults.
- **Constraints**: Maintain backward compatibility with existing collection files and test fixtures.

## Q&A

- **Q: How should structured types (array/object) or booleans be represented in the table cell?**
  - A: Booleans as `"true"`/`"false"`, numbers/strings directly as text, arrays and objects serialized as JSON strings.
