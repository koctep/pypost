# PYPOST-959: Dev Docs Update

## Changes

Updated `doc/dev/agent_e2e_http.md`:

- Compound-key match rule documents uppercase map-key convention and request
  method uppercasing before lookup (PYPOST-959).
- Unit proof list includes
  `test_stub_agent_e2e_http_url_router_compound_key_mixed_case_method`.

## Scope

Minimal touch to existing URL router section; no new standalone doc file.

## Verification

- Doc references match new unit test name.
- Normalization note aligns with `_resolve_url_router_response` behavior.
