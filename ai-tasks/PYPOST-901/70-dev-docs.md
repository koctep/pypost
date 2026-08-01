# PYPOST-901: Developer Documentation

## Updates

| Doc | Change |
| --- | --- |
| `doc/dev/agent_e2e_http.md` | URL-router section links GUI multi-URL scenario + run command |
| `doc/dev/agent_e2e.md` | Harness table row for mapping multi-URL module (901) |

## Review

Self-review against `70-dev-docs.mdc`: router API already documented (868);
Step 8 adds discoverability — harness table sync and named GUI module with
`make test-agent-e2e` target. Guard
`tests/test_agent_e2e_harness_table_doc.py` green after table row.
