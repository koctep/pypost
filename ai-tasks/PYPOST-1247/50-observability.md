# PYPOST-1247: Observability

`FunctionRegistry` remains a pure in-memory catalog. Registration does not perform I/O or
change external state, so adding logs or metrics would expose no useful operational signal.
Existing resolver and template-service observability remains unchanged.

## Validation

- Dynamic functions are observable through the existing `allowed_names`, `get`, and strictness
  APIs.
- No function arguments or callable details are logged.
- Focused registry tests cover registration and metadata behavior.
