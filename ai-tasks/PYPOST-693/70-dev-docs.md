# PYPOST-693: Developer Documentation

## Overview

Resolved audit finding **D-004** / **R-P1-002** by splitting nine PySide6-dependent modules
into `pypost/core/qt/`. Qt-free business logic remains in `pypost/core/` root. User-visible
behavior is unchanged.

## Documentation Updates

| File | Change |
| --- | --- |
| `doc/dev/architecture.md` | Added `core/qt/` subpackage to directory tree; updated layer rules |
| `doc/dev/architecture_audit.md` | Marked D-004 / R-P1-002 remediated |
| `doc/dev/testability.md` | Added Qt integration layer section |
| `doc/dev/testing.md` | Updated coverage paths for moved modules |
| `doc/dev/sensitive_data_masking_policy.md` | Updated worker/metrics module paths |

## Import Paths

```python
from pypost.core.qt.worker import RequestWorker
from pypost.core.qt.mcp_server import MCPServerManager
from pypost.core.qt.state_manager import StateManager
from pypost.core.qt.metrics import MetricsManager
from pypost.core.qt.collection_storage_gateway import CollectionStorageGateway
from pypost.core.qt.environment_storage_gateway import EnvironmentStorageGateway
from pypost.core.qt.encryption_migration_worker import EncryptionMigrationWorker
```

Qt-free alternatives:

```python
from pypost.core.metrics_protocol import MetricsTrackerProtocol, resolve_metrics
from pypost.core.mcp_server_impl import MCPServerImpl
from pypost.core.encryption_migration import EncryptionMigrationService
```

## Boundary Rule

Code that must run headless without PySide6 must **not** import from `pypost.core.qt`. Use
Qt-free modules in `pypost.core` and protocols in `pypost.core.metrics_protocol`.

## Troubleshooting

If tests fail with `ModuleNotFoundError` for old paths (`pypost.core.worker`, etc.), update
imports to `pypost.core.qt.*`. Logger names in `assertLogs` and `expected_log_allowlist.yaml`
must also use the new module path.
