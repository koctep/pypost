# PYPOST-1044: Dev Docs

## Summary

The documentation now describes PyPost's persisted multi-endpoint MCP
registry.  Each endpoint selects one collection, one environment, and its own
globally unique port; it starts, stops, refreshes, and reports state
independently of every other endpoint.  The docs also document the explicit
legacy single-server conversion rather than implying that the active
environment controls registry-owned endpoints.

## Documentation delivered

| Location | Audience | Coverage |
| --- | --- | --- |
| `doc/dev/mcp_server_registry.md` | Developers | Registry ownership, configuration model, lifecycle API, isolation, migration, observability, troubleshooting, and focused checks. |
| `doc/dev/README.md`, `doc/dev/mcp_integration.md` | Developers | Developer-doc index plus implementation wiring, endpoint environment binding, scoped tool refresh, API, and configuration details. |
| `doc/dev/collection_import.md`, `doc/dev/jira_mcp_project_default.md`, `doc/dev/mcp_secrets_policy.md`, `doc/dev/mcp_trust_model.md`, `doc/dev/request_execution.md`, `doc/dev/security_audit.md`, `doc/dev/testing.md` | Developers | Collection/environment selection, secrets and trust boundaries, execution behavior, audit guidance, and regression-test expectations reconciled with endpoint isolation. |
| `doc/mcp_integration.md`, `doc/prometheus_monitoring.md` | Operators | Connection and operational guidance, including aggregate lifecycle metrics. |
| `doc/user/README.md`, `doc/user/environments.md`, `doc/user/getting-started.md`, `doc/user/interface.md`, `doc/user/mcp-tools.md`, `doc/user/settings.md`, `doc/user/workflows.md` | Users | Creating, configuring, starting, stopping, inspecting, and troubleshooting distinct MCP server rows. |
| `examples/README.md`, `examples/collections/jira_mcp.json` | Users and integrators | Updated example guidance and endpoint-selected collection/environment semantics. |

## Rule coverage

The developer-facing registry page and MCP integration guide cover the Step 8
template requirements in `.cursor/rules/70-dev-docs.mdc`:

- **Overview:** why the registry replaces the mutable application-wide
  endpoint.
- **Architecture:** `MainWindow`, `MCPServerRegistry`, per-row
  `MCPServerManager`/`MCPServerImpl` ownership, copied collection and
  environment inputs, and asynchronous enabled-row startup.
- **Usage:** the per-instance registry lifecycle API and the **MCP Servers…**
  management workflow.
- **Configuration:** persisted `AppSettings.mcp_servers`, endpoint fields,
  global port uniqueness, auto-start, and legacy conversion.
- **Troubleshooting:** failed startup, port conflicts, scoped tool exposure,
  transactional reconfiguration, and environment isolation.

## Validation and review

- [x] `QT_QPA_PLATFORM=offscreen .venv/bin/python -m pytest -q tests/test_mcp_server_registry.py tests/test_mcp_servers_dialog.py` — focused registry/dialog coverage passed (recorded earlier in the task as 16 passed).
- [x] `git diff --check` — no whitespace errors.
- [x] `.venv/bin/python scripts/verify_ai_task_artifacts.py` — its
  repository-wide scan reports no `PYPOST-1044` violation after adding this
  record.  It exits non-zero only for ten unrelated pre-existing task folders
  absent from the checked-in baseline (`PYPOST-1016`, `PYPOST-1025`,
  `PYPOST-1026`, `PYPOST-1033`, `PYPOST-968`, `PYPOST-974`, `PYPOST-975`,
  `PYPOST-976`, `PYPOST-978`, and `PYPOST-979`), which are outside this task.
- [x] Independent final documentation review — passed after all documentation findings were corrected.

## Worklog

tokens_used: 1100
role: execution
step: 8
step_name: Dev Docs artifact completion
