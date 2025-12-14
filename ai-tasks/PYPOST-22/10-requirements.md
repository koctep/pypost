# Requirements: PYPOST-22 - Configurable MCP Server Host

## Goals
Allow users to configure the network interface (host) on which the MCP server runs. By default, the server runs on `127.0.0.1` (localhost), which restricts access from external devices or containers. Users need the ability to change this to `0.0.0.0` or another IP address.

## User Stories
- As a user, I want to change the MCP server host to `0.0.0.0` so that I can connect to it from another computer or a Docker container.
- As a user, I want to see the current host and port in the interface to know where to connect.

## Acceptance Criteria
- [ ] **Settings**: Added "MCP Server Host" field to settings dialog.
- [ ] **Default Value**: `127.0.0.1`.
- [ ] **Validation**: The field accepts valid IP addresses or hostnames.
- [ ] **Server**: The server starts on the specified host.
- [ ] **UI**: The status bar displays the current address (e.g., `MCP: ON (0.0.0.0:1080)`).

## Task Description
Update `AppSettings`, `SettingsDialog`, and `MCPServerManager` to support host configuration.

### Technical Details
- **Component**: `SettingsDialog`.
- **Model**: `AppSettings.mcp_host`.
- **Server**: Pass `host` parameter to `uvicorn.run` or `starlette` server.
