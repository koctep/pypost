# PYPOST-1454: Real Remote HTTP Transport Abort and Session Teardown Registration

## Goals

When users cancel a long-running, stalled, or unwanted remote collection retrieval or
catalog discovery operation, the application must immediately abort the underlying
network connection and terminate the active HTTP session.

In remote network operations, simply discarding the eventual result in the user interface
while leaving the remote connection active in the background causes severe operational issues:
- **Resource waste**: Abandoned network requests continue consuming local network sockets,
  thread capacity, and memory, as well as bandwidth and compute resources on remote servers.
- **UI sluggishness and stalls**: Users who cancel a slow fetch or dismiss a dialog must not
  experience lag or application stalls waiting for remote HTTP timeouts (which may take 30+
  seconds) to elapse before background workers can terminate.
- **Connection pile-up**: Rapidly switching between remote collections or repeatedly opening
  and closing remote import views must terminate previous transfers immediately rather than
  queuing multiple concurrent large payload downloads in the background.

This task establishes requirements for registering real remote transport abort and session
closure with the cancellation mechanism so that cancellation actively severs in-flight HTTP
transfers promptly.

## Programming Language

- **Implementation language**: Python

## User Stories

1. **As a workspace user**, when I cancel a slow or unresponsive remote collection import,
   I want the transfer to stop immediately over the network so my workspace remains snappy
   and my bandwidth is not wasted on discarded data.
2. **As a workspace user**, when I rapidly change selections between remote collections, I want
   superseded network transfers to abort instantly so that all available network throughput
   and worker threads are dedicated exclusively to my latest selection.
3. **As a workspace user**, when I close or dismiss the collection import dialog while a remote
   transfer is in flight, I want the dialog and its background tasks to close cleanly without
   hanging or waiting for remote server responses.
4. **As a workspace user**, when I cancel a remote transfer, I want the cancellation to be
   treated as an intentional user action, without receiving false "network failure" or
   "connection broken" error banners.
5. **As a maintainer**, I want automated verification demonstrating that cancelling a remote
   transfer actively terminates the underlying network session and aborts socket reading
   promptly, rather than relying on timeout expiration or post-hoc result discard.

## Definition of Done

- Cancelling an in-flight remote HTTP transport operation immediately triggers connection
  abortion and session closure over the wire.
- Background workers engaged in remote HTTP transfers unblock and terminate promptly
  (under 0.5s) upon cancellation instead of waiting for standard network timeouts.
- Cancelled transfers cleanly release all associated network sockets, session resources, and
  temporary buffers without leaking descriptors.
- Cancellation events do not surface user-facing error dialogs or false failure alerts; the
  cancellation remains quiet and clean.
- Subsequent requests after an aborted request can be initiated normally without interference
  or socket pool corruption.
- Automated tests verify prompt transport abortion and session termination when cancellation
  occurs during active remote data transfers.
- All quality gates pass via Makefile targets (`make check`).

## Task Description

The application supports importing collections and discovering manifests from remote
libraries. Remote network transfers are subject to high latency, slow connections, and
potential hangs. While cooperative cancellation signals and result discard mechanisms exist,
true remote transports require proactive closure of the underlying transport session/socket
when cancellation is signaled. Without this, blocked socket reads or HTTP streams hold
resources and worker threads until the full payload arrives or socket timeouts expire.

This task addresses registering real remote HTTP session and socket abort actions with the
cancellation workflow, ensuring in-flight remote transfers are actively severed when cancelled.

### Scope

- Business and functional requirements for remote transport abort upon user cancellation.
- Immediate teardown of active HTTP sessions/connections when a cancellation signal is fired.
- Quiet error handling for cancelled remote operations (preventing spurious error alerts).
- Clean lifecycle management for remote transport resources across success, error, and cancellation.

### Exclusions

- Modifying local filesystem or mock-only transport mechanisms (covered under prior tasks).
- Designing specific low-level transport classes or internal protocol architectures (deferred to Step 2).
- External network test dependencies (testing must remain fully self-contained).

## Functional Requirements

- **FR-1: Remote Transport Abort on Cancellation**: When a cancellation request is issued for
  an ongoing remote operation, the active network transport (HTTP session and underlying socket)
  must be immediately closed.
- **FR-2: Immediate Worker Unblock**: Closing the transport must unblock any worker threads
  blocked on remote network reads, allowing workers to exit promptly.
- **FR-3: Resource Teardown and Cleanup**: Any sockets, connections, or session handles opened
  for a remote request must be disposed of cleanly upon cancellation, preventing socket leaks.
- **FR-4: Quiet Cancellation Experience**: A cancelled remote operation must not trigger user-visible
  error banners, popups, or error logging that would misrepresent user cancellation as a system
  fault.
- **FR-5: Idempotent and Thread-Safe Cancellation**: Triggering cancellation multiple times, or
  triggering cancellation concurrently with normal request completion or failure, must be safe,
  deterministic, and free of race conditions.

## Non-Functional Requirements

- **NFR-1: Responsiveness / Teardown Latency**: Worker exit and socket closure upon cancellation
  must complete within 500 milliseconds, compared to standard network timeouts which may exceed
  30 seconds.
- **NFR-2: Resource Efficiency**: Local system resources (file descriptors, sockets, thread pool
  slots) and remote bandwidth must not be consumed by abandoned transfers.
- **NFR-3: Fault Tolerance & Robustness**: Aborting a connection mid-stream (e.g. during headers,
  during body transfer, or during connection negotiation) must never crash the application or leave
  the transport layer in an inconsistent state.

## Constraints and Assumptions

- **Language & Runtime**: Python / PySide6 environment.
- **No External Network in Tests**: Automated validation must use mock or local loopback servers;
  CI runs must not depend on external Internet connectivity.
- **Integration with Existing Cancellation**: Must integrate with the cooperative cancellation
  signaling conventions established in the application core.

## Main Entities

- **Remote Transport**: The communication component responsible for executing HTTP network requests
  to remote collection sources.
- **Cancellation Signal**: The cooperative signal indicating that a running operation should cease
  and release resources immediately.
- **Remote Operation Worker**: The background execution worker that orchestrates remote collection
  loading and monitors cancellation.
- **Remote Collection / Manifest**: The data payload retrieved from remote servers.

## Q&A

- **Q: Why is passive result discard insufficient for remote HTTP transfers?**
  **A:** Passive discard leaves the operating system socket open and the background thread blocked
  until the remote server finishes sending data or the socket timeout expires. For large collections
  or slow/hung servers, this wastes client/server bandwidth and holds worker threads hostage for tens
  of seconds.
- **Q: How should cancellation be reflected to the user?**
  **A:** Quietly. Cancelling an operation is an intended user action and should not be reported as a
  network error, server failure, or dialog warning.
- **Q: Does transport abort apply if the remote server has already completed the response?**
  **A:** If the response has already completed before cancellation occurs, the cancellation signal
  cleanly discards the result without needing to interrupt the socket. The abort mechanism is
  specifically targeted at in-flight and pending transfers.
