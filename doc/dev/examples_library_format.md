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
│   ├── gitlab_mcp.json                  # GitLab REST v4 MCP collection, 25 tools (PYPOST-1316)
│   ├── gitlab_mcp_rest_paths.json       # Locked offline path catalog for all 25 GitLab tools
│   ├── github_mcp.json                  # GitHub REST MCP collection, 30 tools (PYPOST-1334)
│   ├── github_mcp_rest_paths.json       # Locked offline path catalog + API version for 30 GitHub tools
│   └── mcp.json                         # Local MCP probe collection
└── environments/
    ├── jira_cloud.json                  # Standalone environment fixture
    ├── gitlab.json                      # GitLab companion environment (PYPOST-1316)
    └── github.json                      # GitHub companion environment (PYPOST-1334)

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
- `tests/test_gitlab_mcp_collection.py`: GitLab collection, environment, catalog, manifest and README contracts (PYPOST-1316).
- `tests/test_github_mcp_collection.py`: GitHub collection, environment, catalog, manifest and README contracts (PYPOST-1334).

### GitLab MCP collection (PYPOST-1316)

The manifest lists `collections/gitlab_mcp.json` after `jira_mcp.json`, adds the variables `gitlab_base_url`, `gitlab_project` and `gitlab_token` (`secret: true`), and adds the `gitlab_com` preset (no token). The catalog `gitlab_mcp_rest_paths.json` is not importable and is not listed in the manifest. See [GitLab MCP Example Collection](gitlab_mcp_collection.md) for the structure, encoding rules and the `make check-gitlab-mcp-path-freshness` workflow.

### GitHub MCP collection (PYPOST-1334)

The manifest lists `collections/github_mcp.json` after `gitlab_mcp.json` and before `mcp.json`, adds the variables `github_api_url`, `github_owner`, `github_repo` and `github_token` (`secret: true`), and adds the `github_com` preset (no token). The catalog `github_mcp_rest_paths.json` is not importable and is not listed in the manifest. See [GitHub MCP Example Collection](github_mcp_collection.md) for the structure, design decisions, encoding rules and the `make check-github-mcp-path-freshness` workflow.
