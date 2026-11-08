# PYPOST-1467: IPC Protocol Version Negotiation and Mismatch Rejection

## Goals

When Model Context Protocol (MCP) servers run in isolated execution mode, the PyPost host
application and child worker processes communicate across process boundaries using an
inter-process communication (IPC) channel.

Currently, IPC message envelopes are stamped with a protocol version (`v=1`), but message
receivers on both sides of the boundary completely ignore this version field. As a result, if
host and worker processes run with mismatched protocol versions (such as during rolling upgrades,
code drift, or future envelope changes), the receiver may attempt to parse incompatible
payloads. This can lead to silent data corruption, misinterpreted commands, unhandled runtime
crashes, or unexplained worker process termination.

The goal of this task is to enforce explicit IPC protocol version validation and mismatch
rejection between the host supervisor and isolated worker processes. By rejecting incompatible or
unsupported protocol versions deterministically with clear, structured diagnostics, the system
prevents silent corruption, fails fast safely, and establishes a reliable foundation for future
protocol evolution while maintaining full compatibility with existing version 1 messages.

## Programming Language

- **Implementation language**: Python

## User Stories

- As a **system operator**, I want IPC message receivers to validate protocol versions
  immediately upon arrival, so that version mismatches or outdated components are rejected
  deterministically rather than causing silent errors or undefined runtime states.
- As an **automation author**, I want any protocol mismatch between host and worker processes to
  fail fast with structured diagnostics, so that my automated workflows do not execute against
  an inconsistently configured or degraded worker process.
- As a **troubleshooter / support engineer**, I want clear and sanitized diagnostic logs when a
  version mismatch occurs (including received version and supported versions), so that deployment
  version skew can be identified quickly without exposing sensitive variables or secrets.
- As a **system developer / maintainer**, I want a formal protocol version boundary with clear
  rejection rules, so that future IPC protocol changes or opcode additions can be introduced
  safely without breaking existing worker processes unexpectedly.

## Definition of Done

1. Explicit protocol version validation is enforced on all incoming IPC messages by both the
   host supervisor and the isolated worker process.
2. Any IPC message envelope bearing an unsupported, missing, or mismatched protocol version is
   deterministically rejected before the payload is processed by normal message handlers.
3. When a protocol version mismatch occurs, the receiver records or returns a structured
   diagnostic notification indicating the rejected version and expected version, avoiding silent
   message drops or unhandled exceptions.
4. Backwards compatibility with the current version 1 IPC protocol is strictly maintained; all
   valid version 1 messages continue to be accepted and processed without regression.
5. Rejection of an invalid or mismatched message on one worker channel is contained: it does not
   destabilize or crash the host application, nor does it interfere with healthy peer workers.
6. Diagnostic logs and rejection messages remain sanitized and never expose sensitive
   configuration, environment variables, or tool request payloads.
7. Automated acceptance checks verify deterministic rejection of unsupported or malformed version
   identifiers as well as successful communication using valid supported versions.
8. The change is strictly internal to the IPC communication boundary and introduces zero changes
   or regressions to the end-user graphical interface.

## Task Description

### Problem and Scope

In isolated execution mode, the host supervisor communicates with child worker processes by
passing structured message envelopes across IPC pipes. While envelopes include a version stamp
(`v=1`), receivers do not validate this property. Mismatched or malformed messages are processed
blindly, risking silent misinterpretation of parameters, broken worker states, or
difficult-to-trace crashes.

The scope of this task includes:

- Validating the protocol version on all message envelopes received by the host supervisor from
  isolated workers.
- Validating the protocol version on all message envelopes received by isolated workers from the
  host supervisor.
- Deterministically rejecting unsupported or mismatched versions with structured diagnostic
  details.
- Preserving backwards compatibility for valid version 1 messages across all supported message
  types.
- Ensuring host application stability and isolation containment when a mismatch occurs.

Out of scope are:

- Designing new transport mechanisms (existing pipe/queue IPC transports remain in place).
- Modifying end-user UI dialogs or settings controls.
- Unrelated process reliability features (such as active heartbeat watchdogs or worker memory
  ceilings), which are tracked in separate follow-up issues.

### Functional Requirements

- **FR1 (Host-Side Version Verification)**: The host supervisor must inspect the protocol
  version of every message received from a worker process before delegating to type-specific
  handlers.
