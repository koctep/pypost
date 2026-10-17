# PYPOST-1437: Replace Fixed Thread Join Timeouts with Adaptive Backoff and Cancellation Tokens

## Goals

In PyPost, standalone Model Context Protocol (MCP) servers run asynchronous ASGI web service runtimes (such as Uvicorn) inside dedicated background worker threads. When an operator, automated test, or tool reconfiguration event requests a server shutdown via `stop_server()`, the background worker thread must be cleanly and reliably terminated before resources are reclaimed or new servers are launched.

Currently, the server shutdown routine relies on a rigid, hardcoded wait of 2.0 seconds (`self._server_thread.join(timeout=2.0)`). In production, high-concurrency test suites, and diverse operating environments, this fixed join timeout exhibits two severe operational drawbacks:
1. **Premature Timeout Under Heavy Load**: In high-load test matrix environments, busy continuous integration (CI) runners, or scenarios involving slow ASGI task drains and lingering keep-alive HTTP socket flushes, a fixed 2.0-second window is frequently insufficient for the ASGI loop to finish cleanly. The thread join times out, leaving an orphaned worker thread still executing and holding underlying network sockets. Subsequent server startups on the same host and port then encounter port collision errors (`EADDRINUSE`) or unpredictable test failures.
2. **Inflexible, Unobservable Waiting**: A single static timeout treats thread shutdown as an unobservable black box. If a thread exits in 5 milliseconds, or conversely if it remains blocked draining a slow request, the system lacks fine-grained visibility into shutdown progression, elapsed drainage duration, and cancellation status.
3. **Absence of Cooperative Cancellation Tracking**: While a stop flag may be signaled, the system lacks structured cooperative cancellation tracking to observe whether the worker thread has acknowledged the cancellation request, begun its drain cycle, or exceeded safe execution deadlines.

The business goal of this task is to replace the hardcoded thread join timeout with an adaptive backoff polling loop paired with cooperative cancellation tracking. This guarantees responsive shutdown when threads exit promptly, accommodates bounded drain periods for slow ASGI tasks or keep-alive socket releases under heavy system load, provides rich diagnostic logging across shutdown phases, and preserves thread lifecycle integrity across PyPost.

## Programming Language

- **Implementation language**: Python

## User Stories

- As an **automated test runner / CI pipeline**, I want server shutdown to adaptively monitor background thread termination with bounded backoff rather than a rigid fixed cutoff, so that heavy CPU load or ASGI task drainage in CI does not produce orphaned threads, leaked sockets, or flaky test failures.
- As an **API developer / desktop operator**, I want server termination and tool reconfiguration hot reloads to complete as fast as possible when worker threads exit promptly, so that user workflows and tool updates feel instantaneous and responsive.
- As a **PyPost system maintainer / DevOps engineer**, I want clear observability into thread drain phases and cooperative cancellation status, so that slow drains, long-lived client connections, or hung background workers are visibly reported with actionable diagnostics in system logs.
- As an **AI automation agent / client application**, I want server restarts to guarantee that previous background threads and network resources are thoroughly released before attempting rebinding, so that subsequent tool invocations never encounter connection resets or address contention.

## Definition of Done

This task is considered complete when:
1. The hardcoded 2.0-second fixed thread join timeout in server termination is completely replaced with an adaptive backoff polling mechanism and cooperative cancellation tracking.
2. The adaptive polling mechanism detects thread completion promptly with minimal latency, avoiding unnecessary delays when threads terminate rapidly.
3. Cooperative cancellation tracking explicitly coordinates shutdown signaling and tracks cancellation states (such as initiated, draining, completed, or timed out).
4. A bounded overall timeout ceiling is enforced to prevent indefinite hangs if a background worker or ASGI task fails to terminate.
5. Structured diagnostic logging records elapsed drainage time, drain phases, and clear warnings if worker threads fail to exit within the allowed threshold.
6. The server thread reference and running state remain truthful to actual runtime conditions, preventing premature thread dereferencing while background tasks are still active.
7. Verification passes all project quality gates (`make check` and `make verify-ai-tasks`).

## Task Description

### Problem Statement

In PyPost, standalone MCP servers execute ASGI servers within background worker threads to expose tool execution APIs over HTTP and Server-Sent Events (SSE). During normal application lifecycles, servers are frequently stopped and restarted—for example, when an operator updates environment variables, when tool collection signatures change, or during automated test teardowns.

