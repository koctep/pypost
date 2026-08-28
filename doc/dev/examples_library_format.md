# Examples Collection Library & Legacy Fixtures

## Overview

As part of parent epic [PYPOST-1219](https://pypost.atlassian.net/browse/PYPOST-1219) (*Git-based Collection Libraries & Self-Contained Collection Format*), **PYPOST-1224** modernizes the `examples/` directory into a canonical Git Collection Library and archives legacy format fixtures in `tests/fixtures/legacy_collections/`.

### Directory Layout

```text
examples/
├── pypost-library.yaml                  # Library manifest declaring bundled collections and variable schemas
├── README.md                            # Comprehensive user and developer guide
├── collections/
│   ├── jira_mcp.json                    # Modernized Jira Cloud MCP collection (with embedded variable metadata)
│   ├── jira_mcp_critical_rest_paths.json # Offline REST path catalog
│   └── mcp.json                         # Local MCP probe collection
└── environments/
    └── jira_cloud.json                  # Standalone environment fixture

tests/fixtures/legacy_collections/
├── README.md                            # Legacy fixtures explanation
├── legacy_jira_mcp_v1.json              # Frozen v1 Jira Cloud collection
├── legacy_jira_cloud_env_v1.json        # Frozen v1 Jira environment
├── legacy_mcp_v1.json                   # Frozen v1 MCP collection
└── legacy_gurushots_v1.json             # Frozen v1 GuruShots collection
```

### Verification & Testing

- `tests/test_examples_modernization_repro.py`: Repro test ensuring manifest existence and collection disk validation.
- `tests/test_examples_modernization.py`: Comprehensive test suite verifying manifest metadata, embedded variables, and backward compatibility with legacy fixtures.
