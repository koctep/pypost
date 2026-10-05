# PYPOST-1289: Count MCP client session disconnects

## Goals

Operators can see MCP client connection attempts and tool activity, but they cannot see when an
established client session ends. This leaves the session lifecycle incomplete and obscures
session churn. Recording each session end and its cause will make connection and disconnection
activity comparable and support investigation of session lifetimes alongside time-based
observability data.

## Programming Language

- **Implementation language**: Python. The task's developer documentation is Markdown.

## Business Entities

- **MCP client session**: An active connection represented by an MCP Client tab. A session starts
  when the client reaches its connected state and ends when it leaves that state.
- **Session end**: One transition that ends an established MCP client session.
- **End reason**: The cause of a session end: `user` for an explicit disconnect, `error` when a
  failure ends the session, or `teardown` when the tab or application releases it.
- **Lifecycle measurement**: An aggregate count of session ends, grouped by end reason, that
  operators can view with existing MCP client activity measurements.

## User Stories

- As an operator, I want to see how many MCP client sessions ended, so I can compare starts and
  ends and spot unexpected churn.
- As an operator, I want session ends grouped by cause, so I can distinguish user action,
  failures, and normal cleanup.
- As a developer, I want the MCP client lifecycle measurement documented and verified, so I can
  interpret it consistently when diagnosing session behavior.

## Definition of Done

1. Every established MCP client session that ends contributes one disconnect count.
2. Each disconnect count has exactly one reason: `user`, `error`, or `teardown`, matching the
   action or condition that ended the session.
3. Disconnecting through the tab control or the `F5` shortcut produces the same `user` count.
4. An error is counted as a disconnect only if it ends an established session. A failed attempt
   to connect is represented by the existing connection outcome and is not a disconnect.
5. Closing a tab or otherwise releasing an established session contributes a `teardown` count
   unless that session was already counted when it ended.
6. Repeated disconnect or cleanup requests after a session has ended do not add counts.
7. The measurement is available through the application's supported metrics outputs, including
   the output used when metrics collection is disabled, without changing user-facing session
   behavior.
8. Automated checks cover the reason categories, one-count-per-session rule, and availability
   through the supported metrics outputs. Developer documentation describes the measurement and
   its reason meanings.
9. The repository quality gate passes.

## Task Description

The MCP client currently reports connection, tool listing, and tool invocation activity but
omits disconnection. This task completes the observable session lifecycle for outbound MCP
clients. It covers established sessions ended by a user, by an error that actually terminates
the session, or by cleanup. It does not change when a session connects, disconnects, retries,
or reports a tool operation outcome.

The count is aggregate observability data. A count alone does not provide an exact duration
for any individual session; correlation with time-based data would be needed for that analysis.
The work does not add per-session tracing or a duration measurement.

Non-functional requirements: reasons remain limited to the three stated values, the
measurement does not expose connection addresses, tool arguments, or credentials, and
instrumentation must not interrupt the disconnect action.

## Q&A

- **Q: Why is a disconnect measurement needed?**
  A: The current lifecycle shows starts but not ends. Operators cannot measure churn or explain
  why sessions end using the available MCP client activity data.
- **Q: Does a failed connection attempt count as a disconnect?**
  A: No. No established session ended; the existing connection outcome covers that attempt.
- **Q: What if cleanup follows a user disconnect?**
  A: The ended session is counted once, with the cause that ended it. Later cleanup adds no count.
- **Q: Does this task provide exact session durations?**
  A: No. Aggregate disconnect counts complete the lifecycle activity view but do not themselves
  encode per-session start and end times.
- Source: [PYPOST-1285 technical debt TD-2](../PYPOST-1285/60-tech-debt.md).
