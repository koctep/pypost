# PYPOST-1288: Count outbound WebSocket messages and bytes

## Goals

Operators need to see how many WebSocket messages PyPost sends and how much payload data those
messages contain. Today, the outbound message and byte metrics remain at zero during normal use,
so dashboards cannot distinguish an idle session from one actively sending traffic. This task
closes that visibility gap without changing the user's send workflow.

The implementation language is Python.

## User Stories

- As an operator, I can see the number of WebSocket messages sent from PyPost so I can assess
  outbound activity.
- As an operator, I can see the outbound payload volume in bytes so I can assess traffic volume
  independently of message count.
- As a developer, I can rely on a documented and verified outbound metric contract when
  maintaining WebSocket send behavior or dashboards.

## Definition of Done

- Each successful outbound WebSocket text or binary message contributes exactly one to the
  outbound message count and its actual payload byte length to the outbound byte count.
- The count covers WebSocket tab sends regardless of whether the user triggers them with the Send
  button or `Ctrl+Return`. Other WebSocket tab send paths that successfully send a message are
  counted under the same rule.
- A blocked send, invalid message, or send that fails before handoff to the active connection
  contributes to neither outbound count. Peer delivery confirmation is not required: a successful
  send means PyPost accepted the message for transmission through an open connection.
- Text and binary messages remain distinguishable in the message count. A text message's byte
  count reflects its encoded payload size, including non-ASCII text; a binary message's byte count
  reflects its binary payload size.
- The public direction value for both outbound metrics is `outbound`, consistent with the
  existing metrics catalog. Each successful message uses that value for both counts.
- Automated contract coverage verifies successful text and binary sends, byte lengths, and a
  blocked or failed send. The developer metrics catalog explains when the counts change and the
  direction value used.
- Sending, validation, stream display, and connection behavior remain unchanged for users.

## Task Description

### Scope

The WebSocket session is the source of outbound text and binary messages. The operator observes
aggregate sent-message and sent-payload-byte counts. The message kind identifies text or binary
traffic; the direction identifies traffic leaving PyPost. A send attempt can be accepted, blocked,
or fail. Only an accepted message contributes to these outbound metrics.

This task covers outbound message and byte counts, their public direction and kind meanings,
behavioral contract coverage, and the developer metrics catalog. It does not change the send
controls, message contents, validation rules, transport behavior, or inbound metrics. WebSocket
control frames and peer receipt or acknowledgment are outside this task's count.

### Constraints and assumptions

- Existing metrics already define outbound WebSocket message and byte counts. The task concerns
  making those counts reflect actual use, not adding a new measurement category.
- One accepted message counts once even if the same message appears in the stream inspector.
- Metric labels and documentation must not include message payloads, connection URLs, or secrets.

### Non-functional requirements

- **Accuracy:** counts and byte totals reflect accepted messages without double counting.
- **Privacy:** metrics expose traffic totals and message kind, never payload content.
- **Consistency:** the same outbound direction value appears in both metrics and their catalog.

## Q&A

- **Q: Why count outbound sends?**
  A: Operators currently cannot tell from metrics whether users send WebSocket messages or how
  much data they send. This gap became more visible when `Ctrl+Return` became the tab-wide Send
  Message shortcut. See [PYPOST-1285 technical debt](../PYPOST-1285/60-tech-debt.md).
- **Q: Does `out` or `outbound` identify the direction?**
  A: `outbound` is the public metrics value used by the existing
  [metrics catalog](../../doc/prometheus_monitoring.md). `out` is a stream display value and does
  not define the metrics contract.
- **Q: What qualifies as a successful send?**
  A: PyPost accepts the message for transmission through an open WebSocket connection. This does
  not claim the remote peer received it. Blocked, invalid, and failed attempts are excluded.
- **Q: Do the counts apply only to the shortcut?**
  A: No. The business need is outbound traffic visibility, so a successful send counts regardless
  of the WebSocket tab action that started it.
