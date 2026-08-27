# Developer Documentation

Welcome to the **PyPost** developer documentation. This guide will help you understand the codebase,
set up your development environment, and contribute to the project.

**End-user documentation** lives in the [User Guide](../user/README.md) under `doc/user/`.
The docs hub is [`doc/README.md`](../README.md) (user vs integration vs developer).
See [User Guide and Documentation Layout](user_guide.md) for layout and maintenance
conventions.

## Table of Contents

### Setup and architecture

1. [Setup and Installation](setup.md)
1. [Architecture Overview](architecture.md)
1. [User Guide and Documentation Layout (PYPOST-1015)](user_guide.md)
1. [Architecture Decision Records (ADR) index](../adr/README.md)
1. [Request Execution](request_execution.md)
1. [WebSocket Transport Seam and Session Engine (PYPOST-1127)](websocket_session_engine.md)
1. [WebSocket Message Stream, Codecs, and Transcript Export (PYPOST-1130)](websocket_message_stream.md)
1. [WebSocket TLS and Connection-Security Policy (PYPOST-1131)](websocket_tls_security.md)
1. [WebSocket UI Client and Live Stream Inspector (PYPOST-1132)](websocket_ui_client.md)
1. [WebSocket Stream Inspector and Virtualized Live Stream Viewer (PYPOST-1133)](websocket_stream_inspector.md)
1. [WebSocket Multi-Format Composer, Saved Presets, and Sequence Runner (PYPOST-1134)](websocket_composer_presets_sequences.md)
1. [WebSocket Environments, Templating, and Secret Masking (PYPOST-1135)](websocket_environments_templating_and_masking.md)
1. [WebSocket Settings, Session Ceiling, Metrics, and Logging (PYPOST-1136)](websocket_settings_session_ceiling_and_metrics.md)
1. [Bounded MCP WebSocket Probe Tool (PYPOST-1137)](websocket_mcp_probe_tool.md)
1. [WebSocket Subsystem Architecture (PYPOST-1138)](websocket_architecture.md)
1. [TemplateService — central variable substitution](template_service.md)
1. [Template Expression Functions and Integer Conversion (PYPOST-450, PYPOST-1037, PYPOST-1038)](template_expression_functions.md)
1. [Variable Propagation](variable_propagation.md)
1. [Variable Validation](variable_validation.md)
1. [Sensitive Data Masking Policy (PYPOST-446)](sensitive_data_masking_policy.md)
1. [Request Data Copy Policy](request_data_copy_policy.md)
1. [State Manager](state_manager.md)
1. [Presenter Architecture and Interaction Model (PYPOST-1082)](presenter_architecture.md)
1. [Headless Daemon Mode (PYPOST-1046)](daemon.md)

### Audits

1. [Architecture and Package Boundary Audit (PYPOST-684)](architecture_audit.md)
1. [SOLID and Maintainability Audit](solid_audit.md)
1. [Security and Secrets Handling Audit (PYPOST-685)](security_audit.md)
1. [Test Coverage and Quality Audit (PYPOST-686)](test_audit.md)
1. [Code Quality and Maintainability Audit (PYPOST-687)](maintainability_audit.md)
1. [Logging Event Naming Convention (PYPOST-747)](logging.md)
1. [Observability and Logging Audit (PYPOST-688)](observability_audit.md)
1. [Prometheus Monitoring](../prometheus_monitoring.md)
1. [Performance and Scalability Audit (PYPOST-689)](performance_audit.md)
1. [Documentation and ADR Alignment Audit (PYPOST-690)](documentation_audit.md)
1. [Dependencies and Supply Chain Audit (PYPOST-691)](dependencies_audit.md)
1. [Licensing and Distribution — PySide6 LGPL (PYPOST-786)](licensing.md)

### Collections and environments

