# PYPOST-1046: Headless daemon launch with configurable data locations

## Goals

Operators need to run PyPost as a long-lived background service for MCP and related service
workloads on hosts where an interactive desktop is unavailable or undesirable. The current
launch path opens the desktop application and makes service readiness depend on GUI startup.

The business goal is a supported daemon launch that uses operator-selected collection and
environment data, starts without a visible user interface or display server, and reports
configuration failures clearly enough for unattended operation and service supervision.

**Programming language:** Python

## User Stories

- As an **operator**, I want to launch PyPost without a GUI so I can run its services on a server
  or as a background process.
- As an **integration operator**, I want to choose the collection and environment locations used
  by a daemon so it serves the intended requests and context.
- As an **automation owner**, I want launch-specific settings to override host-wide settings so
  each deployment can be configured predictably.
- As an **operator**, I want invalid or missing locations to stop startup with an actionable error
  so the process never serves an unintended fallback configuration.
- As an **existing desktop user**, I want the normal PyPost launch to behave as it does today.

## Functional Requirements

### Daemon operation

- PyPost must offer an explicit daemon mode intended for non-interactive, long-running operation.
- Daemon mode must not open or show application windows, require desktop interaction, or require
  an available display server.
- Daemon mode must load the collection and environment data needed by its service workloads before
  reporting itself ready.
- Daemon mode must start the enabled MCP server configurations whose collection and environment
  references are valid in the selected data locations.
- The daemon must remain active while its services are operating and stop them cleanly when the
  process receives a normal termination request.
- Normal termination must have a successful process outcome; configuration or startup failures
  must have a non-successful process outcome.

### Data-location configuration

- Operators must be able to configure the collection location and the environment location
  independently for daemon mode.
- Both locations must support command-line launch configuration and process-environment
  configuration, in addition to existing platform-appropriate defaults.
- Configuration precedence must be deterministic and documented:
  command-line values take precedence over process-environment values, and
  process-environment values take precedence over defaults.
- An absent value at one precedence level must allow the next available level to supply that
  location independently; configuring one location must not require configuring the other.
- Relative and absolute location behavior must be unambiguous in operator documentation.
- Startup diagnostics must identify which logical location is invalid and the effective path that
  was rejected, without disclosing stored environment values or collection contents.

### Validation and compatibility

- An explicitly configured collection or environment location that does not exist, is not a
  directory, or cannot be read must fail startup clearly and must not silently fall back to a
  lower-precedence location.
- Data that cannot be loaded sufficiently to start a configured service must produce an actionable
  error that identifies the affected service context without exposing secrets.
- Invoking the established desktop launch without selecting daemon mode must continue to open the
  GUI and use its existing configuration and storage behavior.
- Daemon-specific location configuration must not silently change the established GUI launch.
- Existing persisted MCP server configurations, including independently configured servers from
  PYPOST-1044, must remain usable when their referenced collection and environment data are
  available to the daemon.

## Non-functional Requirements

- **Reliability:** The daemon must have deterministic startup, readiness, and shutdown outcomes
  suitable for a process supervisor.
- **Security:** Errors and logs may identify configuration sources, paths, record identifiers, and
  failure categories, but must not expose environment values, credentials, request payloads, or
  other stored secrets.
- **Operability:** Startup failures must be visible on the non-interactive process output and
  distinguish configuration problems from service startup problems.
- **Compatibility:** Existing collection, environment, and MCP server data must not require a
  format migration solely to run in daemon mode.
- **Portability:** The default locations must continue to follow the supported platform's normal
  PyPost data-location conventions.
- **Maintainability:** Daemon and GUI behavior, precedence, validation failures, and shutdown must
  be verifiable with repeatable automated checks.
- **Performance:** Startup must not busy-wait, and idle daemon operation must not consume
  significant CPU merely to remain alive.

## Scope

### In Scope

- A supported headless/background-service launch mode.
- Independent daemon configuration of collection and environment data locations.
- Command invocation, process environment, and default precedence behavior.
- Validation and operator-facing errors for missing, invalid, or unreadable locations.
- Loading and running enabled persisted MCP server configurations without GUI interaction.
- Predictable readiness, process exit status, and graceful service shutdown.
- Operator and developer documentation for launch, precedence, defaults, and failures.
- Regression protection for the existing GUI launch.

### Non-goals

- Redesigning the desktop interface or changing its normal launch behavior.
- Redesigning collection, environment, or MCP server persistence formats.
- Adding new MCP tools, changing request execution semantics, or changing tool exposure rules.
- Adding remote administration, a daemon-management GUI, or an operating-system service package.
- Adding authentication, authorization, container orchestration, or network proxy configuration.
- Replacing the multiple-server behavior delivered by PYPOST-1044.
- Defining a general-purpose configuration framework beyond the two requested data locations.

## Assumptions and Constraints

- The issue is a five-point Python story and is related to PYPOST-1044's independently persisted
  MCP server configurations.
- "Daemon" means a foreground-capable, non-interactive long-running process that can be managed by
  an external supervisor; self-forking or platform-specific service installation is not required.
- The collection and environment locations are directories supplied by the operator or resolved
  from defaults. Their internal file layout remains a later design concern.
- Defaults mean the data locations used by a normal PyPost installation on the current platform.
- Command-line and process-environment configuration apply to daemon mode. The established
  desktop launch remains isolated from these daemon-specific overrides unless separately requested
  in a future task.
- The effective location at the highest populated precedence level is authoritative. Invalid data
  at that level is an error, not permission to use a lower-precedence value.
- The process may run without a terminal after startup, so durable process output and exit status
  are the primary startup feedback channels.
