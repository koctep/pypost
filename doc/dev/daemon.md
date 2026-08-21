# Headless Daemon Mode (PYPOST-1046)

## Overview

PyPost headless daemon mode runs the configured background services (Prometheus metrics and enabled
MCP servers) without initializing a graphical user interface or requiring a display server (such as
X11 or Wayland). It enables server deployments, container workloads, CI runners, and background
agent services.

The entry point is decoupled from the desktop Qt Widgets application (`pypost/main.py`), avoiding
unnecessary widget allocations, desktop UI settings persistence, or offscreen window emulation.

## Architecture

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

- **`pypost.daemon`**: Pure CLI entry point. Parses command-line flags, resolves configuration
  paths, registers `SIGINT` / `SIGTERM` handlers, sets up a 500 ms heartbeat timer to ensure Python
  signal processing on the Qt Core event loop, and starts `DaemonRuntime`.
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

### Console Script & CLI

When PyPost is installed into a Python environment, the console script `pypost-daemon` is available:

```bash
pypost-daemon [--collections-dir PATH] [--environments-dir PATH]
```

### Module Execution

```bash
python -m pypost.daemon [--collections-dir PATH] [--environments-dir PATH]
```

### Make Target

```bash
make run-daemon
```

### CLI Arguments

- `--collections-dir PATH`: Directory containing collection JSON files (`*.json`).
  Default: `$PYPOST_COLLECTIONS_DIR` or `<user_data_dir>/collections`.
- `--environments-dir PATH`: Directory containing `environments.json`.
  Default: `$PYPOST_ENVIRONMENTS_DIR` or `<user_data_dir>`.
- `-h`, `--help`: Show help message and exit.

### Exit Codes

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
