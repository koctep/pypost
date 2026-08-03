# PYPOST-1027: Developer Documentation

## Summary

The developer testing guide now records the three protected Jira MCP stretch
operations: worklog lookup, move-to-backlog for removing sprint membership,
and assignable-user search. The code change remains an offline fixture
contract only; it does not alter the shipped collection, runtime MCP behavior,
or end-user workflow.

## Documentation delivered

| Location | Audience | Coverage |
| --- | --- | --- |
| `doc/dev/testing.md` | Contributors and maintainers | Contract overview, native-loader architecture, protected request ID/method/route guarantee, MCP tool usage, offline validation command, configuration boundary, and failure recovery. |
| `doc/dev/README.md` | Developers | MCP documentation index points readers to the fixture-contract guide and identifies the PYPOST-1027 coverage. |

## Contract usage

Run the deterministic fixture check without credentials, a running MCP server,
or a network connection:

```bash
.venv/bin/python -m pytest tests/test_example_fixtures.py -v
```

When a protected workflow is intentionally approved, add one immutable row to
`PROTECTED_STRETCH_JIRA_MCP_OPERATIONS`; its request ID, HTTP method, and route
markers then feed both the required-ID check and the parametrized operation
check. Do not use the collection-size floor as evidence that a particular
workflow remains available.

## Scope decision

No user documentation was changed. PYPOST-1027 neither changes the curated
Jira collection nor changes a user-visible MCP API; it strengthens the
maintainer-facing regression contract for already-shipped requests.

## Validation and review

- [x] Focused fixture-contract test passes offline.
- [x] Independent documentation review passed: Markdown links, index anchor,
  factual accuracy, and test-only scope were confirmed.
- [x] No credentials, live Jira calls, or user-facing claims were introduced.

## Worklog

tokens_used: 0
role: execution
step: 8
step_name: Dev Docs