- **FR2 (Worker-Side Version Verification)**: The worker process must inspect the protocol
  version of every message received from the host supervisor before executing the requested
  action.
- **FR3 (Deterministic Mismatch Rejection)**: When a received message specifies an unsupported,
  missing, or mismatched protocol version, the receiver must reject the message and prevent
  normal payload dispatching.
- **FR4 (Structured Diagnostic Reporting)**: A rejected version mismatch must produce a structured
  error or diagnostic record that identifies the received version and supported protocol
  version.
- **FR5 (Version 1 Compatibility)**: Valid protocol version 1 messages must continue to be
  accepted, parsed, and handled without error or behavioral change.
- **FR6 (Failure Containment)**: Handling a version mismatch on a given worker connection must not
  crash the supervisor process, terminate the PyPost application, or disrupt unaffected workers.

### Non-Functional Requirements

- **NFR1 (Fail-Fast Bounded Handling)**: Mismatched version rejection must occur immediately upon
  message receipt without incurring timeouts or blocking IPC queues.
- **NFR2 (Information Security & Privacy)**: Rejection notices and log entries must not leak
  sensitive values, environment variables, authentication tokens, or tool request payloads.
- **NFR3 (Cross-Platform Consistency)**: Version validation and rejection behavior must operate
  consistently across Linux, macOS, and Windows environments.
- **NFR4 (Zero UI Impact)**: This feature operates exclusively at the IPC layer and requires no
  graphical UI modifications.

### Constraints and Assumptions

- Implementation must be compatible with Python 3.
- Protocol versioning applies to the MCP worker process isolation subsystem.
- The specific architectural mechanism for rejection (e.g. error envelope opcode vs worker exit,
  handshake vs per-message validation) is deferred to Step 2 (Architecture).

### Main Business Entities

- **Host Supervisor**: The component managing isolated worker lifecycles and orchestrating IPC
  communication from the application side.
- **Isolated Worker**: A dedicated child process executing an MCP server instance and exchanging
  lifecycle/control commands with the supervisor.
- **IPC Message Envelope**: The top-level data structure exchanged across process boundaries,
  containing protocol metadata (version, message type) and payload data.
- **Protocol Version**: The numerical or token identifier designating the wire protocol version
  supported by the sending and receiving components.
- **Version Rejection Event**: A deterministic refusal to process an envelope due to an
  unsupported or incompatible protocol version.

### User Scenarios

1. **Normal Version 1 Communication**:
   The host supervisor sends a valid version 1 control message (e.g., START, UPDATE_TOOLS, STOP)
   to an isolated worker. The worker verifies that the protocol version is supported and executes
   the command normally.
2. **Worker Rejects Incompatible Host Message**:
   A worker process receives an IPC message stamped with an unsupported protocol version (e.g.,
   future version 2, negative version, or missing version). The worker rejects the message, emits
   a diagnostic indicating the version mismatch, and refuses to execute the unsupported command.
3. **Supervisor Rejects Incompatible Worker Message**:
   The host supervisor receives an IPC message from a child worker with an unsupported protocol
   version. The supervisor rejects the envelope, records a structured diagnostic detailing the
   incompatibility, and maintains operational stability without crashing the host.
4. **Peer Isolation During Mismatch**:
   When one worker encounters a version mismatch and fails or rejects a message, neighboring
   isolated servers continue operating normally without interruption or shared state
   corruption.

## Q&A

**Q: Why is protocol version validation needed if host and worker share the same codebase?**
A: While built from the same repository, isolated workers run in independent processes. During
application updates, hot-reloading, or future enhancements where protocol envelopes change, host
and worker processes may temporarily skew or receive malformed envelopes. Explicit version
validation ensures fail-fast safety rather than silent data corruption.

**Q: Does this task require introducing multiple active protocol versions right now?**
A: No. Version 1 is the currently supported protocol version. This task requires validating that
version 1 messages are accepted and that unsupported, mismatched, or missing versions are
deterministically rejected.

**Q: Does this document specify the exact wire format or rejection opcodes?**
A: No. In accordance with Top-Down principles, technical wire formats, opcode definitions, and
internal design choices are deferred to Step 2 (Architecture & Design).