When `stop_server()` is invoked, the system signals the server instance to stop and joins the worker thread with a fixed timeout of 2.0 seconds. This static approach creates significant operational vulnerabilities:
- Under CPU contention, virtualization overhead, or slow I/O, the ASGI event loop may require slightly longer than 2.0 seconds to cancel active tasks, flush keep-alive TCP connections, and close open sockets.
- If the 2.0-second wait expires before the worker thread finishes, the thread remains alive in the background (an orphaned thread). Although the system preserves the thread reference to reflect that the server is still running, the shutdown procedure exits without waiting for completion or providing detailed diagnostics on why the thread remained alive.
- If a caller immediately attempts to rebind the port (e.g., during `update_tools` or rapid restart), the port may still be held by the orphaned thread, causing bind failures.
- Conversely, a single fixed timeout call provides no visibility into how long shutdown actually took or whether the worker thread acknowledged cancellation.

An adaptive polling strategy with cooperative cancellation tokens solves these issues by actively polling thread status with exponential or stepped backoff up to a safe bounded limit, while cooperatively monitoring cancellation progress.

### Scope

- **Adaptive Backoff Polling Strategy**:
  - Replacing single-shot fixed timeout joining with an adaptive polling loop that samples thread liveness with increasing sleep intervals.
  - Ensuring near-zero latency exit when the thread terminates immediately.
- **Cooperative Cancellation Tracking**:
  - Utilizing cooperative cancellation signaling to request worker thread exit and track cancellation progression through distinct lifecycle states.
- **Bounded Total Shutdown Deadline**:
  - Enforcing a configurable, bounded overall deadline to guarantee that termination never deadlocks or hangs the calling process.
- **Structured Drain Phase Observability**:
  - Emitting structured log events documenting shutdown initiation, polling intervals, elapsed drain duration, and diagnostic warnings if the thread outlasts the deadline.
- **Thread State Truthfulness**:
  - Ensuring the server's internal running state and thread references truthfully reflect thread liveness throughout the shutdown process.

### Out of Scope

- Rewriting internal asyncio event loops or overriding Uvicorn server internals.
- Modifying MCP JSON-RPC protocol schemas, message definitions, or client transport contracts.
- Introducing asynchronous coroutine requirements to synchronous Qt GUI caller interfaces (the API of `stop_server()` remains synchronous).
- Implementing forced or unsafe thread termination (such as thread killing or process termination) which corrupts Python runtime state.

### Functional Requirements

- **FR1 (Adaptive Polling Mechanism)**:
  - The system must replace the fixed thread join call with an adaptive polling loop that checks thread termination status at increasing intervals (e.g., initial sub-millisecond or fast checks scaling gracefully up to a defined ceiling).
  - The polling loop must exit immediately once the background thread has terminated.
- **FR2 (Cooperative Cancellation Tracking)**:
  - The system must provide cooperative cancellation tokens or flags to signal termination intent to the background worker.
  - The system must track whether cancellation has been signaled, whether the thread is currently draining, and whether termination succeeded cleanly.
- **FR3 (Bounded Maximum Wait Ceiling)**:
  - The shutdown process must enforce a configurable maximum timeout ceiling to ensure that `stop_server()` remains strictly bounded and never blocks indefinitely.
- **FR4 (Responsive Low-Latency Exit)**:
  - When the background worker thread exits quickly (e.g., when no active HTTP connections or long-running tasks exist), `stop_server()` must return promptly without waiting for the full timeout or fixed delay.
- **FR5 (Observability and Drain Phase Logging)**:
  - The system must log structured diagnostic messages indicating:
    - Initiation of cooperative cancellation and target server identity.
    - Duration taken for thread drainage upon successful exit.
    - Warning diagnostics if the thread fails to terminate within the bounded deadline, including elapsed time and thread identifier.
- **FR6 (Truthful Lifecycle State Management)**:
  - The server must maintain truthful running state indicators. If a thread remains active after the bounded wait expires, the thread reference must not be discarded, ensuring subsequent lifecycle checks correctly recognize the server as still occupying resources.

### Non-Functional Requirements

- **NFR1 (Responsiveness and Efficiency)**:
  - The adaptive polling loop must introduce negligible CPU overhead while polling, balancing fast response times with low CPU utilization during backoff.
- **NFR2 (Deterministic Bounded Execution)**:
  - Under all conditions, including deadlocked or non-responsive worker threads, `stop_server()` must complete within the specified bounded deadline.
- **NFR3 (Thread Safety)**:
  - Cancellation state transitions and thread liveness inspections must be fully thread-safe across concurrent calls from GUI threads, worker threads, and test runners.
- **NFR4 (Backward Compatibility)**:
  - Existing call sites and public interfaces of `stop_server()` must remain synchronous and compatible without breaking changes to calling components.

