# Dual Runtime Distribution Modes and Headless Daemon (PYPOST-1046, PYPOST-1269)

## Overview

PyPost provides first-class support for two distinct runtime distribution and execution modes,
tailored to interactive developer environments and automated headless environments:

1. **GUI Desktop Mode**: A full-featured desktop application for interactive API design, request
   composition, real-time inspection, tab organization, and environment management. Launches via
   `pypost`, `python -m pypost`, or `make run`.
2. **Headless Daemon Mode**: A lightweight, background service runtime executing Prometheus
   metrics and enabled MCP servers without initializing a graphical user interface or requiring a
   display server (such as X11 or Wayland). Launches via `pypost-daemon`, `python -m pypost.daemon`,
   or `make run-daemon`.

The entry point for headless execution is completely decoupled from the desktop Qt Widgets
application (`pypost/main.py`), avoiding unnecessary widget allocations, desktop UI settings
persistence, or offscreen window emulation.

## Architecture

### System Module Breakdown

```text
┌────────────────────────────────────────────────────────────────────────┐
│                        Execution Entry Points                          │
│                                                                        │
│   CLI: pypost                CLI: pypost-daemon     CLI: pypost-agent  │
│   Module: python -m pypost   Module: python -m ...  UI sidecar         │
└──────────────────┬───────────────────────┬─────────────────────────────┘
                   │                       │
                   ▼                       ▼
┌──────────────────────────────┐ ┌───────────────────────────────────────┐
│     GUI Desktop Runtime      │ │       Headless Daemon Runtime         │
│     (pypost.main:main)       │ │       (pypost.daemon:main)            │
│                              │ │                                       │
│  - PySide6.QtWidgets.QApp    │ │  - PySide6.QtCore.QCoreApplication    │
│  - MainWindow & Widgets      │ │  - DaemonRuntime lifecycle            │
│  - AgentUiAttachHost (IPC)   │ │  - SIGINT/SIGTERM handlers + heartbeat│
│  - ComposedApp Wiring        │ │  - Scoped strict data loaders         │
└──────────────┬───────────────┘ └───────────────────┬───────────────────┘
               │                                     │
               └──────────────────┬──────────────────┘
                                  │
                                  ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      Shared Core Domain Services                       │
│                      (pypost.core.*, pypost.models.*)                  │
│                                                                        │
│  - StorageManager & DaemonStorage (JSON collections / environments)    │
│  - ConfigManager & Settings (Strict / Defaults)                        │
│  - MCPServerRegistry & MCPServerManager (Uvicorn / Stdio tools)        │
│  - MetricsManager (Prometheus exporter)                                │
│  - TemplateService & Variable Resolution (Jinja2)                      │
│  - RequestManager & Request Execution Engine                           │
│                                                                        │
│  * Strict Constraint: Pure Python + PySide6.QtCore ONLY                │
│    Zero dependencies on PySide6.QtWidgets or pypost.ui                │
└────────────────────────────────────────────────────────────────────────┘
```

### Architectural Decoupling Invariants

To guarantee that headless daemon execution never crashes in displayless environments (e.g.,
containers or remote servers where `DISPLAY` and `WAYLAND_DISPLAY` are unset), the codebase
enforces strict architectural boundaries and import invariants:

1. **GUI Presentation Layer (`pypost.ui.*`, `pypost.main`)**:
   - Depends on `PySide6.QtWidgets`, `PySide6.QtGui`, and `PySide6.QtCore`.
   - Depends on `pypost.core.*` and `pypost.models.*`.
   - Never depended upon by headless daemon or core services.
2. **Headless Daemon Layer (`pypost.daemon`, `pypost.core.qt.daemon_runtime`)**:
   - Depends on `PySide6.QtCore` only.
   - Depends on `pypost.core.*` and `pypost.models.*`.
   - Strictly decoupled from `PySide6.QtWidgets` and `pypost.ui.*`.
3. **Core Domain Layer (`pypost.core.*`, `pypost.models.*`)**:
   - Depends on standard library, `pydantic`, `requests`, `mcp`, `prometheus_client`, and
     `PySide6.QtCore`.
   - **Invariant**: No module in `pypost.core` or `pypost.models` may import `PySide6.QtWidgets`,
     `PySide6.QtGui`, or any module within `pypost.ui`.
   - Core Qt helpers (specifically `EnvironmentStorageGateway.wait_idle()`) use
     `from PySide6.QtCore import QCoreApplication` to pump pending events rather than
     `QApplication`, ensuring no GUI platform plugins are initialized during storage sync.

### Headless Daemon Subsystem

Daemon mode runs within a minimal `QCoreApplication` event loop to maintain compatibility with Qt
Core thread signaling used by `MetricsManager` and `MCPServerRegistry`.

