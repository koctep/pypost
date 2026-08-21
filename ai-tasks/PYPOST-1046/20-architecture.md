# PYPOST-1046: Headless daemon launch architecture

## Research

### Repository findings

- `pypost/main.py` is the desktop composition root. `main()` always constructs
  `QApplication`, composes `MainWindow`, shows it, and blocks in the widget event loop.
- `compose_app()` is intentionally UI-shaped: it creates history, storage, request, metrics,
  alert, and MCP collaborators and returns a `MainWindow`. Reusing it would create the GUI that
  daemon mode must avoid.
- `MainWindow` loads collections and environments asynchronously through presenters. Only after
  both presenter signals arrive does it call `McpServerSettingsController.start_enabled()`.
- `McpServerSettingsController` is under `pypost/ui/`. It loads persisted MCP rows and delegates
  runtime ownership to `MCPServerRegistry`; daemon code must not depend on that UI controller.
- `MCPServerRegistry` already owns one `MCPServerManager` per persisted row, isolates collection
  and environment snapshots, reports per-row state, and stops all managers. It can be reused with
  lookup functions backed by daemon-loaded dictionaries.
- `MCPServerManager` and `MetricsManager` depend on Qt Core objects and run uvicorn in bounded-join
  background threads. They do not require widgets, but their signals need a Qt event loop for
  deterministic main-thread delivery.
- `StorageManager` currently derives `collections/` and `environments.json` from one data root,
  creates missing paths, and has tolerant loaders intended for the desktop. Daemon startup needs
  independent directories and strict, non-mutating load outcomes.
- `ConfigManager.load_config()` logs malformed settings and returns defaults. That is safe for the
  desktop but would let a daemon hide a configuration failure, so daemon startup needs a strict
  read path without changing the existing method.
- The package has one console entry point, `pypost-agent-ui-mcp`, and the Makefile has separate
  `run` and `run-agent-ui-mcp` targets. There is no general `pypost` command to extend safely.
- Existing command tools use `argparse`, accept `argv` for tests, resolve `Path` values, write
  diagnostics to stderr, and return integer process outcomes.
- `pypost.agent.AgentAppSession` is not a daemon substitute: it intentionally creates and shows an
  offscreen `QApplication`/`MainWindow` for UI automation and uses temporary data by default.

### Official references and conclusions