- The architecture step will choose names, interfaces, ownership boundaries, and internal loading
  mechanisms. This document intentionally specifies only observable behavior.

## Business Entities and Interactions

- **Operator:** A person or automation responsible for a PyPost service deployment. The operator
  selects daemon mode, supplies locations, observes readiness and failures, and requests shutdown.
- **Daemon process:** The non-interactive PyPost service runtime. It resolves configuration,
  validates data locations, starts services, and remains active until termination.
- **Collection location:** The operator-selected source of persisted request collections. It
  supplies the tool catalogs referenced by enabled MCP servers.
- **Environment location:** The operator-selected source of persisted environment contexts. It
  supplies variables and hidden-value metadata for enabled MCP servers.
- **Configuration source:** A command-line value, process-environment value, or platform default.
  It contributes each effective location according to documented precedence.
- **MCP server configuration:** The persisted description of an independently operated MCP
  endpoint. It references one collection and environment and starts when enabled and valid.
- **Service supervisor:** An external process manager or automation. It starts the daemon,
  observes its outcome, and sends normal termination requests.

## Scenarios

### Start with defaults

1. An operator selects daemon mode without supplying either data location.
2. PyPost resolves both locations from its platform defaults.
3. PyPost validates and loads the data, starts valid enabled services, and reports readiness.
4. No application window is opened and no display server is required.

### Configure through the process environment

1. An operator provides collection and environment locations through the process environment.
2. PyPost uses those values because no command-line values were supplied.
3. Services use only the data from the effective locations.

### Override one location for one invocation

1. The process environment supplies both locations.
2. The operator supplies a command-line collection location only.
3. PyPost uses the command-line collection location and the process-environment
   environment location.
4. Startup output makes the effective configuration understandable without exposing data values.

### Reject an invalid high-precedence location

1. A valid default and process-environment collection location exist.
2. The operator supplies a command-line collection location that is missing, unreadable,
   or not a directory.
3. Startup identifies the collection location and rejected path, starts no unintended fallback
   service, and exits unsuccessfully.

### Handle an unresolved persisted server reference

1. An enabled MCP server configuration refers to collection or environment data absent from the
   selected locations.
2. PyPost reports the affected server context and missing reference without exposing secret data.
3. The daemon does not substitute a different collection or environment silently.

### Preserve desktop launch

1. A user invokes PyPost through the established desktop path without selecting daemon mode.
2. The application opens its normal GUI and follows existing storage and startup behavior.
3. Daemon-specific location settings do not redirect the desktop session.

### Graceful shutdown

1. A supervisor sends a normal termination request to a ready daemon.
2. PyPost stops all services owned by that daemon and releases their resources.
3. The process exits successfully without requiring GUI interaction.

## Definition of Done

- [ ] A documented daemon launch starts PyPost without showing a GUI or requiring a display server.
- [ ] The daemon can independently obtain collection and environment locations from a
      command-line value, a process-environment value, or the platform default.
- [ ] Documented and tested precedence is command line over process environment over default,
      evaluated independently for each location.
- [ ] The effective collection and environment locations are validated before service readiness.
- [ ] Missing, non-directory, and unreadable explicit locations produce clear errors and a
      non-successful process outcome without silent fallback.
- [ ] Enabled MCP server configurations can start from the selected collection and environment
      data without opening a GUI.
- [ ] Missing persisted collection or environment references are reported without silently using
      different data or exposing secrets.
- [ ] The daemon stays active while services run and shuts them down cleanly on normal termination.
- [ ] The established GUI launch continues to open and behave as before when daemon mode is not
      selected.
- [ ] Operator documentation explains daemon launch, both location inputs, precedence, defaults,
      relative-path behavior, validation failures, readiness, and shutdown.
- [ ] Automated checks cover GUI isolation, all precedence levels, independent location
      resolution, invalid paths, service startup, process outcomes, and graceful shutdown.

## Current Behavior Evidence

- The standard `make run` target starts `pypost/main.py`, which creates a desktop application,
  shows the main window, and enters the GUI event loop.
- The current main launch has no daemon-mode selection or command-line parsing.
- The current application has no process-environment overrides for collection or environment data
  locations.
- Persistent storage currently derives collection and environment data from a common
  platform-specific data root.
- The application composition seam accepts an alternate shared data root for agent/test sessions,
  but the normal user launch does not expose it as an operator setting.
- Enabled persisted MCP server rows start only after the GUI-owned collection and environment load
  reaches readiness.
- PYPOST-1044 already supports multiple persisted MCP server configurations, each bound to a
  selected collection and environment, and provides independent lifecycle ownership.

## Q&A

**Q: Why is this needed instead of the existing launch?**

A: The existing path requires desktop application startup, which is unsuitable for unattended
servers and service supervisors.

**Q: Does daemon mode mean PyPost installs itself as an operating-system service?**

A: No. It provides a non-interactive long-running process that an external supervisor can manage.

**Q: Which configuration source wins?**

A: A command-line value wins over the process environment, which wins over the platform
default. Each location resolves independently.

**Q: What happens when the highest-precedence path is invalid?**

A: Startup fails clearly. PyPost does not hide the mistake by falling back to another location.

**Q: Must daemon mode support independently configured MCP servers?**

A: Yes. Enabled persisted configurations remain independent and use their referenced collection
and environment data when valid.

**Q: Does this task change stored collection or environment formats?**

A: No. It changes how operators launch the product and select data locations.

**Q: Does daemon configuration affect desktop users?**

A: No. The established GUI launch and its storage behavior remain unchanged.

**Q: Are command names or configuration variable names defined here?**

A: No. Those implementation-facing names belong to the architecture and development steps.
