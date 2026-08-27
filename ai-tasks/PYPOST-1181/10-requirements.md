# PYPOST-1181: Stabilize flaky WebSocket connect/disconnect UI lifecycle test

## Goals

Continuous integration and local quality gates must give a trustworthy
pass/fail signal for the WebSocket client UI connect and disconnect lifecycle.
Today,
`tests/test_websocket_client_ui_repro.py::test_presenter_connect_and_disconnect_lifecycle`
intermittently fails (and in full-suite runs can hang long enough to be marked
timed out), even when the intended product Connect → Open → Disconnect → Idle
UI behavior is correct. That false failure and stall waste engineer time,
undermine confidence in the suite, and can block unrelated work in the Suite
Failures Cleanup sprint.

This debt item restores reliable verification that the presenter and tab UI
reflect session lifecycle correctly, without changing the business meaning of
Connect, Cancel, Disconnect, or editor lock/send enablement for end users.

**Implementation language**: Python (PyPost desktop client automated tests and
any supporting test isolation needed in the existing Python / Qt WebSocket UI
suite; no new runtime language).

## User Stories

- As a **developer or CI runner**, I want the WebSocket connect/disconnect UI
  lifecycle test to pass consistently so that a green suite means the
  Connect → Open → Disconnect → Idle UI contract is really intact.
- As a **maintainer diagnosing flakes**, I want this known intermittent
  Connect-button / handshake-race failure and mid-suite hang eliminated so
  unrelated task validation is not polluted by a pre-existing false negative
  or timeout.
- As a **user of the WebSocket client UI**, I want Connect and Disconnect to
  keep showing the correct button labels and control enablement for each
  session state; this task does not change that product contract — it only
  makes automated proof of it trustworthy.

## Definition of Done

- `tests/test_websocket_client_ui_repro.py::test_presenter_connect_and_disconnect_lifecycle`
  no longer fails intermittently with the Connect button stuck on "Connect"
  after a simulated open (including races where a live handshake failure is
  applied after open was already asserted).
- The same test (and its file under full `make test`) no longer hangs long
  enough to be marked timed out by the suite worker timeout; the check
  finishes within normal bounded suite expectations.
- The test still verifies the intended UI lifecycle contract:
  - Idle: Connect label; send disabled; editor writable
  - Connecting: Cancel label; editor read-only
  - Open: Disconnect label; send enabled
  - After disconnect back to Idle: Connect label; send disabled; editor
    writable again
- The flake is not “fixed” by skipping, xfailing, or deleting the test.
- Product Connect/Disconnect behavior for real users is unchanged except as
  required to keep the verified UI contract stable under test; no new
  end-user feature is in scope.
- Sibling debt and epic work (blank-tab picker, draft editor, collections
  import hang, MCP flakes) remain out of scope except as discovery context.

## Task Description

### Problem

The named WebSocket UI lifecycle regression test sometimes asserts that the
connect control shows "Disconnect" after a simulated open, but observes
"Connect" instead, accompanied by a host-not-found / handshake-failed outcome
against an unreachable example host. Isolated runs often pass; parallel full
`make test` runs have failed intermittently. Separately, under full suite
load the containing file has been observed to hang for many minutes and
surface as a timed-out file failure once worker timeouts are enforced
(PYPOST-1192 note on this issue).

Base commit noted at filing:
`1cc642b2ef7ff554228a5022cc5de866be6e72fb` (isolated re-run at that commit:
PASS). Observed rate at filing: intermittent fail under parallel full suite;
isolated runs typically green; later suites sometimes green. Not skipped,
xfailed, or deleted.

### Business need

Engineers need a stable regression check for “WebSocket UI follows
connect/disconnect lifecycle.” False failures and hung files erode trust in
CI, stall the Suite Failures Cleanup sprint goal, and divert investigation
away from real defects. End users already expect correct Connect/Disconnect
labels and control locking; this task protects that expectation with a
reliable automated signal.

### Scope

**In scope**

- Stabilize the named connect/disconnect UI lifecycle check so it passes
  reliably under both isolated and full-suite (`make test`) conditions.
- Eliminate the mid-suite hang / worker timeout for this file insofar as it
  is caused by the same lifecycle test instability.
