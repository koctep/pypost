# PYPOST-1224: [Libraries] Modernize examples to unified library format and preserve legacy fixtures in tests

## Architecture & Design

### 1. Modernized `examples/` Directory Layout

The `examples/` folder is restructured as a canonical Git Collection Library:

```text
examples/
├── pypost-library.yaml          # Manifest declaring library metadata, collections, variables, presets
├── README.md                    # Updated guide for using examples as a Git collection library
├── collections/
│   ├── jira_mcp.json            # Modernized Jira Cloud MCP collection (with embedded variable metadata)
│   ├── jira_mcp_critical_rest_paths.json # Offline REST path catalog
│   └── mcp.json                 # Local MCP probe collection
└── environments/
    └── jira_cloud.json          # Legacy environment fixture retained for standalone imports
```

### 2. Manifest Definition (`examples/pypost-library.yaml`)

```yaml
schema_version: "1.0.0"
id: "pypost-examples"
name: "PyPost Official Examples"
version: "2.0.0"
description: "Reference collection library showcasing Jira Cloud MCP integration, REST workflows, and local probing."
collections:
  - path: "collections/jira_mcp.json"
    name: "Jira Cloud MCP"
    description: "Curated Jira Cloud REST API collection with 22 MCP tools"
  - path: "collections/mcp.json"
    name: "Local MCP Probe"
    description: "Local MCP SSE endpoint probing tools"
variables:
  - key: "jira_base_url"
    value: "https://your-company.atlassian.net"
    description: "Jira Cloud site base URL"
    is_secret: false
  - key: "jira_project_key"
    value: "PROJ"
    description: "Default Jira project key or comma-separated keys"
    is_secret: false
  - key: "jira_credentials"
    value: ""
    description: "Atlassian account email:api_token"
    is_secret: true
presets:
  jira_cloud:
    jira_base_url: "https://your-company.atlassian.net"
    jira_project_key: "DEMO"
```

### 3. Preserved Legacy Fixtures (`tests/fixtures/legacy_collections/`)

To guarantee strict backward compatibility without risking regressions if `examples/` changes in the future, legacy collection/environment pairs are archived in `tests/fixtures/legacy_collections/`:

```text
tests/fixtures/legacy_collections/
├── README.md
├── legacy_jira_mcp_v1.json
├── legacy_jira_cloud_env_v1.json
├── legacy_gurushots_v1.json
└── legacy_mcp_v1.json
```

### 4. Automated Verification Test (`tests/test_examples_modernization_repro.py`)

Asserts:
1. `examples/pypost-library.yaml` exists and validates via `read_library_manifest` and `validate_manifest_collections`.
2. `examples/collections/jira_mcp.json` loads as valid collection format.
3. `tests/fixtures/legacy_collections/` contains legacy fixtures and verifies that legacy import loaders parse them without error.
