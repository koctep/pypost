# Architecture Decision Records (ADR) Index

PyPost does not yet store full ADR markdown files per decision. This index links the major
architectural choices to their canonical developer documentation and originating Jira tasks.

Use this page for onboarding; use linked `doc/dev/` guides for implementation detail.

## Index

| ID | Decision | Status | Primary references |
| --- | --- | --- | --- |
| ADR-001 | Presenter-based UI decomposition (MainWindow split) | Accepted | [solid_audit.md](../dev/solid_audit.md), [PYPOST-43](https://pypost.atlassian.net/browse/PYPOST-43) |
| ADR-002 | Composition root and dependency injection in `main.py` | Accepted | [testability.md](../dev/testability.md), [PYPOST-404](https://pypost.atlassian.net/browse/PYPOST-404) |
| ADR-003 | Async encrypted environment storage | Accepted | [environment_storage_async.md](../dev/environment_storage_async.md), [PYPOST-486](https://pypost.atlassian.net/browse/PYPOST-486) |
| ADR-004 | MCP server threading and lifecycle model | Accepted | [mcp_integration.md](../dev/mcp_integration.md), [PYPOST-556](https://pypost.atlassian.net/browse/PYPOST-556) |
| ADR-005 | MetricsManager injection and Prometheus facade | Accepted | [testing.md](../dev/testing.md), [PYPOST-44](https://pypost.atlassian.net/browse/PYPOST-44) |
| ADR-006 | Sensitive data masking for history and logs | Accepted | [sensitive_data_masking_policy.md](../dev/sensitive_data_masking_policy.md), [PYPOST-446](https://pypost.atlassian.net/browse/PYPOST-446) |
| ADR-007 | MCP inbound trust model | Accepted | [mcp_trust_model.md](../dev/mcp_trust_model.md), [PYPOST-705](https://pypost.atlassian.net/browse/PYPOST-705) |
| ADR-008 | TemplateService central substitution | Accepted | [template_service.md](../dev/template_service.md) |
| ADR-009 | Collection tree presenter/actions split | Accepted | [collection_tree_actions.md](../dev/collection_tree_actions.md) |
| ADR-010 | Request execution and HTTP client layering | Accepted | [request_execution.md](../dev/request_execution.md) |

## How to add a decision

1. Implement the change with `ai-tasks/<JIRA-ID>/20-architecture.md` as the task record.
2. Add or update a `doc/dev/<topic>.md` guide when the decision affects contributors.
3. Append a row to this index with links to both artifacts.

## Related

- [Developer documentation hub](../dev/README.md)
- [Documentation audit (PYPOST-690)](../dev/documentation_audit.md)