```text
CLI Arguments / Environment Variables / Platform Defaults
                          │
                          ▼
             pypost.core.daemon_config
             (resolve_daemon_paths)
                          │
                          ▼
            pypost.core.daemon_storage
             (strict snapshot loaders)
                          │
                          ▼
           pypost.core.qt.daemon_runtime
                   (DaemonRuntime)
                     │         │
        ┌────────────┴──┐   ┌──┴─────────────┐
        ▼               ▼   ▼                ▼
  QCoreApplication  Signals  MetricsManager  MCPServerRegistry
  (event loop)     (SIGINT)  (Prometheus)    (MCP Servers)
```

### Key Components

- **`pypost.main`**: Desktop GUI composition root and entry point. Sets up `QApplication`,
  creates `MainWindow`, initializes UI presenters, and starts the GUI event loop.
- **`pypost.__main__`**: Top-level package execution script delegating to `pypost.main:main`,
  enabling `python -m pypost`.
- **`pypost.daemon`**: Pure CLI entry point for headless service mode. Parses command-line flags,
  resolves configuration paths, registers `SIGINT` / `SIGTERM` handlers, sets up a 500 ms heartbeat
  timer to ensure Python signal processing on the Qt Core event loop, and starts `DaemonRuntime`.
- **`pypost.core.daemon_config`**: Pure Python path resolution and validation. Enforces independent
  precedence across collections and environments directories without relying on Qt or global state.
- **`pypost.core.daemon_storage`**: Strict snapshot loaders (`load_collections_snapshot_strict`,
  `load_environments_snapshot_strict`). Unlike desktop storage, daemon storage never creates missing
  explicit directories and returns immutable dictionary snapshots containing only the records
  required by enabled MCP servers.
- **`pypost.core.config_manager`**: Supports `load_config_strict()` to parse `settings.json` without
  falling back silently to default values when the file is malformed or unreadable.
- **`pypost.core.qt.daemon_runtime.DaemonRuntime`**: Qt Core lifecycle coordinator. Orchestrates
  strict configuration loading, storage snapshots, metrics server binding, and MCP registry startup.
  Tracks startup deadlines via a 10-second watchdog timer, coordinates fail-fast error handling, and
  executes idempotent teardown on shutdown.

## API / Usage

### Dual Distribution Execution Matrix

| Runtime Mode | Console Script | Module Launcher | Make Target | Display Server Required? |
| --- | --- | --- | --- | --- |
| **GUI Desktop** | `pypost` | `python -m pypost` | `make run` | Yes (X11 / Wayland / macOS / Windows) |
| **Headless Daemon** | `pypost-daemon` | `python -m pypost.daemon` | `make run-daemon` | No (`QCoreApplication` headless) |
| **Agent UI Sidecar** | `pypost-agent-ui-mcp` | `python -m pypost.agent.ui_actions_mcp` | `make run-agent-ui-mcp` | No (offscreen QPA) |

### GUI Desktop Execution

Launch the interactive desktop interface:

```bash
# Via installed console script
pypost

# Via Python module execution
python -m pypost

# Via Make
make run

# Direct script execution
PYTHONPATH=. python pypost/main.py
```

### Headless Daemon Execution

Launch the headless background services:

```bash
# Via installed console script
pypost-daemon [--collections-dir PATH] [--environments-dir PATH]

# Via Python module execution
python -m pypost.daemon [--collections-dir PATH] [--environments-dir PATH]

# Via Make
make run-daemon
```

### Daemon CLI Arguments

- `--collections-dir PATH`: Directory containing collection JSON files (`*.json`).
  Default: `$PYPOST_COLLECTIONS_DIR` or `<user_data_dir>/collections`.
- `--environments-dir PATH`: Directory containing `environments.json`.
  Default: `$PYPOST_ENVIRONMENTS_DIR` or `<user_data_dir>`.
- `-h`, `--help`: Show help message and exit.

### Daemon Exit Codes

- `0`: Clean shutdown triggered by `SIGINT` (Ctrl+C) or `SIGTERM`.
- `1`: Fatal error (configuration error, invalid directory, missing required record, bind conflict,
  startup timeout, or unexpected background service exit).

## Configuration

### Path Precedence Matrix

Storage paths for collections and environments are resolved completely independently:

1. **Explicit CLI Argument**: `--collections-dir` or `--environments-dir`.
2. **Environment Variable**: `PYPOST_COLLECTIONS_DIR` or `PYPOST_ENVIRONMENTS_DIR`.
3. **Default Platform Data Directory**: Platform-specific user data directory
   (`platformdirs.user_data_dir("pypost")`), where collections live in `collections/` and
   environments live in `environments.json`.

