# PYPOST-1342: Technical Debt Analysis

Scope: optional `enum` / `items` on `McpToolParam`, schema emission, runtime validation,
request-editor columns, GitHub/GitLab curated param tightenings, and docs.

**No BLOCKER items.** New and edited test modules keep module-level
`pytest.mark.timeout` (30s / 60s for UI).

## Summary Table

| ID | Priority | Item | Follow-up | Jira |
| --- | --- | --- | --- | --- |
| TD-1 | Low | `items` validation only enforces top-level `items.type` | yes (new) | — |
| TD-2 | Low | Workflow-run `event` filters remain free-form (open-ended GitHub events) | no | accepted |
| TD-3 | Low | `make lint` fails on pre-existing `tests/test_mcp_server_registry.py` E501 | yes | [PYPOST-1303][] (context) |
| TD-4 | Lowest | Collection JSON re-serialized with `indent=2` may reorder keys vs prior hand edit | no | accepted |

## Shortcuts Taken

- **TD-1 — shallow `items` enforcement.** Runtime checks only `items["type"]` against
  known MCP scalar/object/array types. Nested `items.enum`, `minItems`, etc. are persisted
  and published in the schema but not enforced locally. Sufficient for curated string
  arrays; deeper JSON Schema validation would be a separate helper.
- **TD-2 — open-ended workflow `event`.** Architecture deliberately left list-runs `event`
  without enum because GitHub accepts many event names. Closed sets only.
- **No new metrics** for enum rejections (cardinality / prior MCP labeling policy).

## Code Quality Issues

- `McpParamsTable` is now seven columns; wide tables may need horizontal scroll on small
  screens — acceptable for power-user MCP tab.
- Synthetic GitHub/GitLab test requests now pass `enum`/`items` into `McpToolParam` so
  checker twins stay aligned with published schemas.

## Missing Tests

- No dedicated test that collection export/import round-trips `enum`/`items` through
  `build_export_payload` (covered indirectly by fixture load + schema equality and UI
  round-trip). Optional follow-up if export shape drifts.
- No live MCP client interoperability test against a third-party client that rejected
  arrays without `items`.

## Performance Concerns

None. Enum membership and array element checks are O(n) on argument size and run only for
declared constraints.

## Follow-up Tasks

1. **TD-1 — Deeper array `items` validation** (Low)
   If curated tools need `items.enum` or object item schemas, extend
   `validate_mcp_argument_values` (or a small JSON-Schema subset helper) beyond
   `items.type`.
2. **TD-3 — Test lint baseline / flake8 on tests** (existing)
   Pre-existing `make lint` → `lint-tests` failure at
   `tests/test_mcp_server_registry.py:308` E501. Confirm under [PYPOST-1303][] rather than
   a new ticket unless the baseline script needs a fresh allowance.

[PYPOST-1303]: https://pypost.atlassian.net/browse/PYPOST-1303