1. [Collection Loading](collection_loading.md)
1. [Collection Storage](collection_storage.md)
1. [Collection Import](collection_import.md)
1. [Collection Export](collection_export.md)
1. [Shared JSON Export Root Policy (PYPOST-1010)](json_export_root.md)
1. [WebSocket Connection Profile Model, Persistence, and Interchange (PYPOST-1128)](websocket_persistence_and_interchange.md)
1. [Collection Tree Actions](collection_tree_actions.md)
1. [Collections WebSocket Context Menu (PYPOST-1160)](websocket_collections_menu.md)
1. [WebSocket Save-to-Collection Flow (PYPOST-1161)](websocket_save_flow.md)
1. [WebSocket Session Hotkeys (PYPOST-1162)](websocket_hotkeys.md)
1. [Collection Tree Performance](collection_tree_performance.md)
1. [Collection Item Delete](collection_item_delete.md)
1. [Collection Item Rename](collection_item_rename.md)
1. [Collection Item Strategies and Dispatch Context (PYPOST-1193)](collection_item_strategies.md)
1. [Environments Dialog](environments_dialog.md)
1. [Environment Management and Variable Display (PYPOST-1073)](environments.md)
1. [Environment Variable Delete](environment_variable_delete.md)
1. [Environment Encryption at Rest](environment_encryption_at_rest.md)
1. [Async Environment Storage (PYPOST-486)](environment_storage_async.md)
1. [Encryption Key Migration (PYPOST-487)](encryption_key_migration.md)
1. [Hidden Variables](hidden_variables.md)

### Request and response UI

1. [Request Actions](request_actions.md)
1. [Blank-tab protocol picker (PYPOST-1157 / PYPOST-1165 / PYPOST-1183)](new_tab_protocol_picker.md)
1. [Last-tab close protocol picker (PYPOST-1159 / PYPOST-1183)](last_tab_protocol_picker.md)
1. [Blank WebSocket draft tab lifecycle (PYPOST-1158)](websocket_draft_tab.md)
1. [MCP Client draft tab (PYPOST-1166–1170)](mcp_client_draft_tab.md)
1. [Shared empty-row Key/Value table (PYPOST-1186)](empty_row_key_value_table.md)
1. [Open Request in Isolated Tab](open_request_in_isolated_tab.md)
1. [Response Streaming Display (PYPOST-887)](response-streaming-display.md)
1. [Response Body Search](response_search.md)
1. [Copy as cURL](copy_curl.md)
1. [Method / Body Auto-Switch](method_body_autoswitch.md)
1. [JSON Syntax Highlighting](json_syntax_highlighting.md)

### Body editor

1. [Body Editor Auto-Indent (PYPOST-105)](body_editor_indent.md)
1. [Body Editor Line Numbers (PYPOST-510)](body_editor_line_numbers.md)
1. [Body Editor Folding (PYPOST-511)](body_editor_folding.md)
1. [Body Editor Validation (PYPOST-512)](body_editor_validation.md)
1. [Body Format Selector (PYPOST-513)](body_format_selector.md)
1. [YAML as JSON Send Conversion (PYPOST-514)](yaml_as_json.md)

### MCP