```text
Precedence Evaluation:
CLI Flag Present & Non-Empty?
    ├── YES ──► Use CLI path (must exist and be readable)
    └── NO  ──► Environment Variable Set & Non-Empty?
                    ├── YES ──► Use Environment path (must exist and be readable)
                    └── NO  ──► Use Default Path (auto-initialized if missing)
```

### Strict Directory Validation

- **Explicit Paths (CLI / Environment)**: Must already exist, be directories, and have read/execute
  permissions (`os.R_OK | os.X_OK`). Daemon mode never creates missing custom directories.
- **Default Paths**: If default platform directories do not exist, daemon mode initializes them
  safely (creating `collections/` and writing `[]` to `environments.json` if missing).
- **Settings Path**: Loaded strictly from the user config directory
  (`platformdirs.user_config_dir("pypost")`). Missing `settings.json` loads default settings, but
  malformed or unreadable settings raise `StrictConfigError` and abort startup.

### Snapshot Scoping & Privacy

Daemon storage performs scoped, strict loading:
- Only collection and environment records referenced by **enabled** MCP server configurations are
  loaded into memory.
- If a referenced record is missing, corrupted, or duplicated, startup fails immediately with a
  typed error identifying the affected server ID.
- Unreferenced corrupted records are skipped, emitting count-only diagnostic logs
  (`daemon_storage_records_skipped`) without logging file contents or secret keys.

## Packaging and Distribution Validation

### Wheel Entry Points Validation

PyPost packages both entry points into standard Python distribution packages via `pyproject.toml`
`[project.scripts]`:

```toml
[project.scripts]
pypost = "pypost.main:main"
pypost-daemon = "pypost.daemon:main"
pypost-agent-ui-mcp = "pypost.agent.ui_actions_mcp:main"
```

To prevent regressions in wheel distributions:
- `scripts/check_package_data.py` (`verify_entry_points`): Unpacks the built wheel archive and
  validates `.dist-info/entry_points.txt` to confirm that `[console_scripts]` includes both
  `pypost = pypost.main:main` and `pypost-daemon = pypost.daemon:main`.
- `tests/test_runtime_distribution_modes.py`: Automates verification of:
  1. `pyproject.toml` console script declarations for `pypost` and `pypost-daemon`.
  2. Direct module execution (`python -m pypost` and `python -m pypost.daemon`).
  3. Headless import isolation: ensures `PySide6.QtWidgets` and `pypost.ui` are never loaded in
     daemon execution.
  4. Wheel metadata validation matching expected entry point definitions.
- Verification targets:
  ```bash
  make check-package-data
  make test
  ```

## Troubleshooting

### Corrupt Storage Diagnostics

When a required collection or environment file is unreadable or malformed, the daemon logs
structured diagnostics to `stderr` and exits with status `1`:

```text
ERROR pypost.core.qt.daemon_runtime: daemon_data_failed kind=collections category=invalid_record affected_server_id=jira-server
ERROR pypost.core.qt.daemon_runtime: daemon_start_failed collections category=invalid_record affected_count=1
ERROR pypost.core.qt.daemon_runtime: daemon_fatal reason=configuration
```

Common diagnostic categories:
- `store_unavailable`: The directory or `environments.json` file is missing.
- `store_unreadable`: File permission or I/O error reading data.
- `invalid_record`: JSON syntax error or Pydantic validation error in a required record.
- `duplicate_id`: Two collection or environment records share the same identifier.
- `missing`: An enabled MCP server references an ID that is not present in storage.

### Port Conflicts

If the configured Prometheus metrics port or any MCP server port is already in use by another
process:
- For metrics port conflicts, the daemon logs `daemon_fatal reason=metrics_start_failed` and exits.
- For MCP server port conflicts, the daemon logs `daemon_fatal reason=mcp_failed instance_id=<id>`
  and performs a clean rollback of all other started services before exiting.

### Startup Timeout

The daemon enforces a 10-second startup deadline (`startup_timeout_ms = 10_000`). If metrics or any
enabled MCP server fails to signal ready state within this window, the daemon logs
`daemon_fatal reason=startup_timeout`, tears down running listeners, and exits with code `1`.

### Signal Handling & Graceful Termination

To stop a running daemon:
- Send `SIGINT` (Ctrl+C) or `SIGTERM` (`kill <pid>`).
- The signal handler sets `normal_termination = True` and calls `QCoreApplication.quit()`.
- `aboutToQuit` triggers `DaemonRuntime.shutdown()`, which:
  1. Stops all running MCP server uvicorn instances via `MCPServerRegistry.stop_all()`.
  2. Stops the Prometheus HTTP listener via `MetricsManager.stop_server()`.
  3. Disarms all active timers.
- The process restores original signal handlers and exits cleanly with status code `0`.