- Preserve the business UI contract under test (labels and enablement across
  Idle → Connecting → Open → Idle).
- Keep the check present and mandatory (do not skip, xfail, or delete).

**Out of scope**

- Blank-tab protocol picker and related epic stories
  ([PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157) and
  follow-ons such as PYPOST-1158 / PYPOST-1159).
- Collections import UI hang ([PYPOST-1182](https://pypost.atlassian.net/browse/PYPOST-1182)).
- MCP server-manager / port-busy flakes (for example PYPOST-1178).
- Broader refactors of unrelated WebSocket UI or session features.
- Changing documented end-user Connect/Disconnect product behavior beyond
  what is needed for a trustworthy regression signal.

### Constraints and assumptions

- The intended UI lifecycle contract is already correct for users; the defect
  is intermittent automated verification (and related suite hang), not a new
  product feature request.
- Failure mode involves a live handshake outcome racing with a simulated
  open in the test; requirements demand isolation from that race without
  prescribing a specific design.
- Waits and event processing in the check must remain time-bounded; no
  open-ended stalls.
- Related debt origin: NON-BLOCKER follow-up 1 in
  `ai-tasks/PYPOST-1157/60-tech-debt.md`
  ([PYPOST-1181](https://pypost.atlassian.net/browse/PYPOST-1181)).
- Hang/timeout evidence: Jira comment from PYPOST-1192 Step 4
  (`tests/test_websocket_client_ui_repro.py` mid-suite hang; worker timeout
  surfaces TIMED_OUT).

## Non-Functional Requirements

- **Reliability**: The named test must not fail intermittently under repeated
  suite runs when the UI lifecycle contract is correct.
- **Boundedness**: The test and its file must finish within normal suite
  time bounds; no multi-minute hangs that only resolve via worker timeout.
- **Isolation**: The lifecycle check must not depend on real network
  reachability of example hosts for asserting simulated open/disconnect UI
  states.
- **Scope discipline**: Changes stay limited to making this UI lifecycle
  verification trustworthy; no unrelated WebSocket feature work.

## Main Entities

- **WebSocket client UI**: Tab and controls that show Connect / Cancel /
  Disconnect and gate send and editor editability by session state.
- **Session lifecycle**: Idle → Connecting → Open → Idle (or Closed) path the
  UI must reflect for connect and disconnect actions.
- **Connect control**: Button whose label and related control enablement
  must match the current session state.
- **Lifecycle regression test**: Automated check that connect then disconnect
  leave the UI in the expected states without flaking or hanging.
- **Quality gate (`make test`)**: Full suite run that must remain a
  trustworthy signal for this contract.

## User Scenarios

1. **Single-test run**: A developer runs
   `test_presenter_connect_and_disconnect_lifecycle` alone; it passes and
   confirms Connect → Open → Disconnect → Idle UI updates.
2. **Full suite**: The same test runs inside `make test`; it does not flake
   with a Connect label after open, and the file does not hang until worker
   timeout.
3. **Unrelated task validation**: Maintainers running full-suite checks for
   other tickets (for example Suite Failures Cleanup / PYPOST-1192-style
   work) are no longer blocked by this pre-existing WebSocket UI flake or
   hang.

## Q&A

**Why fix a flake that often passes in isolation?**
Intermittent full-suite failures and hung files burn capacity and hide or
distract from real regressions; trustworthy gates are a product-quality
requirement.

**Is the flake caused by PYPOST-1157 blank-tab picker work?**
No. It was found during that task’s suite/cleanup work; parent tech-debt
notes it as pre-existing / flaky. Isolated re-run at the noted base commit
passed.

**How does the PYPOST-1192 hang note relate?**
Full-suite hangs of `tests/test_websocket_client_ui_repro.py` were observed
and later surfaced as TIMED_OUT via worker timeout. That hang is treated as
in-scope failure mode of this same lifecycle instability, not a separate
product feature.

**May we skip or xfail the test?**
No. Definition of Done requires the check to remain active and stable.

**What counts as success for the UI contract?**
After connect reaches open, the UI shows Disconnect and allows send; after
disconnect back to idle, it shows Connect again with send disabled and the
editor writable — verified reliably without depending on live host lookup
success for the simulated open path.