1. [MCP Integration](mcp_integration.md)
1. [MCP Client draft tab (PYPOST-1166–1170)](mcp_client_draft_tab.md)
1. [Shared empty-row Key/Value table (PYPOST-1186)](empty_row_key_value_table.md)
1. [MCP Reverse Proxy (PYPOST-1092)](mcp_proxy.md)
1. [Multiple independent MCP servers (PYPOST-1044)](mcp_server_registry.md)
1. [MCP argument query/body regression coverage (PYPOST-1034)](mcp_integration.md#mcp-argument-substitution-coverage-pypost-1034)
1. [Jira numeric identifier MCP contract (PYPOST-1038)](mcp_integration.md#jira-numeric-path-identifiers-pypost-1038)
1. [Optional MCP parameter defaults (PYPOST-1054)](mcp_integration.md#optional-mcp-parameter-defaults-pypost-1054)
1. [Jira MCP Example Project Default (PYPOST-1032)](jira_mcp_project_default.md)
1. [Jira MCP critical REST path freshness (PYPOST-1030 / PYPOST-1056)](jira_mcp_path_freshness.md)
1. [Optional protected Jira MCP live smoke (PYPOST-1039)](jira_mcp_live_smoke.md)
1. [CI-safe Jira MCP collection e2e (PYPOST-1053)](jira_mcp_collection_e2e.md)
1. [Inbound MCP Trust Model (PYPOST-705)](mcp_trust_model.md)
1. [MCP Secrets Policy](mcp_secrets_policy.md)
1. [Bounded MCP WebSocket Probe Tool (PYPOST-1137)](websocket_mcp_probe_tool.md)
1. [UI Action Tools — out-of-process packaging (PYPOST-918)](ui_actions.md)
1. [jira-mcp example fixtures](
   testing.md#example-fixtures-contract-pypost-1017--pypost-1026--pypost-1047--pypost-1028--pypost-1048--pypost-1050--pypost-1056)
   (including protected stretch-operation contracts, PYPOST-1027, and
   env/auth/`mcp_params` contracts, PYPOST-1028)

### UI and settings

1. [Settings Dialog](settings_dialog.md)
1. [UI Font Size, Themes, and Global Styles (PYPOST-106, PYPOST-792)](ui_font_and_styles.md)
1. [UI Widget Mixins](ui_mixins.md)
1. [Keyboard Shortcuts and Hotkeys Dialog](hotkeys.md)

### Testing and quality

1. [Unit Testability Patterns (PYPOST-382)](testability.md)
1. [Testing via MCP and Prometheus](testing.md)
1. [Parallel Test Runner Orchestrator (PYPOST-1149)](parallel_test_runner.md)
1. [Test Log Guardrails and Capture (PYPOST-1081)](test_log_guardrails.md)
1. [Verification-Artifact Contracts (PYPOST-1077)](verification_artifact_contracts.md)
1. [AI Task Artifacts Verification (PYPOST-816, PYPOST-1071, PYPOST-1079)](ai_task_artifacts_verification.md)
1. [Static Type Checking (PYPOST-734)](static_type_checking.md)
1. [GUI Testing](gui_testing.md)
1. [Agent UI E2E (PYPOST-839; broader packaging PYPOST-922)](agent_e2e.md)
1. [Agent E2E Environment Contract (PYPOST-856)](agent_e2e_env.md)
1. [Agent E2E Seed Inventory (PYPOST-857)](agent_e2e_seed.md)
1. [Agent E2E HTTP Fixture Layer (PYPOST-859)](agent_e2e_http.md)
1. [Agent E2E Response-Panel Helpers (PYPOST-869)](agent_e2e_response_panel.md)
1. [Agent E2E Send Settle Helpers (PYPOST-948)](agent_e2e_send_settle.md)
1. [Agent App Lifecycle (PYPOST-833)](agent_lifecycle.md)
1. [UI Widget Identity (PYPOST-834)](ui_identity.md)
1. [UI State Snapshot (PYPOST-835)](ui_snapshot.md)
1. [UI Action Tools (PYPOST-836; out-of-process packaging PYPOST-918)](ui_actions.md)
1. [Agent UI Actions MCP (PYPOST-952; attach PYPOST-1207; ATTACH-3
   verification PYPOST-1208)](agent_ui_actions_mcp.md#proven-vs-manual-attach-3--pypost-1208)
1. [UI Settle / Wait Helpers (PYPOST-837)](ui_wait.md)
1. [Agent Golden E2E (PYPOST-838)](agent_golden_e2e.md)
1. [Agent E2E Product Dialog Settle (PYPOST-919)](agent_dialog_settle.md)
1. [Agent E2E Double Response-Body Lock (PYPOST-889)](agent_e2e_double_response_body.md)
1. [Agent E2E Presentation Matrix (PYPOST-890)](agent_e2e_presentation_matrix.md)
1. [Scripted WebSocket Test Server and Fixture (PYPOST-1129)](websocket_test_harness.md)
1. [Metric Rename Migration (PYPOST-443)](metric_rename_migration.md)

### Tech debt

1. [Tech Debt Inventory](tech_debt_inventory.md)
1. [Tech Debt → Jira Sync (PYPOST-1016)](tech_debt_jira_sync.md)
1. [Post-request Scripts Tech Debt (PYPOST-10)](tech-debt/PYPOST-10.md)
1. [Settings and Hotkeys Tech Debt (PYPOST-11)](tech-debt/PYPOST-11.md)
1. [Template Service Tech Debt (PYPOST-21)](tech-debt/PYPOST-21.md)
1. [Variable Validation Tech Debt (PYPOST-25)](tech-debt/PYPOST-25.md)
1. [SOLID Audit Tech Debt (PYPOST-40)](tech-debt/PYPOST-40.md)
1. [Qt Mouse Event API Tech Debt (PYPOST-431)](tech-debt/PYPOST-431.md)
1. [Pytest and CI Hygiene Tech Debt (PYPOST-434)](tech-debt/PYPOST-434.md)
1. [History-recording Helper Tech Debt (PYPOST-463)](tech-debt/PYPOST-463.md)

## Quick Start

To get the application running immediately using Make:

```bash
# Install dependencies and setup environment
make install

# Run the application
make run
```
