# PYPOST-992 Architecture

## Test topology

```text
pytest process
    │ stdio pipes
    ▼
pypost.agent.ui_actions_mcp subprocess
    │ in-process Qt widgets
    ▼
AgentAppSession → active request tab → URL QLineEdit
```

The parent creates `StdioServerParameters` with the current Python executable
and starts the module entry point. The child owns its QApplication and
`AgentAppSession`, exactly as an external stdio MCP client would use it.

## Assertions

The test initializes the MCP session, calls `ui_fill` on
`pypost_url_input` with `in_current_tab=true`, then calls `ui_click` on that
same visible editable widget. Both returned text payloads must equal
`{"ok": true}`. Using the URL field for the click avoids opening the plus-tab
menu, which is not deterministic under the offscreen Qt platform and is
outside the ticket's click/fill contract.

## Lifecycle

Nested `stdio_client` and `ClientSession` contexts close the pipes and let the
sidecar's existing `finally` block shut down its `AgentAppSession`. The test
module and action calls use bounded timeouts; the Make parallel runner adds a
process-level worker bound.
