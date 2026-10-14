# PYPOST-1269: Support dual runtime distribution modes: GUI desktop and headless daemon

## Goals

PyPost serves two primary operational contexts:
1. Interactive API development on local developer workstations where users need a visual,
   graphical desktop interface to design, execute, and inspect requests and manage environments.
2. Automated service execution in server, container, CI/CD, and AI agent environments where
   graphical windowing systems (such as X11 or Wayland display servers) are absent, restricted, or
   unnecessary overhead.

Currently, running PyPost in headless or automated environments can cause operational friction,
inflated deployment footprints, and potential startup failures because desktop graphical
dependencies and windowing assumptions may interfere with headless execution.

The goal of this task is to establish first-class, explicit support for two distinct runtime
distribution and execution modes:
- **GUI Desktop Mode**: A full desktop application for interactive user workflows.
- **Headless Daemon Mode**: A lightweight, background service runtime for MCP server operations,
  automated collection execution, and environment serving without graphical display requirements.

**Implementation language**: Python (within the existing PyPost application codebase).

## User Stories

- As an **automation engineer / system administrator** deploying PyPost in a server or container,
  I want to run PyPost as a headless daemon service without needing a graphical display or desktop
  windowing system, so that services and background agents run reliably and efficiently.
- As an **AI agent operator**, I want to launch PyPost headless services to expose MCP tools and
  data collections, so that agents can interact with APIs without opening desktop windows or
  triggering GUI subsystem requirements.
- As an **API developer / desktop user**, I want to launch the complete interactive PyPost desktop
  application via a dedicated command, so that I have immediate access to the visual request editor,
  tabs, and configuration dialogs.
- As a **maintainer**, I want clearly defined runtime entry points, separated dependency concerns,
  and automated regression verification, so that ongoing changes to graphical features never break
  headless daemon operation and vice versa.

## Definition of Done

- Two first-class runtime execution modes are supported and documented: GUI desktop and headless
  daemon.
- Headless daemon mode starts, operates, and terminates cleanly in environments without an active
  display server (no display or GUI windowing system present).
- Dedicated, standard executable commands are provided for launching each mode:
  - GUI desktop application launcher.
  - Headless daemon service launcher.
- Development and operational tooling (such as repository run targets and packaging configuration)
  cleanly support both execution modes.
- Automated tests verify runtime isolation: headless daemon functionality can run without
  initializing or depending on desktop graphical interface components.
- User and developer documentation is updated to describe the dual runtime modes, their respective
  purposes, and instructions for running each mode.

## Task Description

### Problem Statement

PyPost provides both a rich desktop graphical user interface and headless MCP capabilities for local
AI agents. However, when operators or agents attempt to run PyPost as a background service or within
containerized environments, desktop graphical dependencies and windowing subsystems create severe
operational drawbacks:
- Unnecessary requirement for graphical libraries and display servers in non-interactive
  environments.
- Potential crash-on-launch or import errors when display servers (e.g. X11, Wayland) are absent.
- Lack of dedicated, distinct command-line entry points tailored to interactive versus daemon
  operations.

### Business Goals

- Enable seamless, resilient deployment of PyPost in headless cloud, container, and CI/CD
  environments.
- Maintain an intuitive, dedicated launch experience for desktop interactive developers.
- Ensure functional separation between interactive window presentation and background service
  orchestration.

### Scope (In)

- Defining and supporting the two explicit runtime modes: GUI desktop and headless daemon.
- Standard executable entry points for both GUI desktop and headless daemon execution.
- Operational tooling updates (e.g. run commands, packaging configuration, and verification gates)
  supporting both modes.
- Automated verification of headless execution in displayless environments.
- Comprehensive user and developer documentation explaining both modes and their usage.

### Scope (Out)

- Modifying the visual appearance, styling, or existing UI features of the desktop application.
- Altering the core semantics of the MCP protocol or introducing unrelated MCP tools.
- External operating system package manager packaging (e.g., creating native OS packages like
  RPM, DEB, or Homebrew formulas).

### Constraints and Assumptions

- **Implementation language**: Python.
- **Backward compatibility**: Existing desktop user workflows must continue to function seamlessly.
- **Environment**: Headless mode must function in standard POSIX/Linux container environments
  without an active graphical display.

## Main Entities and Interactions

| Entity | Role in System |
| --- | --- |
| **Desktop Runtime Mode** | Full interactive GUI application providing visual editors, tabs, and dialogs |
| **Headless Daemon Mode** | Background service runtime executing MCP services and API tasks without a GUI |
| **Desktop User** | Person interacting with the visual interface to edit and execute requests |
| **Automation / Agent** | Autonomous consumer interacting via background MCP or daemon services |
| **Shared Core Services** | Domain capabilities (collections, environments, execution engine, MCP tools) |
| **Runtime Entry Points** | Dedicated executable commands providing access to the respective runtime modes |

### System Interactions

1. **Interactive Workflow**: A Desktop User invokes the desktop entry point, which initializes the
   application with the visual windowing interface, allowing the user to manage requests and
   view responses.
2. **Headless Automation Workflow**: An Automation Engineer or Agent Operator invokes the daemon
   entry point in a headless environment. The daemon starts the background service and MCP
   capabilities without attempting to create desktop windows or connect to a display server.
3. **Shared Core Execution**: Both runtime modes rely on the shared core domain logic (requests,
   environments, collections, and MCP tooling), ensuring consistent functional behavior across both
   modes.

## Non-Functional Requirements

- **Operational Independence**: Headless daemon mode must execute successfully in headless
  environments where no display server (e.g., `DISPLAY` or `WAYLAND_DISPLAY`) is configured.
- **Reliability**: Failures or missing optional components in graphical subsystems must not impede
  the startup or continuous operation of the headless daemon service.
- **Ergonomics & Clarity**: Clear, distinct commands must exist for launching each runtime mode,
  preventing user confusion regarding which mode is active.
- **Maintainability & Verification**: Automated regression tests must safeguard the import and
  execution isolation of the headless daemon runtime.

## Q&A

**Q: Why are two explicit runtime modes needed instead of always running the GUI?**  
**A:** Automated environments (containers, remote servers, AI agent runners) do not have display
servers or monitors. Attempting to run graphical components in such environments causes errors,
wastes resources, and complicates container setup.

**Q: Why not split PyPost into two completely separate repositories?**  
**A:** Both modes share the underlying domain model, collection storage, environment resolution, and
MCP tool implementation. Maintaining them together ensures behavioral consistency while allowing
flexible execution.

**Q: Does headless daemon mode change how requests and collections work?**  
**A:** No. Core request execution, variable substitution, and collection storage behave identically
in both runtime modes.

**Q: What is the primary user-facing change for desktop users?**  
**A:** Desktop users gain a clean, first-class launcher command dedicated to the GUI application,
while retaining existing desktop workflows.
