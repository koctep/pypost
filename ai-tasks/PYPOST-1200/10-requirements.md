# PYPOST-1200: Clarify redundant WebSocket UI lifecycle regression coverage

## Goals

The WebSocket UI regression suite contains two green lifecycle checks whose
purposes are not sufficiently distinct. Both exercise the transition from a
connection attempt through an opened session and assert that the UI presents
the opened state. One check also covers the complete return to the idle state,
while the other gives additional assurance that event processing does not
replace an already-open session with a failure outcome.

The current wording of the narrower check describes a deferred transport
failure, although the repository evidence shows that its current green path
uses a quiet, deterministic transport and verifies that the opened state
survives event processing. This mismatch makes the suite harder to read and
leaves maintainers unsure whether the checks protect different behavior or
repeat the same regression coverage.

The business need is a trustworthy and maintainable regression suite. A
maintainer should be able to understand the purpose of each green check from
its presentation, and CI should retain a clear signal for the WebSocket UI
connect, open, disconnect, and idle lifecycle without paying for unexplained
duplicate coverage.

## User Stories

- As a **WebSocket UI maintainer**, I want each lifecycle regression check to
  communicate the behavior it protects so that failures can be diagnosed
  quickly.
- As a **test author**, I want overlapping checks to have clearly separated
  purposes or one canonical purpose so that future changes do not preserve
  misleading or redundant coverage.
- As a **CI user**, I want the WebSocket lifecycle signal to remain active and
  deterministic so that a green quality gate continues to represent the
  expected user-visible behavior.
- As a **PyPost user**, I want the existing Connect, Open, and Disconnect UI
  behavior to remain unchanged while its automated protection is clarified.

## Definition of Done

- The WebSocket UI lifecycle coverage has one unambiguous purpose for every
  remaining green check.
- The overlap between the complete lifecycle coverage and the opened-state
  stability coverage is resolved: the checks are clearly differentiated by
  behavior, or the redundant representation is consolidated without losing
  meaningful assertions.
- The resulting descriptions accurately describe the behavior currently being
  verified and do not imply a failure path that the green check does not
  exercise.
- The active coverage still protects the user-visible lifecycle expectations:
  an attempted connection presents a connecting state, an opened session
  presents its usable state, and disconnecting returns the UI to its idle
  state.
- No lifecycle coverage is skipped, disabled, or made non-enforcing as a way
  to remove the ambiguity.
- No production WebSocket behavior, public UI contract, transport semantics,
  or user-facing feature is changed.
- The focused WebSocket UI regression checks remain deterministic and pass
  through the repository's permitted Make validation.

## Task Description

### Scope

In scope:

- Clarifying the purpose and presentation of the overlapping green WebSocket
  UI lifecycle coverage.
- Preserving the meaningful opened-state stability and complete lifecycle
  assertions that the repository currently records.
- Removing only the ambiguity or redundancy associated with this specific
  coverage.

Out of scope:

- Changes to production WebSocket client behavior or UI state transitions.
- New WebSocket functionality, transport behavior, or network integration.
- Reworking unrelated WebSocket tests, fixtures, or lifecycle scenarios.
- Shared test infrastructure work that is not required to clarify this
  coverage.
- Changes to developer documentation outside the task artifacts unless a later
  approved workflow step establishes a need.

### Current ambiguity and repository evidence

- The same WebSocket UI regression module contains a broad Connect → Open →
  Disconnect lifecycle check and a second green check focused on preserving
  Open while events are processed.
- The broad check already asserts the visible controls at idle, connecting,
  open, and post-disconnect states.
- The narrower check repeats the initial connection and opened-state setup and
  adds a bounded event-processing observation, but its wording refers to a
  deferred transport failure that is not part of its current deterministic
  green setup.
- The issue description and the repository's preceding technical-debt record
  identify the valid resolution as either making the narrower purpose clear or
  consolidating genuinely redundant coverage. This requirements step does not
  choose between those outcomes.

### Compatibility constraints

- The user-visible Connect, Cancel, Disconnect, send-enabled, and editor
  editability states must retain their existing meanings.
- The lifecycle checks must remain active regression coverage and must not rely
  on live network reachability for a simulated opened state.
- Any retained event processing must remain bounded so the quality gate cannot
  hang while proving lifecycle behavior.
- The change must remain limited to the specified WebSocket UI regression
  coverage and its task artifacts.

### Business entities

- **WebSocket UI lifecycle**: the user-visible progression from attempting a
  connection to an opened session and back to idle after disconnecting.
- **Lifecycle regression coverage**: an automated quality signal that confirms
  the UI reflects those states and remains stable during normal event
  processing.
- **Maintainer**: the person who interprets a failed check and keeps the suite
  understandable over time.
- **CI quality gate**: the repository validation that reports whether the
  lifecycle contract remains trustworthy.

## Non-Functional Requirements

- **Clarity**: A maintainer can infer the protected behavior from each green
  check's description without reading unrelated implementation history.
- **Reliability**: The retained lifecycle signal remains deterministic under
  the repository's normal focused and full validation contexts.
- **Boundedness**: Event processing and lifecycle observation do not introduce
  an unbounded wait or suite hang.
- **Traceability**: The final coverage can be mapped to the user-visible
  Connect → Open → Disconnect → Idle expectations.
- **Scope discipline**: The task causes no production behavior change and no
  unrelated test-suite refactor.

## User Scenarios

1. **Maintainer reads the suite**: The maintainer can distinguish the purpose
   of the complete lifecycle check from any retained opened-state stability
   check, or sees one canonical check when the assertions are truly
   redundant.
2. **Lifecycle regression occurs**: A change that breaks the visible state
   progression or causes an opened state to be incorrectly replaced is still
   reported by active regression coverage.
3. **CI validates the change**: The focused WebSocket UI validation completes
   within bounded time and reports a meaningful pass or failure without
   depending on external network availability.
4. **User behavior remains stable**: A user sees the same connection controls,
   state transitions, and send/editor enablement as before this maintenance
   task.

## Q&A

**Why is this a maintenance task rather than a product feature?**

The user-visible WebSocket lifecycle is already defined and covered. The
problem is that two green checks communicate overlapping or mismatched intent,
which increases maintenance cost and weakens failure diagnosis.

**Must the work choose renaming or merging now?**

No. The requirement is to remove the ambiguity and preserve meaningful
coverage. The later design and development steps may determine whether clear
separation or consolidation best satisfies that requirement.

**Can the opened-state stability assertion be dropped?**

Only if the same regression protection remains represented by the resulting
active coverage. Removing meaningful protection solely to reduce the test
count does not satisfy this task.

**Does this change the WebSocket client or its transport?**

No. Production behavior, UI semantics, and transport behavior are
compatibility constraints, not targets of this task.

**What repository context informed these requirements?**

The Jira issue PYPOST-1200, its parent technical-debt record for WebSocket UI
lifecycle stabilization, and the current WebSocket UI regression module were
reviewed. No Jira fields, comments, or worklogs were changed.
