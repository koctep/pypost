# Multiple MCP Servers

## Overview

PYPOST-1044 replaces the application-owned mutable MCP endpoint with persisted,
independent MCP server configurations. Each configuration selects exactly one
collection and one environment, binds to its own port, and owns an independent
runtime. This lets separate MCP clients use different tool catalogs and
credentials at the same time.

The primary developer entry point is `MCPServerRegistry` in
`pypost/core/mcp_server_registry.py`. The legacy `MCPServerManager` remains
the single-endpoint transport primitive used by each registry row; it is no
longer the owner of the application-wide multi-server lifecycle.

## Architecture

`McpServerSettingsController` (`pypost/ui/mcp_server_controller.py`, PYPOST-1071)
constructs the registry with ID-based collection and environment lookups, then
loads persisted rows before asynchronous collection and environment loading
starts. `MainWindow` composes that controller and keeps only the readiness
gate: once both sources are ready it calls `mcp_controller.start_enabled()`,
which starts every row with `enabled=True`. Startup is best-effort: a missing
reference or bind failure marks that row failed and does not interrupt another
endpoint.

For each started row the registry creates one `MCPServerManager`, which in turn
owns one `MCPServerImpl`, activity log, uvicorn server, and background thread.
Before starting it, the registry deep-copies the selected collection requests
and snapshots the selected environment variables and hidden keys. A later
change in the environment selector therefore cannot retarget a running
endpoint.

```text
AppSettings.mcp_servers
        |
        v
MCPServerRegistry -- one runtime per configuration --> MCPServerManager
        |                                            --> MCPServerImpl
        +-- collection/environment ID lookup + copied snapshots
```

`McpControlsPresenter` (`pypost/ui/presenters/mcp_controls_presenter.py`,
PYPOST-1071) owns the **MCP Servers…** entry point; `EnvPresenter` only hosts
its widgets in the environment bar. The top-bar status is an aggregate
running/failed count, while the dialog presents row-specific state, endpoint,
collection, environment, activity, and scoped tool overview.

### Library-backed local servers

A local server may select a workspace collection or a collection from a
connected library. The library path is not the row identity. The persisted
selection is the tuple `library_id`, `manifest_id`, and
`library_collection_path`; the manifest index is display metadata.
`McpServerSettingsController` resolves that tuple through
`LibraryManagerService` and re-reads the current connection and manifest
before accepting a save. A disconnected library, changed manifest, or stale
collection path produces a categorized validation error instead of silently
switching to another collection.

`LibraryMcpSourcePicker` performs connected-library and manifest collection
discovery through cancellable workers. `_McpServerEditor` invalidates the
active request when the dialog is cancelled or the source changes, so a late
worker result cannot repopulate a different library selection. The editor also
exposes the selected library profile and declared typed variables. Values are
handed to the controller as a local overlay draft; secret fields are masked
and their values are never written to logs or documentation.

Library variable resolution is documented in
[Library Manifest and Local Overlay](library_manifest_and_overlay.md). For an
MCP row, effective values are layered from manifest and collection defaults,
the active manifest/collection profile, local non-secret overrides, and local
secrets, in that order of increasing precedence. A normal workspace
`Environment.id` remains the row's `environment_id`; it is not required to be
the name of a library preset. Workspace environment variables are used when
that ID is selected, while an overlay profile can further specialize the
library selection. Declared secret variables, overlay secrets, and workspace
hidden keys are included in runtime masking.

The controller saves a library row through `LibraryMcpSaveTransaction`. The
checked settings store verifies serialized settings and overlay writes, uses a
journal and durable backups for recovery, and restores both previous snapshots
if registry installation or persistence fails. The registry validates the
candidate runtime before installing it, so a failed save does not leave a
partially installed row. Normal workspace rows and upstream proxy rows retain
their existing save and runtime paths; library-only identity and overlay logic
is not applied to them.

#### Planned Variable Setup Wizard (PYPOST-1284)

