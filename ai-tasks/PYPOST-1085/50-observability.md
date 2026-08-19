# Observability: PYPOST-1085

## Overview

Audited observability impacts of dropping the `for_window` back-reference and `MainWindow` MCP aliases.

## Findings

- No logging statements or metrics were added, removed, or modified.
- `mcp_persisted_servers_loaded` and `main_window_initialized` logs continue to fire as before.
