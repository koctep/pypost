# PYPOST-992 Observability

The test observes only the external MCP contract:

- sidecar subprocess startup and MCP initialization complete;
- `ui_fill` returns `{"ok": true}`;
- `ui_click` returns `{"ok": true}`;
- nested stdio contexts close within the test's bounded lifecycle.

The fill value is a deterministic test URL and is not logged by the sidecar;
the test does not add payload logging or alter production observability.
Failure diagnostics come from the existing sidecar stderr capture and the
Make runner's bounded worker timeout.
