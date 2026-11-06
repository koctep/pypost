# PYPOST-1342: Observability

## Analysis

Enum/items enforcement sits on the existing MCP argument validation path
(`validate_mcp_argument_values` → `McpArgumentValidationError`). Type mismatches already
raise without logging raw values; enum/items follow the same contract. Schema emission is
pure data transformation with no I/O.

## Logging

- **No new INFO/WARNING events** for successful schema build or valid calls (noise).
- **UI:** invalid Enum/Items cell JSON already logs at DEBUG via
  `mcp_param_json_field_coerce_failed` / `mcp_param_json_field_type_mismatch` without
  treating the cell as a secret beyond normal debug practice (editor-local metadata).
- **Runtime:** rejection messages stay value-safe (parameter name + expected-type label
  only). Call sites that already translate `McpArgumentValidationError` into MCP tool
  errors continue to apply.

## Metrics

- **No new Prometheus labels or counters.** Param-name labels would raise cardinality;
  MCP metrics remain method-scoped per prior PYPOST-1038 decision. Failures remain visible
  in the MCP activity / error path as invalid arguments.

## Validation

- Unit tests assert illegal enum/item values raise `McpArgumentValidationError` and that
  the raw value string is absent from the message.
