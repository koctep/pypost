# Developer Documentation

Welcome to the **PyPost** developer documentation. This guide will help you understand the codebase,
set up your development environment, and contribute to the project.

## Table of Contents

1. [Setup and Installation](setup.md)
1. [Architecture Overview](architecture.md)
1. [Architecture and Package Boundary Audit (PYPOST-684)](architecture_audit.md)
1. [SOLID and Maintainability Audit](solid_audit.md)
1. [Security and Secrets Handling Audit (PYPOST-685)](security_audit.md)
1. [Test Coverage and Quality Audit (PYPOST-686)](test_audit.md)
1. [Code Quality and Maintainability Audit (PYPOST-687)](maintainability_audit.md)
1. [Observability and Logging Audit (PYPOST-688)](observability_audit.md)
1. [Unit Testability Patterns (PYPOST-382)](testability.md)
1. [MCP Integration](mcp_integration.md)
1. [Testing via MCP and Prometheus](testing.md)
1. [Request Actions](request_actions.md)
1. [Collection Item Delete](collection_item_delete.md)
1. [Collection Item Rename](collection_item_rename.md)
1. [Response Body Search](response_search.md)
1. [Hidden Variables](hidden_variables.md)
1. [Environment Variable Delete](environment_variable_delete.md)
1. [Environment Encryption at Rest](environment_encryption_at_rest.md)
1. [Encryption Key Migration (PYPOST-487)](encryption_key_migration.md)
1. [Metric Rename Migration (PYPOST-443)](metric_rename_migration.md)
1. [Async Environment Storage (PYPOST-486)](environment_storage_async.md)
1. [Template Expression Functions (PYPOST-450)](template_expression_functions.md)
1. [Body Editor Auto-Indent (PYPOST-105)](body_editor_indent.md)
1. [Body Editor Line Numbers (PYPOST-510)](body_editor_line_numbers.md)
1. [Body Editor Folding (PYPOST-511)](body_editor_folding.md)
1. [Body Editor Validation (PYPOST-512)](body_editor_validation.md)
1. [Body Format Selector (PYPOST-513)](body_format_selector.md)
1. [YAML as JSON Send Conversion (PYPOST-514)](yaml_as_json.md)
1. [UI Font Size and Global Styles (PYPOST-106)](ui_font_and_styles.md)

## Quick Start

To get the application running immediately using Make:

```bash
# Install dependencies and setup environment
make install

# Run the application
make run
```
