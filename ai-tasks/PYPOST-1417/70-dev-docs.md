# Reusable Multi-Subsystem Integration Harness Helper (PYPOST-1417)

## Overview

Developer documentation decisions and records for [PYPOST-1417](https://pypost.atlassian.net/browse/PYPOST-1417) (*Reusable multi-subsystem integration harness helper*).

This task extracts the `CollectionVariablesIntegrationHarness` previously embedded inside `tests/test_collection_scoped_variables_integration.py` into a shared, reusable test helper module at [`tests.helpers.collection_integration_harness`](file:///home/src/tests/helpers/collection_integration_harness.py). It provides context manager support (`__enter__`/`__exit__`), standard pytest fixture bindings (`collection_integration_harness` and `collection_harness`), and safe, idempotent resource teardown.

---

## Documentation Updates

1. **New Dedicated Developer Guide**:
   - [`doc/dev/collection_integration_harness.md`](file:///home/src/doc/dev/collection_integration_harness.md)
     - Created a comprehensive reference document covering the `tests.helpers.collection_integration_harness` module architecture, coordinated services, pytest fixtures, context manager usage, programmatic helper methods, dataclass contracts, and resource teardown guarantees.
2. **Updated Architecture Guide**:
   - [`doc/dev/collection_scoped_variables.md`](file:///home/src/doc/dev/collection_scoped_variables.md)
     - Updated the section *Integration Test Harness Architecture (`CollectionVariablesIntegrationHarness`)* to reference the shared helper module `tests.helpers.collection_integration_harness`.
     - Documented the seven coordinated subsystem services (`StorageManager`, `LibraryConnectionStore`, `LocalOverlayManager`, `TemplateService`, `LibraryManagerService`, `LibraryRuntimeResolver`, `MCPServerRegistry`).
     - Added context manager code examples (`with CollectionVariablesIntegrationHarness(...) as harness:`).
     - Added pytest fixture binding documentation (`collection_integration_harness` and alias `collection_harness`).
     - Documented all programmatic helper methods (`create_library`, `create_workspace_environment`, `create_overlay`, `start_standalone_server`, `run_unified_lifecycle`).
     - Documented the `UnifiedLifecycleResult` dataclass and its fields.
     - Documented resource teardown guarantees (idempotent `teardown()`, stopping running MCP servers, closing connection stores).
     - Documented reference test suites (`tests/test_collection_integration_harness_repro.py` and `tests/test_collection_scoped_variables_integration.py`).
     - Added [PYPOST-1417](https://pypost.atlassian.net/browse/PYPOST-1417) and `collection_integration_harness.md` to Traceability & References.
3. **Updated Developer Documentation Index**:
   - [`doc/dev/README.md`](file:///home/src/doc/dev/README.md)
     - Added `[Reusable Collection Integration Test Harness (PYPOST-1417)](collection_integration_harness.md)` under both *Collections and environments* and *Testing and quality* sections.

---

## Architecture & Coordinated Services

[`CollectionVariablesIntegrationHarness`](file:///home/src/tests/helpers/collection_integration_harness.py) centralizes the setup, orchestration, and teardown of seven core domain services within an isolated filesystem tree rooted at `tmp_path`:

```
tmp_path/
├── libraries/                # Synthesized library catalogs and collections
│   └── <manifest_id>/
│       ├── pypost-library.json
│       └── collections/
│           └── <collection_id>.json
├── workspace/                # Workspace storage for environments and collections
│   └── environments/
│       └── environments.json
├── libraries_data/           # Machine-local overlays (mode 0o600)
│   └── <manifest_id>/
│       └── overlay.json
└── connections.json          # Library connection registry
```

- **[`StorageManager`](file:///home/src/pypost/core/storage.py)**: Manages workspace environments under `tmp_path/workspace/`.
- **[`LibraryConnectionStore`](file:///home/src/pypost/core/library_connection_store.py)**: Persists library connection metadata at `tmp_path/connections.json`.
- **[`LocalOverlayManager`](file:///home/src/pypost/core/local_overlay_manager.py)**: Manages local secret overrides under `tmp_path/libraries_data/` with `0o600` permissions.
- **[`TemplateService`](file:///home/src/pypost/core/template_service.py)**: Evaluates template expressions in URLs, headers, and request bodies.
- **[`LibraryManagerService`](file:///home/src/pypost/core/library_manager_service.py)**: Discovers catalog and legacy manifests and registers collections.
- **[`LibraryRuntimeResolver`](file:///home/src/pypost/core/library_runtime_resolver.py)**: Implements 3-tier precedence and standalone environment resolution.
- **[`MCPServerRegistry`](file:///home/src/pypost/core/mcp_server_registry.py)**: Supervises local and standalone MCP server lifecycles, states, and process lifecycles.

---

## API & Usage Patterns

### Context Manager Usage

```python
from tests.helpers.collection_integration_harness import CollectionVariablesIntegrationHarness

def test_custom_scenario(tmp_path):
    with CollectionVariablesIntegrationHarness(tmp_path) as harness:
        lib_dir = harness.create_library("my-lib", collections_data={...})
        server_id, port, status = harness.start_standalone_server("my-lib", "col1")
        assert status == "running"
    # Guaranteed: harness.teardown() stops all servers and releases ports
```

### Pytest Fixture Bindings

```python
from tests.helpers.collection_integration_harness import (
    collection_integration_harness,
    collection_harness,
)

def test_via_fixture(collection_integration_harness):
    result = collection_integration_harness.run_unified_lifecycle(...)
    assert result.status == "success"

def test_via_alias(collection_harness):
    env = collection_harness.create_workspace_environment(name="Dev")
    assert env.name == "Dev"
```

### Programmatic Helper Methods

- **`create_library(manifest_id, is_legacy_manifest, collections_data, manifest_variables, manifest_presets) -> Path`**: Synthesizes a library catalog directory (v2 catalog or v1 legacy) and connects it to `LibraryManagerService`.
- **`create_workspace_environment(name, variables, hidden_keys) -> Environment`**: Creates and saves an isolated workspace environment.
- **`create_overlay(library_id, active_profile, secrets) -> LocalLibraryOverlay`**: Creates and saves a machine-local overlay with `0o600` permissions.
- **`start_standalone_server(manifest_id, collection_id, collection_filename, collection_name, host, port) -> tuple[str, int, str]`**: Configures, starts, and verifies a standalone MCP server on an ephemeral collision-free port via `allocate_tcp_port()`.
- **`run_unified_lifecycle(...) -> UnifiedLifecycleResult`**: Orchestrates discovery → overlay configuration → standalone MCP server startup → workspace environment import → request template substitution.

### Data Contract: `UnifiedLifecycleResult`

```python
@dataclass
class UnifiedLifecycleResult:
    """Outcome of end-to-end multi-subsystem workflow execution."""
    status: str
    standalone_server_id: str
    standalone_status: str
    imported_summary: ImportSummary
    rendered_request_url: str
    rendered_auth_header: str
    rendered_body: str
```

---

## Resource Teardown & Invariants

- **Idempotent Teardown**: `teardown()` and `close()` safely call `registry.stop_all()`. Multiple calls or calling after context manager exit are safe no-ops.
- **Exception Logging**: `__exit__` catches and logs unhandled exceptions during test execution before running teardown.
- **Dynamic Port Allocation**: Uses `tests.helpers.port_allocation.allocate_tcp_port()` to avoid port collisions in parallel test runs.
- **Zero Global State**: All file operations and configurations are confined strictly to `tmp_path`.

---

## Verification & Test References

- [`tests/test_collection_integration_harness_repro.py`](file:///home/src/tests/test_collection_integration_harness_repro.py): Repro and verification suite confirming harness imports, context manager lifecycle, fixture bindings, and lifecycle execution.
- [`tests/test_collection_scoped_variables_integration.py`](file:///home/src/tests/test_collection_scoped_variables_integration.py): Full integration and compatibility test suite consuming the shared helper.
