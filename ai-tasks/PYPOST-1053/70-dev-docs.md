# PYPOST-1053: Developer Documentation

## Summary

Step 8 documents the shipped CI-safe Jira MCP collection e2e pack.

## Developer Documentation

**New reference:** `doc/dev/jira_mcp_collection_e2e.md`

Documents the pack overview, four read-only workflows, real request-path
architecture, focused and default-suite usage, public timeout behavior,
fixed offline configuration, loopback-only safety boundary, and troubleshooting.

**Updated references:**

- `doc/dev/testing.md` lists the target and replaces the stale planned-pack note.
- `doc/dev/jira_mcp_live_smoke.md` distinguishes the default loopback pack from
  the protected opt-in tenant smoke.
- `doc/dev/mcp_integration.md` describes the shipped standard-suite pack.
- `doc/dev/agent_e2e.md` distinguishes the real socket path from UI HTTP stubs.
- `doc/dev/README.md` indexes the new reference.

## Verification

- `make test-mcp-collection-e2e` — passed (1 test).
- `git diff --check` — passed.
- Confirmed no stale developer-doc references describe the collection pack as
  planned or unshipped.
