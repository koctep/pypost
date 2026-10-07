# PYPOST-1297: Verify outbound WebSocket metrics through a real loopback send

## Goals

Operators use the outbound WebSocket message count and outbound payload byte total to judge
how much traffic PyPost sends. PYPOST-1288 made these counts reflect accepted sends. Its
automated checks use a simulated connection, so they do not show that the counts stay correct
when a message goes through the real WebSocket connection used by the application.

This task adds that evidence. A regression in the real send path that leaves the counts at
zero, counts a message twice, or reports the wrong byte total must fail the automated suite.
User-visible behavior does not change.

The implementation language is Python.

## User Stories

- As an operator, I can trust that the outbound message count and byte total reflect messages
  sent over a real WebSocket connection, not only over a simulated one.
- As a developer, I get an automated failure when a change to the real send path breaks the
  outbound metric contract defined in PYPOST-1288.

## Definition of Done

- An automated check opens a real local WebSocket connection with no external network access.
  It sends messages through the same send path and metric recording that the WebSocket tab
  uses.
- For each accepted outbound text message, the outbound message count for text increases by
  exactly one. The outbound byte total increases by the UTF-8 encoded size of the original
  text. At least one text message contains non-ASCII characters, so the encoded size differs
  from the character count.
- For each accepted outbound binary message, the outbound message count for binary increases by
  exactly one. The outbound byte total increases by the size of the original binary payload.
- An accepted zero-byte message increases the outbound message count by exactly one and leaves
  the outbound byte total unchanged.
- Each check compares the value before the send with the value after the send, so values from
  other tests or earlier sends cannot affect the result.
- The checks confirm that the local peer received each sent message, including the zero-byte
  message, with the same kind and payload. This is evidence that the real connection carried
  the send. It is not a delivery guarantee offered by PyPost.
- The check finishes within the repository test timeout and uses bounded waits only.
- Existing coverage still passes. This includes the real loopback text and binary round trip
  and the PYPOST-1288 simulated-connection contract tests.
- Production behavior, public metric names, label values, and the metrics catalog meaning stay
  unchanged. If the check finds a real defect, the defect is fixed or recorded as a blocker. The
  check is not weakened.
- The affected test files pass when run with `make test WORKERS=1 PYTEST_ARGS='<files> -q'`.
- `make lint` passes.
- `make check` reports no failure outside the pre-existing failures already filed as
  PYPOST-1299, PYPOST-1298, PYPOST-1263, PYPOST-1305, and PYPOST-1306. A failure not in that set
  blocks completion.

## Task Description

### Problem

PYPOST-1288 recorded this follow-up as a non-blocking coverage gap in
[its technical debt analysis](../PYPOST-1288/60-tech-debt.md). The gap still exists at base
commit `286b3a4c`.

- The real loopback test sends one text message and one binary message through the real Qt
  WebSocket adapter. It checks the round trip only. It does not use the WebSocket tab's metric
  recording and does not check any outbound metric. It sends no zero-byte message.
- The PYPOST-1288 metric tests check text, binary, blocked, and rejected sends against a
  simulated connection. The real adapter is tested only in isolation, with its handoff result
  replaced, so real socket behavior is not checked.

### Scope

In scope:

- Automated integration coverage that connects real loopback traffic to the outbound message
  count and outbound byte total.
- Text messages, including non-ASCII text, binary messages, and a zero-byte message.

Out of scope:

- New metrics, labels, dashboards, or catalog changes.
- Inbound metrics and control frames.
- Delivery acknowledgement or guaranteed-delivery behavior in PyPost. The test peer's receipt
  is test evidence only and adds no new production behavior.
- Blocked, invalid, and rejected sends. PYPOST-1288 already covers these.
- Changes to send controls, validation, or stream display.

### Business entities

- **Outbound message:** a text or binary message that PyPost accepts for transmission through
  an open WebSocket connection.
- **Outbound message count:** the total number of accepted outbound messages, separated by
  message kind (text or binary), with direction `outbound`.
- **Outbound byte total:** the total payload size of accepted outbound messages, with direction
  `outbound`. Text size is its UTF-8 encoded size. Binary size is its raw size.
- **Local loopback peer:** a WebSocket endpoint inside the test that receives the messages. It
  needs no external network.

### Constraints and assumptions

- The metric contract is the one accepted in
  [PYPOST-1288 requirements](../PYPOST-1288/10-requirements.md). This task verifies that
  contract and does not change it.
- Assumption: a zero-byte message is a valid accepted send for both text and binary on an open
  connection. At least one zero-byte kind must be covered. If a zero-byte message is not
  accepted on the real path, the check records this as a finding and does not skip the
  criterion.
- Assumption: the local peer can observe a zero-byte message. At `286b3a4c`, the real adapter
  treats a send as accepted when the handed-off size equals the payload size, which holds for
  zero bytes. The test peer records every received text and binary message with no size
  filter. If the peer does not observe a zero-byte message, the check records this as a
  finding. The criterion is not weakened to the metric change alone.
- Assumption: covering the send path behind the WebSocket tab is enough. Driving the widget
  through simulated key presses or clicks is not required.
- Repository operations run only through `make` targets.

### Non-functional requirements

- **Determinism:** the check is hermetic, uses bounded waits, and is stable under parallel
  test runs.
- **Isolation:** the check does not depend on metric values from other tests.
- **Privacy:** no message content appears in metric labels.

## Q&A

- **Q: Why add this check if PYPOST-1288 already passes?**
  A: The PYPOST-1288 checks prove the send contract with a simulated connection. Only a real
  connection proves that the real adapter's acceptance result and the payload sizes produce the
  expected counts. See [PYPOST-1288 technical debt](../PYPOST-1288/60-tech-debt.md).
- **Q: Does the real loopback test already check outbound metrics?**
  A: No. At `286b3a4c`, it checks sent and received frames for one text and one binary message
  only. It does not check metrics or use a zero-byte message.
- **Q: Why include a zero-byte message?**
  A: It is the edge case where the count must change but the byte total must not. It also
  checks that the real adapter treats an empty payload as a complete accepted send.
- **Q: Which `make check` failures are acceptable?**
  A: Only the pre-existing failures filed as PYPOST-1299, PYPOST-1298, PYPOST-1263,
  PYPOST-1305, and PYPOST-1306. Any other failure blocks the task.