- Python documents [`argparse`](https://docs.python.org/3.11/library/argparse.html) as its standard
  basic command-line parser; `parse_args()` can consume an injected argument list. Use it for a
  small testable daemon entry point instead of adding a dependency.
- [`os.environ`](https://docs.python.org/3.11/library/os.html#os.environ) is the process environment
  mapping. Pass a `Mapping[str, str]` into the resolver in tests and use `os.environ` only at the
  outer entry point.
- [`pathlib.Path`](https://docs.python.org/3.11/library/pathlib.html) provides platform-aware path
  expansion, resolution, and directory checks. Normalize relative inputs against the daemon's
  startup working directory and report the resulting absolute path.
- Python [signal handling](https://docs.python.org/3.11/library/signal.html) runs Python handlers in
  the main interpreter thread. Install `SIGINT` and `SIGTERM` handlers only in the console entry
  point and have them request event-loop shutdown rather than stopping services in the handler.
- Qt defines
  [`QCoreApplication`](https://doc.qt.io/qtforpython-6/PySide6/QtCore/QCoreApplication.html) as the
  event-loop owner for console/server applications without a GUI. Qt recommends connecting cleanup
  to `aboutToQuit`; `exec()` blocks until `quit()` or `exit()` is requested.
- The PyPA
  [entry-points specification](https://packaging.python.org/en/latest/specifications/entry-points/)
  says console-script functions may return an integer process outcome. A `[project.scripts]`
  command is therefore the portable installed launch surface.

## Architectural Decision

Add a separate `pypost-daemon` console entry backed by `pypost.daemon`. Do not add daemon parsing
to `pypost.main`, and do not import `pypost.main`, `pypost.ui`, `QtGui`, or `QtWidgets` from the
daemon path. The desktop `make run` path remains byte-for-byte behaviorally independent.

The daemon uses one `QCoreApplication` because the existing MCP and metrics lifecycle facades are
Qt Core objects. It loads immutable collection/environment snapshots synchronously, constructs the
existing registry with dictionary lookups, starts the existing metrics and enabled MCP servers,
and keeps the Qt Core event loop alive until normal termination or a fatal service failure.

## Architecture

### Component and dependency flow

```text
CLI values -----------+
process environment --+--> daemon_config --> validated resolved directories
platform defaults ----+                              |
                                                     v
settings.json --> strict ConfigManager ------> strict StorageManager snapshot
                                                     |
                                                     v
QCoreApplication --> DaemonRuntime --> MetricsManager
       |                    |
SIGINT/SIGTERM               +--> MCPServerRegistry --> MCPServerManager(s)
       |                    |
       +--> quit -----------+--> idempotent shutdown

Desktop make run --> pypost.main --> QApplication/MainWindow  (unchanged)
```

Dependencies point inward from the console entry to pure configuration and storage code, then to
the Qt Core runtime adapter. No production UI module depends on daemon modules, and daemon modules
never construct a widget.

### `pypost/core/daemon_config.py`

This module is pure Python and owns path-source precedence. It contains no Qt imports and exposes:

```python
@dataclass(frozen=True)
class ResolvedDaemonPaths:
    collections_dir: Path
    environments_dir: Path
    collections_source: Literal["cli", "environment", "default"]
    environments_source: Literal["cli", "environment", "default"]


def resolve_daemon_paths(
    *,
    cli_collections_dir: str | None,
    cli_environments_dir: str | None,
    environ: Mapping[str, str],
    default_data_dir: Path | None = None,
    cwd: Path | None = None,
) -> ResolvedDaemonPaths: ...


def validate_daemon_paths(paths: ResolvedDaemonPaths) -> None: ...
```

The optional default and working-directory inputs are deterministic test seams. Production omits
them, allowing the platform data root and current working directory to be resolved normally.

### Configuration names and precedence

| Logical input | Command line | Process environment | Default |
| --- | --- | --- | --- |
| Collections | `--collections-dir PATH` | `PYPOST_COLLECTIONS_DIR` | data root `collections/` |
| Environments | `--environments-dir PATH` | `PYPOST_ENVIRONMENTS_DIR` | user data root |

The environment default is the user data root because the compatible persisted file remains
`environments.json` directly under that directory. This task changes directory selection, not the
on-disk format.

Each row resolves independently in strict order: command line, then a non-empty environment value,
then default. An empty command-line value is an error. An empty or whitespace-only environment
value is treated as absent so deployment templates can leave it unset without selecting the
working directory accidentally.

For a selected non-empty value, expand `~`, then resolve it to an absolute path. Relative paths are
anchored to the process working directory captured once at startup. The normalized effective path,
not the unresolved input, appears in diagnostics.

### Directory validation and storage behavior

CLI- and environment-selected directories must already exist. Validation rejects, in order:

1. expansion or resolution failure;
2. a missing path;
3. a path that is not a directory;
4. a directory that cannot be traversed/read by the process.

An explicit invalid selection never falls through to a lower-precedence source. The exception is a
typed `DaemonConfigurationError` containing only logical input, source, normalized path when
available, and a safe reason.

Default directories retain first-run compatibility: the existing platform data root,
`collections/` child, and empty `environments.json` may be initialized as they are today. Failure
to create or read a default is fatal and uses the same safe diagnostic contract.

Extend `StorageManager` with keyword-only `collections_dir`, `environments_dir`,
`initialize_collections=True`, and `initialize_environments=True` inputs:

- Existing callers pass none and retain the current shared-data-root behavior exactly.
- Daemon callers pass both resolved paths. Each initialization switch is true only for its own
  default-origin path, so mixed-source resolution cannot mutate an explicit directory.
- `collections_path` points directly to the resolved collections directory.
- `environments_file` remains `<resolved environments directory>/environments.json`.

Add these strict, non-mutating `StorageManager` methods for daemon startup:

```python
def load_collections_snapshot_strict(
    self,
    *,
    required_ids: AbstractSet[str],
) -> Mapping[str, Collection]: ...


def load_environments_snapshot_strict(
    self,
    *,
    required_ids: AbstractSet[str],
) -> Mapping[str, Environment]: ...
```

`required_ids` is the deduplicated set referenced by enabled MCP rows, computed after strict
settings loading. Each method returns a read-only, ID-keyed mapping containing exactly the
requested records, with values detached from parser-owned mutable containers. An empty set
returns an empty mapping after checking the selected directory/file existence contract; it does
not parse unrelated records. Neither method renames legacy collection files, creates files,
updates encryption adapter state for skipped environments, or invokes the tolerant desktop
loaders.

Strictness applies to data needed by an enabled service, not to the entire operator data store.
Collection discovery accepts both ID-named and compatible legacy files. It parses candidate files
needed to resolve `required_ids`; malformed files not named for and not yielding a required ID are
skipped with a sanitized count-only warning. Environment loading parses the list container, then
fully decrypts and validates only records whose readable `id` is required. Invalid, duplicate, or
undecryptable unreferenced records are skipped with a sanitized count-only warning.

The methods raise a safe `DaemonDataError` when an unreadable or malformed store prevents a
required ID from being resolved, a required record is malformed or cannot be decrypted, a
required ID occurs more than once, or a required ID is absent. The error carries data kind,
`record_id: str | None`, safe filename when known, and failure category only. `record_id` is the
affected required ID for record-level and missing-reference failures; it is `None` only for a
store-wide failure that prevents any requested IDs from being resolved. A whole-file environment
JSON failure is fatal only when `required_ids` is non-empty. Existing tolerant desktop load
methods remain unchanged.

Storage stays independent of MCP configuration. `DaemonRuntime` owns the correlation boundary:

```python
@dataclass(frozen=True)
class RequiredDataConsumers:
    collections: Mapping[str, tuple[str, ...]]
    environments: Mapping[str, tuple[str, ...]]


def affected_server_ids(
    error: DaemonDataError,
    consumers: RequiredDataConsumers,
) -> tuple[str, ...]: ...
```

Each mapping key is a required record ID and each sorted, deduplicated tuple contains the opaque
IDs of all enabled MCP rows that reference it. For a record-specific error, the function returns
the consumers of that record. For a store-wide error with `record_id is None`, it returns the
union of consumers for that data kind. The return never contains server names, URLs, headers, or
other configuration values.

The runtime catches every `DaemonDataError` at the loader boundary, calls
`affected_server_ids()`, and emits one safe startup diagnostic for each returned server ID with
the data kind and failure category before aborting. Thus an absent, invalid, duplicate,
undecryptable, or store-blocked required record identifies every affected configured service even
though loading fails before row preflight. Unrelated bad persisted data still cannot prevent valid
enabled services from starting.

An explicit environment directory must contain the compatible `environments.json`; its absence is
a data error. A default-origin environment directory may initialize that file to an empty list,
preserving first-run behavior. An empty, readable collection directory is valid.

### Strict settings read

Add `ConfigManager.load_config_strict() -> AppSettings` alongside the unchanged tolerant
`load_config()`. Missing `settings.json` yields normal `AppSettings` defaults. An unreadable,
malformed, or invalid settings file raises a safe configuration exception instead of silently
starting with defaults.

Validation output may include the settings path plus sanitized validation field locations and
categories. It must not include Pydantic input representations, proxy headers, auth settings, or
environment values.

### `pypost/core/qt/daemon_runtime.py`

`DaemonRuntime` is the Qt Core lifecycle coordinator. It receives already resolved paths and
injectable collaborators; it never reads global arguments or environment variables. Its primary
interface is:

```python
class DaemonRuntime(QObject):
    def start(self) -> None: ...
    def shutdown(self) -> None: ...

    @property
    def is_ready(self) -> bool: ...

    @property
    def exit_code(self) -> int: ...
```

Composition creates one `ConfigManager` and strictly loads settings once. It builds
`RequiredDataConsumers` from enabled MCP rows before touching record contents and passes its keys
as the collection and environment `required_ids`. It applies encryption settings to one
`StorageManager`, calls the two strict snapshot methods, and translates any loader error through
the consumer indexes. It then creates one `MetricsManager`, one `TemplateService`, and one
`MCPServerRegistry` with lookup functions backed by those fixed mappings. It deep-copies persisted
rows into the registry through the existing `upsert()` contract.

Before opening any listener, preflight every enabled row:

- local endpoints must resolve their selected collection and environment;
- proxy endpoints must resolve an environment only when their configuration names one;
- duplicate ports remain rejected by the existing settings/registry validation;
- a missing reference identifies the opaque server ID and missing kind, never a substitute row.

The final missing-reference check is defensive because strict snapshot loading normally reports
it through `RequiredDataConsumers` first. Every loader or preflight failure for an enabled row
aborts the whole daemon startup and identifies its opaque server ID. Invalid data outside the
derived `required_ids` is not a loader or preflight input and cannot block valid enabled rows.
This is deliberately stricter than the GUI's best-effort row startup for configured services: a
supervisor needs one deterministic non-zero outcome rather than a partially ready process. The GUI
keeps its current best-effort semantics.

### Startup and readiness

The console entry schedules `DaemonRuntime.start()` after the Qt event loop begins. Startup then:

1. starts the metrics listener using persisted metrics bind settings;
2. starts every enabled MCP row through `MCPServerRegistry.start_enabled()`;
3. watches public metrics readiness and registry `status_changed` signals;
4. uses one bounded `QTimer` deadline for all startup work;
5. emits/logs ready only when metrics is listening and every enabled row is `running`.

No enabled MCP rows is valid: the metrics service still gives the daemon a useful long-lived
workload. A missing reference, bind failure, metrics failure, or deadline expiry before readiness
stops all partially started services and exits with status 1.

Expose the underlying thread-safe server state and callbacks through `MetricsServer`:

```python
@property
def is_listening(self) -> bool: ...


def set_lifecycle_handlers(
    self,
    *,
    listening_changed: Callable[[bool], None],
    unexpected_exit: Callable[[str], None],
) -> None: ...
```

`is_listening` is false initially and before each start, becomes true only after uvicorn startup
completes, and becomes false before either lifecycle callback reports a stop. The first callback
fires once for each actual boolean transition. The second fires exactly once per start generation
when a server that reached listening exits without `stop_server()` having requested that exit; its
string is a sanitized reason category, not an exception representation. Handler registration and
both methods return `None`.

`MetricsManager` converts those worker-thread callbacks into this Qt-facing public contract:

```python
class MetricsManager(QObject):
    listening_changed = Signal(bool)
    unexpected_exit = Signal(str)

    @property
    def is_listening(self) -> bool: ...
```

The property mirrors `MetricsServer.is_listening`; it is coherent before the corresponding signal
is emitted. Connections made by `DaemonRuntime` before `start_server()` receive lifecycle signals
on the Qt event-loop thread. `start_failed(str)` remains the pre-listening failure channel and is
not also emitted as `unexpected_exit`. Intentional stop may emit `listening_changed(False)` but
never `unexpected_exit`.

After readiness, an unexpected enabled MCP or metrics listener exit is fatal: the coordinator
logs the service kind/opaque ID, requests shutdown, and exits 1. Intentional shutdown sets a guard
first so expected `stopped` or `listening_changed(False)` signals are not misclassified.

### Console entry and packaging

`pypost/daemon.py` owns only process boundaries:

```python
def build_parser() -> argparse.ArgumentParser: ...
def main(argv: list[str] | None = None) -> int: ...
```

`main()` configures stderr logging, parses the two path options, resolves and validates paths,
creates exactly one `QCoreApplication`, composes `DaemonRuntime`, and installs main-thread
`SIGINT`/`SIGTERM` handlers. A retained low-frequency `QTimer` gives Python regular interpreter
opportunities while the Qt loop is idle; it does no work and is not a busy wait.

Signal handlers only mark normal termination and call `QCoreApplication.quit()`. Cleanup is
connected to `aboutToQuit` and repeated in a `finally` fallback; `shutdown()` is idempotent.

Add these supported launch surfaces:

- `[project.scripts]`: `pypost-daemon = "pypost.daemon:main"`;
- module fallback: `python -m pypost.daemon`;
- developer target: `make run-daemon`, using the repository virtual environment.

The existing `make run`, `pypost.main.main()`, and agent UI sidecar remain unchanged. The two new
environment variables are read only by `pypost.daemon`, so they cannot redirect desktop storage.

### Process outcomes and error semantics

| Outcome | Exit status | Operator output |
| --- | --- | --- |
| Help | 0 | Generated usage on stdout |
| Command syntax error | 2 | Generated usage/error on stderr |
| Normal `SIGINT`/`SIGTERM` | 0 | Shutdown start/completion events |
| Invalid directory or data | 1 | Logical input, source, safe path/reason |
| Invalid settings/reference | 1 | Settings path or server ID plus failure category |
| Bind/startup timeout | 1 | Service kind, server ID when applicable, bind/timeout reason |
| Unexpected service exit | 1 | Service kind/ID and lifecycle state |

Top-level handlers catch only expected typed startup errors. Unexpected exceptions are logged as a
generic startup failure with traceback policy reviewed for secret safety, all owned services are
stopped, and the process returns 1. No error path prints collection content, request data,
environment values, proxy headers, credentials, or secret-bearing configuration representations.

The existing proxy-start INFO message currently includes the upstream URL. Remove that value from
the message when enabling daemon launch; retain only host, port, and transport. This closes an
otherwise newly reachable secret-leak path without changing proxy behavior.

### Shutdown order

`DaemonRuntime.shutdown()` is idempotent and performs the following order:

1. mark shutdown intentional and stop readiness/health timers;
2. call `MCPServerRegistry.stop_all()` so request endpoints stop accepting work;
3. stop the metrics listener;
4. log completion and release references.

Existing server joins remain bounded. Cleanup proceeds to later resources even if an earlier stop
raises; individual failures are logged without secret-bearing object representations. The process
uses a non-zero result if cleanup fails after an otherwise normal termination.

## Data and Control Flow

### Successful startup

1. `argparse` separates command-line values from absent values.
2. `resolve_daemon_paths()` selects source and normalizes each directory independently.
3. Validation rejects invalid explicit paths before any service or storage mutation.
4. Strict settings and storage reads produce settings plus immutable ID-indexed snapshots.
5. Runtime preflight proves every enabled row resolves against those snapshots.
6. Qt Core event delivery starts metrics and all enabled registry rows.
7. The shared readiness deadline observes all listeners, then records `daemon_ready` once.
8. The main event loop remains blocked without polling or creating GUI objects.

### Startup failure

1. The first safe configuration/data/preflight failure is reported to stderr and logs.
2. If listeners have begun, shutdown stops every partial runtime.
3. The Qt loop exits with status 1; no lower-precedence path or alternate record is substituted.

### Normal termination

1. The main-thread signal handler marks a normal stop and requests `QCoreApplication.quit()`.
2. `aboutToQuit` invokes idempotent runtime shutdown while the event loop still exists.
3. `main()` returns 0 after successful cleanup.

## Testing Strategy

All new pytest modules declare an explicit timeout. Tests use temporary directories, injected
environment mappings, fake lifecycle collaborators, and bounded Qt timers. No test requires an
external network service, display server, user data directory, or unbounded sleep.

### Step 3 failing repro

Create:

`tests/test_daemon_config.py::test_resolve_daemon_paths_applies_precedence_independently`

The module uses `pytestmark = pytest.mark.timeout(30)`. Inside the test, import
`resolve_daemon_paths`, create distinct temporary default/CLI/environment directories, provide a
CLI collection directory but no CLI environment directory, and provide both environment values.
Assert:

- collections resolve to the CLI directory with source `cli`;
- environments resolve to the environment-provided directory with source `environment`;
- the unused default and lower-precedence collection environment value are not selected;
- importing the pure resolver does not import `PySide6.QtWidgets`.

Run only:

```bash
TEST_NODE='tests/test_daemon_config.py::test_resolve_daemon_paths_applies_precedence_independently'
make test PYTEST_ARGS="$TEST_NODE -q"
```

It fails on the accepted base because `pypost.core.daemon_config` and the independent precedence
contract do not exist. The failure is hermetic and occurs before any Qt event loop or network bind.

### Step 4 companion coverage

- Resolver matrix: CLI, environment, default, independent mixed sources, empty environment values,
  `~`, relative paths, and stable source labels.
- Validation: missing, non-directory, unreadable/traversal failure, explicit no-fallback, and
  default initialization failure. Permission behavior is injected where root users make real mode
  checks unreliable.
- Storage: independent directories, unchanged legacy defaults, no explicit-path creation, strict
  malformed JSON/model/decryption/duplicate-ID failures, and no migration writes.
- Settings: missing file defaults; malformed/unreadable/invalid settings fail safely without
  exposing input values.
- Runtime unit tests: fake metrics and registry drive ready, missing-reference, bind-failure,
  timeout, unexpected-exit, partial-start cleanup, and idempotent shutdown paths.
- Qt Core lifecycle test: a bounded local `QCoreApplication`/`QEventLoop` proves ready-to-quit and
  `aboutToQuit` cleanup without importing or constructing `QApplication`/`MainWindow`.
- CLI tests: help, parse error, environment injection, typed startup failure, normal termination,
  and integer outcomes. Invoke `main(argv)` with fakes rather than sending process signals.
- Packaging/Makefile contract: installed console mapping, module import, `run-daemon` target, and
  preservation of the existing `run` recipe.
- Existing focused suites: storage collections/environments, configuration, MCP registry/manager,
  metrics startup, main-window readiness/shutdown, agent lifecycle, Makefile, and packaging tests.
- Full repository `make test`, lint, typecheck, Markdown/link checks, and `git diff --check` in the
  development/cleanup steps.

## Implementation Plan

1. Add the Step 3 pure resolver test and capture its clean red failure through `make test`.
2. Implement `daemon_config` source selection, normalization, typed errors, and validation until
   the red test passes; add the companion resolver/validation matrix.
3. Extend storage with backward-compatible path injection plus strict non-mutating snapshot reads;
   add focused storage tests.
4. Add strict settings loading without changing desktop fallback behavior.
5. Implement the Qt Core `DaemonRuntime`, public metrics readiness, preflight, bounded readiness,
   health monitoring, and idempotent cleanup with fake-driven lifecycle tests.
6. Add the thin `pypost.daemon` parser/entry point, signal wiring, packaging command, and Makefile
   target; add CLI/import/contract tests.
7. Remove upstream URL content from the proxy-start lifecycle log and lock its privacy contract.
8. Run focused and repository gates, then update operator/developer documentation in Step 8.

Sequencing remains: research and approved architecture, Step 3 red test, production implementation
until green, cleanup, observability/debt analysis, and documentation.

## Compatibility, Rollout, and Rollback

### Compatibility

- Desktop imports, arguments, `QApplication`, `compose_app()`, and window readiness remain
  unchanged.
- Agent UI sessions remain intentionally widget-based and keep temporary shared data roots.
- Existing storage callers receive the same paths, initialization, tolerant loads, and migration
  behavior because all new storage inputs are keyword-only with compatible defaults.
- Existing `settings.json`, collection JSON, `environments.json`, encryption configuration, and
  PYPOST-1044 MCP rows require no migration.
- Existing GUI best-effort endpoint startup remains unchanged; fail-fast applies only to daemon
  readiness.

### Rollout

The daemon command is additive. Operators opt in explicitly and can validate effective paths and
startup behavior before placing the same command under a supervisor. Initial documentation must
state the unauthenticated MCP trust boundary and recommend loopback/firewall controls already
defined by the project.

### Rollback

Remove the console entry, Makefile target, daemon entry/runtime/config modules, and additive strict
storage/settings methods. No persisted format or settings migration needs reversal. The unchanged
desktop path remains the immediate operational fallback throughout rollout.

## Risks and Mitigations

- **Accidental GUI dependency:** Guard imports in tests and keep the daemon dependency graph free of
  `pypost.ui`, `QtGui`, and `QtWidgets`.
- **Partial readiness:** Use one coordinator deadline and fail/clean all partial listeners before
  returning non-zero.
- **Signal/event-loop races:** Install handlers on the main thread, schedule startup after `exec()`,
  and put cleanup on `aboutToQuit` with an idempotent fallback.
- **Desktop regression:** Keep `pypost.main` and existing storage defaults unchanged; run GUI and
  agent lifecycle regressions.
- **Filesystem race after validation:** Strict loaders still handle disappearance/permission
  changes and convert them to the same typed startup failure.
- **Secret leakage:** Sanitize structured errors, never log record contents, and remove the existing
  proxy upstream URL from startup logs.
- **Qt-free expectation:** Daemon mode is widget-free, not Qt-free. The existing registry already
  uses Qt Core signals; locating lifecycle code under `pypost/core/qt/` makes that dependency
  explicit.
- **Unexpected listener death:** Runtime health observation converts it to a supervised non-zero
  exit instead of leaving an apparently healthy empty process.

## Q&A

**Q: Why not add `--daemon` to `pypost.main`?**

A: The project has no installed general `pypost` command, and importing `pypost.main` eagerly pulls
in widgets and `MainWindow`. A separate console entry provides a clean dependency boundary and
leaves the established GUI launch untouched.

**Q: Why use Qt at all in a headless process?**

A: Existing MCP and metrics lifecycle facades are Qt Core objects. `QCoreApplication` provides
their event delivery without a display or widget dependency and avoids a larger server rewrite.

**Q: Why does one invalid enabled row fail the whole daemon?**

A: A process supervisor needs readiness to mean the persisted enabled service set is available.
The desktop can continue best-effort startup, while daemon startup returns a deterministic failure
instead of silently serving a partial configuration.

**Q: Are collection and environment formats changing?**

A: No. Collections remain JSON files in the selected collection directory, and environments remain
in `environments.json` within the selected environment directory.

**Q: Does daemon mode reload files while running?**

A: No. It snapshots data at startup, matching registry isolation. Operators restart the daemon to
apply file or persisted server-configuration changes; live watching is outside this task.

**Q: Is self-daemonization or service installation included?**

A: No. The console process stays in the foreground so systemd, launchd, containers, or another
supervisor can own backgrounding and restart policy.
