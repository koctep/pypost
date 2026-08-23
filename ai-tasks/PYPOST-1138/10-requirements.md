# PYPOST-1138: WS-12 User and developer documentation

## Programming Language

Python and Markdown. Markdown is used for end-user documentation, developer architectural guides, checklists, and workflow artifacts. Python scripts are used for automated Markdown linting and link verification.

## Goals

With the completion of the core WebSocket capabilities (WS-1 through WS-10), PyPost supports interactive WebSocket sessions, message composition and sequences, real-time stream inspection, environmental variable masking, operational resource ceilings, and bounded Model Context Protocol (MCP) probe tools. 

To ship this feature set to PyPost's high standards of software quality and usability, comprehensive and accurate documentation must be provided for both end users and software developers/maintainers.

The primary goals of this task are:
- **End-User Empowerment:** Provide a clear, cohesive User Guide (`doc/user/websocket.md`) and targeted updates across existing user guides that enable users to configure, connect, compose, sequence, inspect, and automate WebSocket endpoints without friction.
- **Limitation & Downgrade Transparency:** Clearly document known technical boundaries (e.g. no `permessage-deflate` compression, no HTTP upgrade response body introspection) and prominently document the collection downgrade caveat (saving a collection containing WebSocket profiles in an older PyPost version drops the profiles).
- **Developer & Contributor Architecture Reference:** Provide in-depth technical documentation (`doc/dev/websocket_architecture.md`) detailing the subsystem architecture, threading and session lifecycles, Qt transport isolation, and presenter ownership, alongside updates to general architecture, testing, and UI identity documents.
- **Cross-Platform Release Assurance:** Integrate an explicit per-platform `wss://` smoke verification procedure into the release checklist in `doc/dev/licensing.md` to ensure TLS certificate store and proxy behaviors are validated on Linux, macOS, and Windows releases.
- **Automated Documentation Hygiene:** Ensure all new and updated documentation strictly adheres to project Markdown standards and passes automated validation (`make lint-docs` and `make check-docs-links`).

## User Stories

- As an **API Developer / Tester**, I want a dedicated WebSocket user guide explaining how to configure connections, manage handshakes, compose text/JSON/binary messages, use presets, run multi-step sequences, and inspect streaming traffic, so that I can effectively test and debug real-time APIs.
- As an **API Developer / Tester**, I want clear documentation on how auto-reconnect, heartbeat pings, and stream buffer limits operate, so that I can configure resilient long-running sessions without overwhelming system memory.
- As an **API Developer**, I want known protocol limitations (such as lack of compression or handshake response body introspection) stated clearly in the user guide, so that I do not spend time troubleshooting unsupported features.
- As a **Team Member / Collaborator**, I want the collection storage guide to document how WebSocket profiles are shared in collection files and what happens if a file is downgraded to an older PyPost version, so that my team can collaborate safely without accidental data loss.
- As an **AI Agent Integrator / Prompt Engineer**, I want the user documentation for MCP tools to explain how WebSocket connection profiles can be exposed as bounded probe tools, how parameter templating works, and how secrets are masked, so that I can configure reliable agent tools for real-time systems.
- As a **Power User**, I want all WebSocket keyboard shortcuts and navigation keys listed in the hotkeys guide, so that I can navigate and operate WebSocket sessions rapidly via the keyboard.
- As a **System Administrator / Operator**, I want all global WebSocket configuration settings (default timeouts, buffer sizes, session concurrency caps, MCP probe ceilings) documented in the settings guide, so that I can tune PyPost for optimal performance and safety.
- As a **Core Developer / Contributor**, I want comprehensive developer documentation detailing the WebSocket architecture, session state machine, presenter boundaries, Qt event loop integration, and threading models, so that I can safely maintain and extend the codebase.
- As an **Automation / Test Engineer**, I want updated developer guides for UI identity object names and testing conventions (including offline mock fixtures and timeouts), so that I can write reliable automated tests for WebSocket features.
- As a **Release Engineer / QA Lead**, I want the release checklist to include a dedicated per-platform `wss://` smoke test procedure alongside existing platform matrices, so that every official release candidate is verified against host TLS certificate stores on all supported platforms.