Epic [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284) enhances library variable
configuration in `_McpServerEditor` with a dedicated setup wizard and rich guidance:
- `CollectionVariable.help_text` schema extension ([PYPOST-1372](https://pypost.atlassian.net/browse/PYPOST-1372)).
- Expandable `VariableGuidanceCard` and `VariableSetupWizardDialog` components ([PYPOST-1373](https://pypost.atlassian.net/browse/PYPOST-1373)).
- Wizard launch and overlay persistence in `_McpServerEditor` ([PYPOST-1374](https://pypost.atlassian.net/browse/PYPOST-1374)).
- Reference collection fixtures with OAuth guidance and contract tests ([PYPOST-1375](https://pypost.atlassian.net/browse/PYPOST-1375)).

#### Variable Setup Wizard & Guidance Card Components (PYPOST-1373)

Story [PYPOST-1373](https://pypost.atlassian.net/browse/PYPOST-1373) implements the UI component
layer for interactive variable configuration under `pypost/ui/variable_setup_wizard_dialog.py`:

##### `VariableGuidanceCard`

A reusable `QFrame` widget rendering input, guidance, and validation states for a single `CollectionVariable`.

- **Visual Header**: Displays variable name, type badge (e.g. `[string]`, `[integer]`), and a `* Required` indicator in warning red when `variable.required=True`. An optional brief `variable.description` is shown as muted label text.
- **Input Field**: A `QLineEdit` pre-populated from `initial_value`, falling back to `variable.default`, or empty string.
- **Secret Masking & Eye Toggle**: When `variable.secret=True`, `input_field` initializes with `QLineEdit.EchoMode.Password`. A companion `QToolButton` ("Show" / "Hide", widget ID `pypost_variable_guidance_secret_toggle`) allows toggling echo mode between `Password` and `Normal` so users can inspect sensitive credentials without shoulder-surfing exposure.
- **Expandable Guidance**: When `variable.help_text` is populated, a toggle button ("Show Guidance" / "Hide Guidance", widget ID `pypost_variable_guidance_expand_button`) controls visibility of a collapsible instructions container. The panel renders rich text / HTML instructions via `QLabel` with `openExternalLinks=True`, allowing users to open documentation or OAuth token generation URLs directly in their browser. If `help_text` is absent or empty, the toggle button and container are omitted for a compact card display.
- **Validation & Visual Feedback**: `is_valid()` checks whether required variables have non-empty text. `set_validation_error(msg)` displays an inline error label in red and applies a red border to the input field (`QLineEdit { border: 1px solid #e74c3c; }`). Error indicators automatically clear when the user edits text (`textChanged` signal).

##### `VariableSetupWizardDialog`

A modal `QDialog` (widget ID `pypost_variable_setup_wizard_dialog`) hosting a scrollable sequence of `VariableGuidanceCard` widgets.

- **Instantiation**: Downstream callers instantiate the wizard by passing a list of `CollectionVariable` models, optional existing values dictionary (`initial_values: dict[str, Any]`), and an optional collection display name:
  ```python
  from pypost.models.collection_variable import CollectionVariable
  from pypost.ui.variable_setup_wizard_dialog import (
      VariableSetupWizardDialog,
  )

  dialog = VariableSetupWizardDialog(
      variables=collection.variables,
      initial_values={"WORKSPACE_ID": "ws-123"},
      collection_name=collection.name,
      parent=editor_widget,
  )
  if dialog.exec() == QDialog.DialogCode.Accepted:
      resolved_values = dialog.get_values()
      configured = dialog.get_configured_variables()
      # configured["values"]: dict[str, Any] -> all values
      # configured["overrides"]: dict[str, Any] -> non-secret overrides
      # configured["secrets"]: dict[str, Any] -> secret credentials
  ```
- **Scroll Container**: Contains cards inside a `QScrollArea(widgetResizable=True)` to comfortably handle collections with numerous variables.
- **Validation on Accept**: Clicking "Save" (`VARIABLE_SETUP_APPLY_BUTTON`) invokes `accept()`, which triggers `validate_all()`. If any required card is empty, validation error cues are highlighted on the offending card(s) and dialog acceptance is prevented until all required fields are satisfied.
- **Value Extraction**:
  - `get_values() -> dict[str, Any]`: Returns a flattened dictionary mapping variable names to user-entered values. Automatically coerces integer and number types where applicable.
  - `get_configured_variables() -> dict[str, dict[str, Any]]`: Returns a partitioned payload with `"values"`, `"overrides"` (non-secrets for settings storage), and `"secrets"` (sensitive credentials for secure overlay storage).
- **Test Automation Identifiers**: All interactive components are registered in `pypost/ui/widget_ids.py` (`VARIABLE_SETUP_WIZARD_DIALOG`, `VARIABLE_GUIDANCE_CARD`, `VARIABLE_GUIDANCE_EXPAND_BUTTON`, `VARIABLE_GUIDANCE_SECRET_TOGGLE`, `VARIABLE_SETUP_APPLY_BUTTON`, `VARIABLE_SETUP_CANCEL_BUTTON`).

#### MCP Server Editor Wizard Integration (PYPOST-1374)

Story [PYPOST-1374](https://pypost.atlassian.net/browse/PYPOST-1374) (under parent epic [PYPOST-1284](https://pypost.atlassian.net/browse/PYPOST-1284)) integrates `VariableSetupWizardDialog` into `_McpServerEditor` in `pypost/ui/dialogs/mcp_servers_dialog.py`, enabling interactive configuration and local overlay persistence for library-backed MCP servers:

##### "Configure Variables…" Action Button

- **Widget Identification**: The action button is registered as `_ConfigureVariablesButton` with automation ID `MCP_SERVER_CONFIGURE_VARIABLES_BUTTON` (`pypost_mcp_server_configure_variables_button`) in `pypost/ui/widget_ids.py` and included in `KEY_WIDGET_IDS`.
- **Placement**: Embedded directly below the library variables form layout in `_McpServerEditor`.
- **Visibility and Enablement Lifecycle**: Governed by `_update_configure_variables_button_state()`. The button and its layout row label are dynamically shown and enabled if and only if:
  1. The server type is `local` (`self._server_type.currentData() == "local"`),
  2. The collection source is `library` (`self._collection_source.currentData() == "library"`), and
  3. The currently selected collection declares at least one variable (`manifest_variables` is non-empty).
  If the source switches away from library (e.g. to `workspace` or `builtin`), or the selected library collection defines no variables, the button is hidden and disabled. State is evaluated whenever server type, collection source, or library collection selections change.

##### Wizard Launch and Pre-population Flow

When the user clicks "Configure Variables…" (`_on_configure_variables_clicked()`):
1. **Manifest Parsing**: Deserializes raw collection variables from `selection.get("manifest_variables", [])` into `CollectionVariable` models, supporting legacy `default_value` mappings.
2. **Initial Values Hierarchy**: Merges active configuration state in order of precedence:
   - Selected active profile values (`manifest_profiles[active_profile]`),
   - Manifest default fallbacks (`var.default`),
   - Draft overlay non-secret overrides (`_library_overlay["overrides"]`),
   - Draft overlay secrets (`_library_overlay["secrets"]`),
   - Any uncommitted inline text currently entered in `_library_variable_fields`.
3. **Modal Dialog Launch**: Instantiates `VariableSetupWizardDialog` via the `_create_variable_wizard` factory seam, logging operational launch metadata (`mcp_server_editor_wizard_launched`), and executes it modally via `_launch_variable_wizard(dialog)`.

##### Acceptance, Synchronization, and Cancellation Semantics

- **Modal Acceptance (`QDialog.DialogCode.Accepted`)**:
  - Extracts partitioned results via `dialog.get_configured_variables()`, containing:
    - `"values"`: All resolved variables.
    - `"overrides"`: Non-secret variable overrides.
    - `"secrets"`: Sensitive credentials.
  - Invokes `_sync_wizard_results_to_overlay(result)`:
    - Merges `overrides` into `self._library_overlay["overrides"]`.
    - Merges `secrets` into `self._library_overlay["secrets"]`.
    - Synchronizes matching inline editor fields (`_library_variable_fields[name].setText(...)`). Secret fields remain masked via password echo mode.
  - Logs safe operational counts (`mcp_server_editor_wizard_applied` with `configured_count`, `overrides_count`, `secrets_count`), ensuring zero credential or payload leakage.
- **Modal Cancellation (`QDialog.DialogCode.Rejected`)**:
  - Discards changes made in the wizard, preserving all existing draft overlay state and inline field values intact.
  - Emits `mcp_server_editor_wizard_cancelled` operational log.
- **Persistence Pipeline**:
  - On editor save (`_accept_if_complete()`), `library_handoff()` produces an overlay candidate from `_library_overlay` and inline fields, validated through `LibraryRuntimeResolver.prepare_environment(...)`.
  - Routed through `McpServerSettingsController.save_library_server(...)`, which persists the validated `LocalLibraryOverlay` to `~/.pypost/overlays/{library_id}.json`.

##### Headless Test Seams

To ensure fast, deterministic UI unit testing without hanging on modal Qt event loops:
- `_create_variable_wizard(variables, initial_values, collection_name) -> VariableSetupWizardDialog`: Factory method hook for creating the wizard dialog instance.
- `_launch_variable_wizard(dialog) -> int`: Invocation hook delegating to `dialog.exec()`. In unit test suites (such as `tests/test_mcp_servers_dialog_variable_wizard_repro.py`), tests mock `_launch_variable_wizard` to simulate `Accepted` or `Rejected` return codes and inspect pre-populated parameters without displaying native modal windows.

#### Live Wire IPC and Stdio Transport Stress Testing (PYPOST-1416)

While in-process unit tests validate tool schema registration and Python supplier dispatches, they bypass the physical operating system networking stack, socket buffers, kernel pipe buffers, and wire framing. Story [PYPOST-1416](https://pypost.atlassian.net/browse/PYPOST-1416) introduces comprehensive live wire IPC and stdio transport stress testing in `tests/test_mcp_standalone_wire_ipc_repro.py`, verifying standalone MCP server implementations under real-world physical wire and pipe conditions. See [mcp_standalone_wire_ipc_stress.md](mcp_standalone_wire_ipc_stress.md) for dedicated reference architecture and failure mode details.

##### Wire-Level Socket Communication

Standalone MCP servers expose two primary HTTP-based wire transports:
1. **Streamable HTTP (`/mcp`)**: Mounted via `mcp.server.streamable_http_manager.StreamableHTTPSessionManager`. Handles JSON-RPC 2.0 requests over HTTP `POST` requests and maintains session state via the `mcp-session-id` header.
2. **Server-Sent Events (`/sse` & `/sse/messages`)**: Mounted via `mcp.server.sse.SseServerTransport`. Establishes persistent server-to-client streaming via HTTP `GET /sse` and routes client JSON-RPC requests via `POST /sse/messages?session_id=...`.

The wire stress harness introduces `RawTcpWireClient` (`tests/helpers/raw_tcp_client.py`,
promoted from `tests/test_mcp_standalone_wire_ipc_repro.py`), a low-level socket client
operating directly on raw TCP streams (`socket.AF_INET`, `socket.SOCK_STREAM`) against the
loopback interface (`127.0.0.1`):
- Transmits raw HTTP/1.1 wire frames with `POST /mcp`, `Host`, `Content-Type: application/json`, `Accept: application/json, text/event-stream`, `Connection: keep-alive`, and `mcp-session-id`.
- Reassembles raw byte streams into status lines, headers, and bodies, handling both fixed `Content-Length` framing and chunked HTTP transfer encoding (`Transfer-Encoding: chunked`).
- Decodes incoming JSON-RPC 2.0 payloads from direct JSON responses and Server-Sent Event (`data: {...}`) blocks.

##### Packet Fragmentation Resilience

In production environments, TCP delivers data as an arbitrary stream of bytes rather than discrete packet boundaries (governed by MTU, Nagle's algorithm, and socket buffers). The wire test harness verifies server resilience against severe packet fragmentation:
- **Header and Body Boundary Splits**: Splits HTTP request headers and JSON-RPC bodies across arbitrary multi-byte boundaries (e.g. 7-byte chunks).
- **1-Byte Micro-Chunking**: Transmits tool call payloads (`tools/call`) byte-by-byte (`send_fragmented(chunk_size=1)`), simulating extreme MTU fragmentation or sluggish network interfaces.
- **Chunked Stream Reassembly**: Exercises Uvicorn/Starlette ASGI request stream parsers, verifying that fragmented frames and chunked SSE streams are reassembled without protocol desynchronization, incomplete reads, or frame dropouts.

##### Pipelined Burst Throughput

To ensure high-throughput agent workflows operate without socket stalls:
- **100-Request Pipelined Bursts**: A client generates and concatenates 100 complete HTTP/JSON-RPC tool execution requests (`pipelined-0` through `pipelined-99`) and transmits them in a single bulk `sendall()` socket write over a single persistent TCP keep-alive connection.
- **Continuous Stream Processing**: Verifies that the ASGI application and `MCPServerImpl` process queued requests continuously, returning exactly 100 sequential HTTP 200 responses with matched request IDs.
- **Zero Stall Guarantees**: Asserts absence of connection resets (`ECONNRESET`), socket deadlocks, or dropped frames under burst saturation.

##### OS Pipe Stdio IPC and Buffer Deadlock Avoidance

In addition to socket transports, standalone MCP servers support out-of-process execution over OS standard input/output (`stdio`) pipes via `mcp.server.stdio.stdio_server`:
- **Subprocess Model**: Launched as an independent OS process via `subprocess.Popen([sys.executable, "-c", ...], stdin=PIPE, stdout=PIPE, stderr=PIPE, bufsize=0)`.
- **The 64KB `PIPE_BUF` Deadlock Risk**: On Linux, operating system pipes have fixed buffer capacities (typically 64KB / 65,536 bytes). If a client writes a burst of requests or a large payload (>64KB) to `stdin` while synchronously waiting for responses, or if the server produces large responses while the client is blocked on writing, both processes will deadlock indefinitely on full kernel pipe buffers.
- **Concurrent Non-Blocking Drainer Threads**: The test harness runs concurrent background worker threads (`stdout_worker` and `stderr_worker`) that continuously drain `process.stdout` and `process.stderr` using line iterators and non-blocking locks.
- **Large Payload Stress**: Stresses the stdio pipe with a 50-request burst containing payloads exceeding 70KB (surpassing the 64KB OS pipe buffer limit). Verifies that large responses are received without corruption, truncation, or deadlocks.
- **Clean Lifecycle on Stdin EOF**: Closing `process.stdin` signals EOF to `stdio_server`, ensuring orderly event loop termination and process exit with code 0 without orphaned zombie processes.

##### Port Re-Binding and Socket Lifecycle Teardown

Improper socket cleanup can hold TCP ports in `TIME_WAIT` or leak file descriptors, preventing servers from restarting:
- **Active Hammer Load**: Simulates rapid concurrent connections from multiple background threads hammering `POST /mcp` requests while the server is active.
- **Rapid Teardown Under Load**: Invokes `manager.stop_server()` while hammer traffic is in flight.
- **Immediate Port Re-Binding**: Verifies that the server cleanly shuts down its Uvicorn worker thread and releases listening sockets, enabling immediate re-binding on the exact same port with `SO_REUSEADDR` without encountering `EADDRINUSE`.
- **Successor Instance Startup**: Immediately instantiates and starts a second `MCPServerManager` on the identical port, asserting full readiness.

#### Concurrent Server Teardown and Parallel Cleanup Support (PYPOST-1434)

When terminating multiple MCP servers—such as during test suite teardown, fixture cleanup, or
application shutdown—stopping instances sequentially introduces cumulative latency, where each
server join timeout can take up to 1.0s or more. Story
[PYPOST-1434](https://pypost.atlassian.net/browse/PYPOST-1434) upgrades `MCPServerRegistry.stop()`
and `MCPServerRegistry.stop_all()` to execute concurrent shutdowns with bounded parallelism and
isolated error handling.

##### Lock Scope Narrowing in `MCPServerRegistry.stop()`

Previously, `MCPServerRegistry.stop()` held the internal `_reconfiguration_lock` across the entire
call to `manager.stop_server()`. Because `stop_server()` halts uvicorn worker event loops and
performs blocking thread joins (`thread.join(timeout=...)`), holding `_reconfiguration_lock`
completely serialized multi-server teardowns and created contention when multiple threads or
workers attempted concurrent stops.

Under PYPOST-1434, the lock window in `MCPServerRegistry.stop(instance_id)` is strictly narrowed:
1. `_reconfiguration_lock` is acquired only to mutate registry state:
   - Pops pending candidate managers from `_pending_reconfigurations`.
   - Fetches the active `MCPServerManager` reference from `_managers`.
   - Transitions instance status to `"stopped"` via `_set_status()`.
2. The lock is released immediately after extracting manager references.
3. Actual server stopping (`pending.candidate_manager.stop_server()` and `manager.stop_server()`)
   and worker thread joins are executed outside `_reconfiguration_lock`.

This critical narrowing enables multiple worker threads to execute `stop()` concurrently without
blocking on registry locks during shutdown joins.

##### Concurrent Teardown in `MCPServerRegistry.stop_all()`

`MCPServerRegistry.stop_all(*, timeout: float = 10.0, max_workers: int | None = None) -> None`
provides bounded parallel teardown across all registered, manager-backed, and pending instances:

- **Target Discovery**: Under `_reconfiguration_lock`, computes the unique union of instance IDs
  from `_managers`, `_pending_reconfigurations`, and `_configurations`.
- **Bounded Worker Pool**: Uses a `concurrent.futures.ThreadPoolExecutor` bounded by
  `worker_count = min(len(target_ids), 16) if max_workers is None else max(1, max_workers)`. This
  prevents thread exhaustion while allowing fully concurrent shutdown of standard test fixtures.
- **Join Timeout**: Submits worker tasks (`_worker_stop`) and awaits completion via
  `concurrent.futures.wait(futures, timeout=timeout)`. If the timeout expires before all workers
  complete, a warning is logged (`mcp_registry_concurrent_teardown_timed_out`) and the executor is
  terminated with `shutdown(wait=False, cancel_futures=True)` to prevent hanging test suites or
  application exit.
- **Per-Worker Exception Isolation**: Each worker wraps `self.stop(instance_id)` in exception
  handling, recording errors in a thread-safe `errors` dictionary and logging
  `mcp_registry_concurrent_teardown_error` with full stack traces. An unhandled exception or crash
  in one server manager never prevents remaining servers from stopping.

#### Structured Errno Normalization and OS Port Preflight Error Classification (PYPOST-1436)

Previously, server bind error detection in `pypost/core/server_bind.py` relied on
locale-fragile substring inspection (e.g. `"address already in use"` in `str(exc).lower()`),
which broke on non-English locales (such as German `"Die Adresse wird bereits verwendet"` or
French `"Adresse déjà utilisée"`). Furthermore, preflight OS port validation was hardcoded to
IPv4 (`socket.AF_INET`), failing on IPv6 addresses like `::1` or `[::1]`.

Story [PYPOST-1436](https://pypost.atlassian.net/browse/PYPOST-1436) formalizes structured errno
normalization across POSIX, BSD/macOS, and Windows Winsock platforms, introduces multi-family
IPv4/IPv6 address detection and socket preflight probing, and removes all substring matching:

##### `BindErrorClassification` and Platform Errno Mapping

`BindErrorClassification` (`pypost/core/server_bind.py`) is an enumeration representing canonical
OS networking bind error categories:
- `PORT_IN_USE`: Port is actively bound by another process or held in socket state.
- `ADDRESS_NOT_AVAILABLE`: Host interface/IP address cannot be assigned on the host system.
- `PERMISSION_DENIED`: Process lacks privileges to bind (e.g. privileged ports `< 1024` on UNIX).
- `UNCLASSIFIED`: Any unmapped or generic socket error.

Errno normalization is maintained via frozen integer sets covering POSIX, BSD/macOS, and
Windows Winsock (WSA) error codes:
- `ERRNO_PORT_IN_USE`: `errno.EADDRINUSE` (98 on Linux), 48 (BSD/macOS), and 10048
  (`WSAEADDRINUSE`).
- `ERRNO_ADDR_NOT_AVAIL`: `errno.EADDRNOTAVAIL` (99 on Linux), 49 (BSD/macOS), and 10049
  (`WSAEADDRNOTAVAIL`).
- `ERRNO_PERMISSION_DENIED`: `errno.EACCES` (13), `errno.EPERM` (1), and 10013 (`WSAEACCES`).

##### Numeric Errno Extraction via `extract_errno`

Because Python socket exceptions and OS errors can package error codes differently across
operating systems and Python runtime versions, `extract_errno(exc: BaseException) -> int | None`:
1. Inspects standard `exc.errno` if it is an `int`.
2. Inspects Windows-specific `exc.winerror` if present.
3. Falls back to inspecting `exc.args[0]` if integer, or unpacking nested socket error tuples
   `exc.args[0][0]` (common in legacy C-extension socket exceptions).
4. Returns `None` if no numeric error code can be extracted.

`classify_bind_error(exc: BaseException) -> BindErrorClassification` maps the extracted errno
against the frozen sets, returning `BindErrorClassification.UNCLASSIFIED` on unknown codes or
`None`.

##### Multi-Family IPv4/IPv6 Address Detection and Preflight Probing

`MCPServerRegistry._validate_os_port` and background server startup utilize:
- `detect_address_family(host: str) -> socket.AddressFamily`: Parses literal IPv4 and IPv6
  strings (supporting bracketed IPv6 notation like `[::1]`) using `ipaddress.ip_address`. If
  parsing as an IP literal fails (for hostnames), detects `:` to classify IPv6 addresses or falls
  back to `socket.AF_INET`.
- `validate_host_and_port(host: str, port: int) -> None`: Probes candidate endpoints prior to
  stopping active servers or launching services. Creates a temporary stream socket with the
  detected address family, applies `SO_REUSEADDR` (where available), and performs a test
  `probe.bind(...)`. If bind fails with an `OSError`, it classifies the failure and raises
  `ValueError` with structured diagnostic details while preserving exception provenance
  (`from exc`).

##### Locale-Resilient `format_bind_error` and Signature Compatibility

`format_bind_error` eliminates substring matching and renders user-facing diagnostics based
exclusively on `classify_bind_error`. It maintains dual-argument signature compatibility across
call sites:
- Modern/legacy order: `(exc, host, port, server_label="server")`
- Inverse order: `(host, port, exc, server_label="server")`
- Keywords: `server_name` / `server_label`

##### Verification Test Suite

Run unit and integration tests verifying structured errno classification and preflight probing:

```bash
make test PYTEST_ARGS="tests/test_server_bind_errno.py"
```

## Configuration and lifecycle

`AppSettings.mcp_servers` is a list of `McpServerConfiguration` objects saved
to the normal PyPost `settings.json`. A row contains:

| Field | Meaning |
| --- | --- |
| `id` | Stable instance identity used by the registry and UI. |
| `name` | Optional display label. |
| `host`, `port` | Endpoint bind address. Ports must be unique across all rows, even with different hosts. |
| `collection_id` | The only collection whose exposed requests become tools for this endpoint. |
| `environment_id` | The environment snapshot used by this endpoint's tool calls. |
| `enabled` | Starts the row after collections and environments have loaded on the next session; **Start** sets it, **Stop** clears it. |

Use `McpServersDialog` through `McpControlsPresenter` for normal changes. Its
Add and Edit forms validate the selected collection, environment, port range,
and global configured-port uniqueness. `McpServerSettingsController` persists a
non-running edit immediately. For a running endpoint it calls
`MCPServerRegistry.reconfigure()`: the replacement endpoint must start
successfully before its persisted configuration replaces the old one. If it
cannot bind, the old endpoint remains available (or is restarted for a
same-address replacement) and the edit is not persisted.

The registry API is intentionally per-instance:

```python
registry.upsert(configuration)       # validate and store a configuration
registry.start(instance_id)          # start only this endpoint
registry.stop(instance_id)           # stop only this endpoint
registry.reconfigure(instance_id, configuration)
registry.remove(instance_id)
registry.refresh_collection(collection_id)
registry.refresh_environment(environment_id)
registry.stop_all(timeout=10.0, max_workers=None)  # concurrent application/test shutdown
```

`refresh_collection()` updates only servers selected for that collection;
`MCPServerManager.update_tools()` may restart only those endpoint(s) when the
tool signature changed; the restart path waits until the prior host/port is
probe-bindable before starting again, retaining the worker thread ref if stop’s
join times out (PYPOST-1178 / PYPOST-1196; see
[MCP Integration](mcp_integration.md)). `refresh_environment()` replaces the
variables and hidden-key suppliers only for servers that selected that
environment.
`reconcile_references()` stops and marks only rows whose persisted collection
or environment was deleted.

## Legacy migration

The old `Environment.enable_mcp` plus global `mcp_host` / `mcp_port` setting
is retained only as an explicit migration input. It does not automatically
start a multi-server endpoint. When the selected legacy environment has
`enable_mcp=True`, **MCP Servers…** offers **Convert current legacy MCP
setting…**. The form preselects that environment and the legacy host/port; the
user must select a collection and save a new explicit row. Conversion does not
change the legacy environment toggle.

## Observability

Registry lifecycle logs include only stable operational context:
`instance_id`, `port`, lifecycle state, and whether a message exists. They do
not log collection names, environment values, hidden keys, credentials, or
request payloads. Failed transactional replacements emit a warning with the
attempted port and reason.

The registry covers the endpoint **runtime**; `McpServerSettingsController`
covers **persistence** — `mcp_persisted_servers_loaded` at startup,
`mcp_servers_persist_requested reason=…` before every settings write, and
`mcp_server_reconfigure_finished instance_id=… committed=…` for the
transactional path (`committed=false` means the edit was rolled back and not
persisted). Both sets emit counts and opaque instance IDs only; the full
catalog is in [logging.md](logging.md#mcp).

`mcp_server_instances{state}` is the aggregate count of configured rows in
`stopped`, `starting`, `running`, and `failed` state. The label set is fixed;
instance IDs, ports, collection IDs, and environment IDs are intentionally not
metric labels. The existing `mcp_server_up` compatibility gauge remains true
while at least one registry endpoint is running. Request counters and duration
histograms remain aggregate; inspect the selected dialog row for its activity.

Library-specific discovery, validation, and save events use bounded operation,
outcome, and category labels. The Prometheus and optional OpenTelemetry
trackers expose `mcp_library_discovery_total`, discovery duration and item
histograms, `mcp_library_validation_total`, and save outcome and duration
histograms. Logs include stable IDs, safe categories, counts, and durations;
they exclude environment values, secret values, request payloads, and
filesystem paths. See [PYPOST-1280 observability](../../ai-tasks/PYPOST-1280/50-observability.md)
for the metric contract.

## Troubleshooting

| Symptom | Check / resolution |
| --- | --- |
| A row is `failed` after startup | Verify its selected collection and environment still exist, then resolve the dialog's error and start that row again. Other rows should stay available. |
| Add or edit rejects a port | Each configured row reserves its port globally. Choose a unique port; a running-row reconfiguration also checks whether the OS can bind it. |
| One client sees unexpected tools | Open **MCP Servers…**, select that endpoint, and use **Tools…**. Verify its collection selection and that requests are marked as MCP tools. |
| An edit did not take effect | A running endpoint is persisted only after its replacement binds. Inspect the row state/error; the previous endpoint is retained on replacement failure. |
| Environment changes do not affect a different server | This is expected. A server receives only the snapshot for its configured environment; edit/select that row's environment instead. |
| A library selection is rejected | Reopen the editor and refresh connected libraries. Check that the connection, manifest ID, collection path, and selected workspace Environment ID still exist. The editor intentionally does not substitute a different collection or profile. |
| A library discovery result is missing | Check whether the dialog was cancelled or the source/library changed while the worker was running. Cancelled or stale results are discarded; start discovery again. |
| Library variables are unavailable at runtime | Supply required values through the selected profile, local override, or local secret field. Secret values are masked in the UI and stored only in the local overlay. |

For comprehensive multi-server concurrency, variable isolation, hot reload, and port contention contracts, see [Concurrent Multi-Server Lifecycle Execution and Port Contention](mcp_concurrent_multiserver.md).

Run the focused checks after changing this subsystem:

```bash
make test PYTEST_ARGS='tests/test_server_bind_errno.py tests/test_mcp_server_registry.py tests/test_mcp_servers_dialog.py tests/test_mcp_servers_dialog_variable_wizard_repro.py tests/test_mcp_standalone_wire_ipc_repro.py tests/test_mcp_concurrent_multiserver_repro.py tests/test_mcp_concurrent_teardown.py'
```