### Constraints and Assumptions

- The solution must use standard Python threading and timing primitives without adding heavy external dependencies.
- The Uvicorn server running within the thread operates cooperatively, monitoring its own `should_exit` flag and task queue.
- Python threads cannot be safely killed externally; shutdown must remain strictly cooperative.

### Main Business Entities

| Business Entity | Description | Attributes (Business Perspective) |
| --- | --- | --- |
| **Server Worker Thread** | The background execution thread managing the Uvicorn ASGI server and network socket listener. | Thread ID, thread name, liveness status, daemon status. |
| **Cooperative Cancellation Token** | A shared token or synchronization construct signaling termination request and tracking drain progress. | Cancellation requested flag, cancellation timestamp, drain state. |
| **Adaptive Polling Policy** | The configuration governing the interval progression, backoff factor, and sleep bounds during thread join polling. | Initial interval, maximum interval, backoff multiplier, maximum total timeout. |
| **Shutdown Drain Event** | An operational event describing the outcome and timing of the server thread shutdown sequence. | Server host/port, duration elapsed, exit status (clean exit or deadline exceeded), remaining active tasks. |

### User Scenarios

#### Scenario 1: Immediate Clean Worker Exit on Normal Shutdown
An operator stops an idle MCP server from the application settings or UI. `stop_server()` signals the cooperative cancellation token and enters the adaptive polling loop. Because the Uvicorn event loop is idle, the worker thread terminates within 10 milliseconds. The adaptive loop detects thread exit on its first check, logs a successful clean shutdown with the elapsed drain time, and returns control immediately.

#### Scenario 2: Adaptive Backoff During Slow ASGI Connection Drain
During a test run, an MCP server is actively finishing a streaming response when `stop_server()` is called. The cancellation token is activated, signaling Uvicorn to drain active connections. The adaptive polling loop checks initially at short intervals, gradually backing off. After 450 milliseconds, the streaming response completes and the worker thread exits. The system logs successful drainage and returns cleanly well before the maximum deadline.

#### Scenario 3: Bounded Timeout and Diagnostic Warning on Stuck Worker
A third-party tool or client holds a persistent connection open indefinitely, preventing the worker thread from completing its drain. The adaptive polling loop continues backing off until the maximum timeout ceiling is reached. Rather than hanging forever, the system terminates the wait loop, retains the thread reference to maintain truthful state, and emits a structured warning detailing that the worker thread failed to terminate within the deadline.

#### Scenario 4: Rapid Tool Reconfiguration Hot Reload
An engineer modifies collection tools while the MCP server is running, triggering an automatic restart (`update_tools`). The server invokes `stop_server()` followed by port rebinding. Thanks to adaptive polling, the thread stops cleanly without lingering, allowing the subsequent bind check to succeed on the first attempt without artificial delay or port collision errors.

## Q&A

**Q: Why replace `Thread.join(timeout=2.0)` with an adaptive polling loop?**  
A: A single fixed join call provides an all-or-nothing wait. If the timeout is set too short (such as 2.0s), busy CI environments prematurely time out while the thread is in the middle of closing sockets. If set too long (e.g. 10s), any uncooperative thread freezes the entire caller for 10 seconds without visibility. An adaptive loop starts with very fast polling (achieving immediate return when threads stop quickly), backs off to prevent CPU spinning, and provides continuous visibility and progress tracking throughout the drain.

**Q: What is the role of cooperative cancellation tokens in this context?**  
A: A cooperative cancellation token provides an explicit, formalized contract between the server manager and the worker thread. Instead of relying solely on implicit side effects, the token explicitly represents the request to stop and allows the worker thread and shutdown manager to coordinate and track phases of the shutdown sequence.

**Q: Why can't we forcefully terminate a worker thread if it does not exit within the timeout?**  
A: In Python, forcibly terminating threads is not supported because it can leave shared runtime locks in corrupted states, truncate I/O buffers, or cause memory leaks and interpreter crashes. Cooperative termination is the only safe approach. By pairing cooperative cancellation with bounded wait timeouts and truthful state retention, PyPost ensures stability while preventing indefinite freezes.

**Q: How does this improve continuous integration (CI) test reliability?**  
A: CI runners frequently experience heavy CPU throttling and scheduling latency. Under fixed 2.0s timeouts, tests that stop and restart servers frequently fail due to `EADDRINUSE` because the previous server thread did not finish releasing its socket within exactly 2.0 seconds. Adaptive polling accommodates realistic drain latency under load while returning instantaneously on fast machines, eliminating test flakes.