## Definition of Done

This task is considered done when the following acceptance criteria are fully met and verified:

1. **Dedicated WebSocket User Guide (`doc/user/websocket.md`):**
   - A complete, structured user guide is created covering:
     - Connecting to WebSocket endpoints (ws:// and wss:// URLs, handshake headers, subprotocols).
     - Composing and sending messages (Text, JSON with formatting/validation, and Binary hex/Base64 modes).
     - Creating, organizing, and sending message presets.
     - Defining and running multi-step message sequences (with step delays and stop conditions).
     - Using the real-time stream inspector (filtering by direction/kind/text, clearing, exporting to JSON/NDJSON/CSV, autoscroll toggling).
     - Session limits, retention budgets, and memory protection.
     - Automatic reconnection policies and heartbeat configuration.
     - Sensitive environment variable masking in streams and exports.
     - Bounded MCP WebSocket probe tool configuration and usage.
   - Known limitations are explicitly stated in the user guide (no `permessage-deflate` compression support, no introspection of HTTP handshake response headers/body).

2. **Cross-Cutting User Guide Updates:**
   - `doc/user/interface.md`: Updated to describe the WebSocket tab layout, connection bar, status badges, stream viewer, and composer/presets panels.
   - `doc/user/hotkeys.md`: Updated with dedicated keyboard shortcuts for WebSocket operations (Connect/Disconnect, Send, Clear, Format JSON, etc.).
   - `doc/user/collections.md`: Updated to describe WebSocket profiles within collections, import/export behaviors, and the explicit lossy downgrade caveat (opening and saving a collection containing WebSockets in older PyPost versions drops the WebSocket entries).
   - `doc/user/settings.md`: Updated with descriptions and default values for all `ws_*` configuration options (concurrency limits, buffer budgets, heartbeat intervals, reconnect policies, MCP probe bounds).
   - `doc/user/mcp-tools.md`: Updated to document WebSocket MCP probe tools, bounded sampling mechanics (`stop_when`, max messages, max duration), secret isolation, and parameter schemas.
   - User documentation release notes include the downgrade caveat.

3. **Dedicated Developer Architecture Guide (`doc/dev/websocket_architecture.md`):**
   - A comprehensive technical guide is created detailing:
     - Subsystem architecture and component ownership.
     - Domain models and separation from Qt runtime types.
     - Session state machine and lifecycle transitions.
     - Presenter architecture (`WebSocketPresenter`, `TabsPresenter` delegation, `CollectionsPresenter` item strategies).
     - Streaming buffer design, retention bounding, and concurrency slots (`SessionSlots`).
     - Threading architecture (`QWebSocket` event loop affinity, `WebSocketProbeRunner` lifecycle).
     - Observability integration (structured logging, Prometheus metrics).

4. **Cross-Cutting Developer Documentation Updates:**
   - `doc/dev/ui_identity.md`: Updated with all stable `objectName` identifiers and automation selectors for WebSocket widgets, tabs, inspectors, buttons, preset lists, and sequence dialogs.
   - `doc/dev/testing.md`: Updated with WebSocket test strategies, offline fixture conventions (`test_websocket_server`), timeout rules (`pytest.mark.timeout`), and headless test execution.
   - `doc/dev/architecture.md`: Updated to reflect the WebSocket subsystem in overall system diagrams, package hierarchies, and component interactions.

5. **Release Checklist Platform Verification:**
   - `doc/dev/licensing.md` (and release checklist references) is updated to include an explicit per-platform `wss://` smoke verification step across Linux, macOS, and Windows to validate platform TLS certificate store and proxy handling.

6. **Documentation Validation & Linting:**
   - `make lint-docs` passes cleanly with zero formatting violations.
   - `make check-docs-links` passes cleanly with zero broken relative links or missing references.

## Task Description

### Problem Statement

During the development of Epic PYPOST-1123, a complete WebSocket subsystem was implemented across ten technical stories (WS-1 through WS-10), delivering backend transport engines, domain models, stream buffers, TLS policies, UI presenters/views, composers, sequences, settings, and MCP tools.

Without complete and synchronized user and developer documentation:
- Users would lack guidance on utilizing advanced WebSocket workflows (sequences, presets, MCP probes, stream exports, environment masking).
- Users might encounter unexpected behavior when downgrading collection files or expecting unsupported features (like permessage compression).
- Future maintainers and contributors would lack a unified reference explaining the architectural principles, threading constraints, and UI identity contracts.
- Release engineering would lack a standardized smoke test procedure to verify cross-platform TLS/WSS behavior before shipping.

### Scope

**In Scope:**
- Creation of `doc/user/websocket.md`.
- Updates to `doc/user/interface.md`, `doc/user/hotkeys.md`, `doc/user/collections.md`, `doc/user/settings.md`, and `doc/user/mcp-tools.md`.
- Inclusion of the collection downgrade caveat in `doc/user/collections.md` and release notes documentation.
- Creation of `doc/dev/websocket_architecture.md`.
- Updates to `doc/dev/ui_identity.md`, `doc/dev/testing.md`, and `doc/dev/architecture.md`.
- Addition of the per-platform `wss://` smoke step in `doc/dev/licensing.md`.
- Verification of documentation links and Markdown formatting via `make lint-docs` and `make check-docs-links`.

**Out of Scope:**
- Code implementation changes to the WebSocket engine or UI (already completed in WS-1 through WS-10).
- Implementation of out-of-scope follow-up features (e.g. Socket.IO client, permessage-deflate compression, live HTTP handshake introspection).
- Modifications to core Python backend models or business logic.

### Scope Boundaries

- **User Documentation vs. Developer Documentation:**
  - `doc/user/*` focuses strictly on user goals, UI interactions, workflows, keyboard shortcuts, configuration settings, and visible limitations. It avoids exposing internal Python classes, method signatures, or Qt internals.
  - `doc/dev/*` focuses on software architecture, design patterns, threading models, object names for test automation, testing harnesses, and release checklists.
- **Accuracy and Synchronization:**
  - All documented UI elements, settings keys, hotkeys, and MCP parameters must strictly match the actual implementation delivered in stories WS-1 through WS-10.

### Constraints and Assumptions

- **Formatting Standards:** All documentation files must comply with `lsr-markdown` rules (ATX headings, clear link text, consistent bullet markers, fenced code blocks, no trailing whitespace).
- **Link Integrity:** All relative links between documentation files must resolve accurately to existing files and valid anchors.
- **No Code Regression:** Documentation updates must not break existing build, lint, or test pipelines.

## Q&A

**Q: Why is documentation delivered as a dedicated top-down task rather than spread across individual stories?**
A: Individual stories (WS-1 through WS-10) focused on isolated slices of functionality (e.g. models, engine, inspector, TLS). A dedicated documentation task allows synthesizing the complete user and developer experience into a coherent, comprehensive guide, eliminating redundancies and ensuring cross-document consistency and link integrity across the entire repository.

**Q: Why must the downgrade caveat be prominently documented?**
A: When a user adds WebSocket profiles to a collection and shares the collection file with a collaborator running an older version of PyPost (which lacks WebSocket support), the older version will parse known fields safely but discard unrecognized `websockets` entries when saving back to disk. Transparently documenting this lossy downgrade behavior in `doc/user/collections.md` and release notes prevents unexpected data loss and sets clear expectations.

**Q: Why are known limitations (no compression, no handshake introspection) highlighted in user docs?**
A: PyPost uses Qt-native WebSocket transport (`QWebSocket`), which does not currently support `permessage-deflate` extensions or deep inspection of raw HTTP 101 Switching Protocols response bodies/headers. Explaining these constraints clearly in the user documentation saves users from confusion when debugging endpoints that request compression or custom upgrade headers.

**Q: Why is the per-platform `wss://` smoke test added to the release checklist in `doc/dev/licensing.md`?**
A: TLS certificate validation and system proxy discovery rely on platform-specific OS certificate stores and network stacks (CryptoAPI/Schannel on Windows, Secure Transport/Security Framework on macOS, OpenSSL on Linux). Automated Linux CI cannot fully substitute for validating packaged builds against native TLS stacks; an explicit release smoke step ensures every packaged release candidate is verified.
