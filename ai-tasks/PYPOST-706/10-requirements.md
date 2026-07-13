# PYPOST-706: Expand history masking beyond hidden_keys

## Definition of Done

- History writes redact Authorization/Cookie/api-key headers even without hidden_keys.
- Query tokens, Bearer tokens, and sensitive JSON body fields are masked heuristically.
- Shared sanitizer used by history and MCP response paths.
