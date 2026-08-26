# PYPOST-1171: Migrate/remove HTTP method MCP

## Goals

HTTP method **MCP** overloaded the request editor with outbound MCP client
behavior (list/call via JSON body). Dedicated MCP Client tab mode (MCP-TM-1…4)
now provides connect → list → invoke UX. Users and collections must stop
creating new HTTP **MCP** requests while legacy collection items keep working.

## User Stories

- As a **user creating requests**, I no longer see **MCP** in the HTTP method
  dropdown, so I choose the dedicated MCP Client tab for outbound MCP.
- As a **user opening a legacy collection item** with `method: "MCP"`, I get an
  MCP Client tab with URL, headers, and body mapped to connect/invoke state.
- As a **maintainer of examples/collections/mcp.json**, I can still open
  "List Tools" via migration without editing the fixture file.
- As a **developer**, I expect `RequestService` to execute HTTP only; outbound
  MCP runs through `McpClientPresenter`.

## Definition of Done

- [x] **MCP** removed from HTTP method combo
- [x] `method:MCP` items open `McpClientTab` with URL/body mapping
- [x] `examples/collections/mcp.json` workflow works via convert-on-open
- [x] `_execute_mcp` dispatch removed from `RequestService`

## Task Description

Retire the HTTP method MCP path. Legacy items convert on open to
`McpClientConnection` (convert-on-open, no bulk collection rewrite). Depends
on MCP-TM-4 (invoke pane) for body → tool pre-selection.

## Q&A

| Question | Answer |
| --- | --- |
| Bulk migrate collection JSON? | No — convert-on-open per parent architecture |
| What happens on Send for method MCP? | Route to MCP Client tab before Send; no HTTP dispatch |
