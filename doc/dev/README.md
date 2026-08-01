# Developer Documentation

Welcome to the **PyPost** developer documentation. This guide will help you understand the codebase,
set up your development environment, and contribute to the project.

## Table of Contents

### Setup and architecture

1. [Setup and Installation](setup.md)
1. [Architecture Overview](architecture.md)
1. [Architecture Decision Records (ADR) index](../adr/README.md)
1. [Request Execution](request_execution.md)
1. [TemplateService — central variable substitution](template_service.md)
1. [Template Expression Functions (PYPOST-450)](template_expression_functions.md)
1. [Variable Propagation](variable_propagation.md)
1. [Variable Validation](variable_validation.md)
1. [Sensitive Data Masking Policy (PYPOST-446)](sensitive_data_masking_policy.md)
1. [Request Data Copy Policy](request_data_copy_policy.md)
1. [State Manager](state_manager.md)

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
1. [Collection Tree Actions](collection_tree_actions.md)
1. [Collection Tree Performance](collection_tree_performance.md)
1. [Collection Item Delete](collection_item_delete.md)
1. [Collection Item Rename](collection_item_rename.md)
1. [Environments Dialog](environments_dialog.md)
1. [Environment Variable Delete](environment_variable_delete.md)
1. [Environment Encryption at Rest](environment_encryption_at_rest.md)
1. [Async Environment Storage (PYPOST-486)](environment_storage_async.md)
1. [Encryption Key Migration (PYPOST-487)](encryption_key_migration.md)
1. [Hidden Variables](hidden_variables.md)

### Request and response UI

1. [Request Actions](request_actions.md)
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
1. [Inbound MCP Trust Model (PYPOST-705)](mcp_trust_model.md)
1. [MCP Secrets Policy](mcp_secrets_policy.md)

### UI and settings

1. [Settings Dialog](settings_dialog.md)
1. [UI Font Size, Themes, and Global Styles (PYPOST-106, PYPOST-792)](ui_font_and_styles.md)
1. [UI Widget Mixins](ui_mixins.md)
1. [Keyboard Shortcuts and Hotkeys Dialog](hotkeys.md)

### Testing and quality

1. [Unit Testability Patterns (PYPOST-382)](testability.md)
1. [Testing via MCP and Prometheus](testing.md)
1. [Static Type Checking (PYPOST-734)](static_type_checking.md)
1. [GUI Testing](gui_testing.md)
1. [Agent UI E2E (PYPOST-839; broader packaging PYPOST-922)](agent_e2e.md)
1. [Agent E2E Environment Contract (PYPOST-856)](agent_e2e_env.md)
1. [Agent E2E Seed Inventory (PYPOST-857)](agent_e2e_seed.md)
1. [Agent E2E HTTP Fixture Layer (PYPOST-859)](agent_e2e_http.md)
1. [Agent E2E Response-Panel Helpers (PYPOST-869)](agent_e2e_response_panel.md)
1. [Agent App Lifecycle (PYPOST-833)](agent_lifecycle.md)
1. [UI Widget Identity (PYPOST-834)](ui_identity.md)
1. [UI State Snapshot (PYPOST-835)](ui_snapshot.md)
1. [UI Action Tools (PYPOST-836)](ui_actions.md)
1. [UI Settle / Wait Helpers (PYPOST-837)](ui_wait.md)
1. [Agent Golden E2E (PYPOST-838)](agent_golden_e2e.md)
1. [Agent E2E Product Dialog Settle (PYPOST-919)](agent_dialog_settle.md)
1. [Agent E2E Double Response-Body Lock (PYPOST-889)](agent_e2e_double_response_body.md)
1. [Agent E2E Presentation Matrix (PYPOST-890)](agent_e2e_presentation_matrix.md)
1. [Metric Rename Migration (PYPOST-443)](metric_rename_migration.md)

### Tech debt

1. [Tech Debt Inventory](tech_debt_inventory.md)
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
