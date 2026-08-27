# PYPOST-1185: Prove Connect / Disconnect button paths update connection state hermetically

## Goals

[PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166) shipped MCP
Client draft chrome: a URL bar, **Connect** / **Disconnect**, and a
connection-state badge. Maintainers already had logging coverage that called
the presenter’s connect / disconnect entry points directly. What remained
unproven was that the **user-visible buttons** drive those same outcomes —
badge moves to Connected after Connect, back to Disconnected after
Disconnect — without opening a real network session in CI.

This debt item closes that verification gap. End users get no new feature;
maintainers get a hermetic, time-bounded GUI regression signal that button
wiring and badge transitions stay correct.

**Implementation language**: Python (PyPost desktop client automated tests;
no new runtime language).

## User Stories

- As a **maintainer**, I want automated proof that clicking **Connect**
  updates the connection-state badge to Connected, so a broken button slot
  cannot hide behind presenter-only tests.
- As a **maintainer**, I want that Connect proof to run without real network
  I/O, so CI stays hermetic and fast.
- As a **maintainer**, I want automated proof that clicking **Disconnect**
  after a connected state returns the badge to Disconnected, so disconnect
  chrome cannot regress unnoticed.
- As a **CI runner / developer**, I want any new checks to declare an
  explicit pytest timeout and finish without open-ended waits.
- As an **end user** of MCP Client Connect / Disconnect, I want no change to
  product behavior — only stronger automated proof that those controls still
  work.

## Definition of Done

PYPOST-1185 is done when:

1. Automated checks prove that activating **Connect** via the Connect
   control updates the connection-state badge to Connected (on a successful
   connect path under hermetic isolation).
2. Those checks isolate the outbound MCP client so **no real network** is
   used; CI never depends on a live MCP server.
3. Automated checks prove that activating **Disconnect** via the Disconnect
   control returns the connection-state badge to Disconnected after a
   Connected state.
4. New or extended checks declare an explicit pytest timeout (module or
   per-test) and do not introduce open-ended waits.
5. Existing MCP Client chrome / connect / disconnect coverage remains green.
6. Product Connect / Disconnect behavior for real users is unchanged except
   as required to restore the verified contract; no new end-user feature is
   in scope.
7. Sibling epic work (live tool browser polish, headers, invoke, user docs)
   stays out of scope except as context.

## Task Description

### Programming Language

Python — PyPost desktop client and its automated test suite.

### Problem

PYPOST-1166 delivered Connect / Disconnect chrome and a connection-state
badge. A follow-up gap (tech-debt item 7) noted that presenter logging tests
invoke connect / disconnect directly, so a broken **button → slot** path
could still leave the badge wrong while those tests pass.

The ticketed intent was an optional GUI check in the MCP Client tab suite:
click Connect → Connected; isolate the outbound client and prove Connect
does not perform live network work; Disconnect → Disconnected; keep pytest
timeout; no network.

### Business Need

Engineers need a hermetic regression signal that Connect and Disconnect
**as clicked by the user** still move the connection-state badge correctly,
without relying on a live MCP server. That protects the MCP Client chrome
contract: Connect and Disconnect are first-class controls, and CI can prove
them without network flakiness. End users do not get a new feature;
maintainers get trustworthy proof.

### Scope (this task)

**In scope**

- Automated proof that clicking **Connect** updates the badge to Connected
  under hermetic isolation (no real network).
- Automated proof that the outbound MCP client is isolated for that check so
  CI does not open sockets or talk to a live server.
- Automated proof that clicking **Disconnect** returns the badge to
  Disconnected after Connected.
- Explicit pytest timeout on new or extended checks; no open-ended waits.

**Out of scope**

- Changing Connect / Disconnect product rules, badge labels, or live
  initialize / `list_tools` / invoke behavior (unless a new assertion
  reveals a real defect against the shipped contract).
- Empty-URL validation policy, CONNECTING in-flight UX, or connect-error
  copy — owned by later / sibling MCP Client stories as already shipped.
- Headers / env resolution, Collections save, user-doc rewrite.
- Replacing or expanding the MCP Client tool browser beyond what is needed
  to observe Connected / Disconnected.
- Sibling suite flakes unrelated to this chrome path.

### Main Entities (Business Perspective)

- **MCP Client tab** — Outbound MCP Client workspace with URL, Connect /
  Disconnect, and connection-state chrome.
- **Connect control** — User-facing control that starts a connect attempt.
- **Disconnect control** — User-facing control that ends the session and
  returns chrome to disconnected.
- **Connection-state badge** — User-visible indicator showing Connected or
  Disconnected (and related non-connected states as the product already
  defines).
- **Outbound MCP client** — Component that would talk to a remote MCP
  server; must be isolated in this debt’s checks so CI stays offline.
- **CI verification** — Hermetic, time-bounded automated proof of the above.

### Functional Requirements

#### FR-1: Click Connect updates Connected badge

- FR-1.1 Automated checks must activate **Connect** through the Connect
  control (not only by calling the presenter entry point directly).
- FR-1.2 After a successful hermetic connect path, automated checks must
  prove the connection-state badge shows Connected.

#### FR-2: Hermetic isolation (no real network)

- FR-2.1 The Connect / Disconnect proofs must not depend on a live MCP
  server or open network sockets.
- FR-2.2 The outbound MCP client must be isolated (substituted or otherwise
  prevented from real I/O) for these checks.
- FR-2.3 The original debt wording “assert the outbound client is not
  called” meant **no live network session in CI**. Where the shipped
  product intentionally uses the outbound client on successful Connect,
  hermetic isolation of that client satisfies the business need; freezing
  draft-shell “never invoke the client on success” is not a user-facing
  requirement of this debt.

#### FR-3: Click Disconnect returns Disconnected

- FR-3.1 Automated checks must activate **Disconnect** through the
  Disconnect control after a Connected state.
- FR-3.2 Automated checks must prove the connection-state badge returns to
  Disconnected.

#### FR-4: Time-bounded suite

- FR-4.1 New or extended checks must declare an explicit pytest timeout
  (module-level or per-test).
- FR-4.2 Checks must not introduce open-ended waits.

#### FR-5: No product expansion

- FR-5.1 This task does not add MCP Client chrome features or change
  Connect / Disconnect product policy beyond restoring the verified
  contract if a proof exposes a real defect.
- FR-5.2 Existing green MCP Client coverage must remain green.

### Non-Functional Requirements

- **NFR-1 Time-bounded suite:** New checks finish within normal suite
  timeout expectations; no open-ended waits.
- **NFR-2 Regression signal:** Broken Connect / Disconnect button wiring or
  Connected / Disconnected badge transitions must fail CI.
- **NFR-3 Hermetic CI:** Proofs must not depend on network or a live MCP
  server.
- **NFR-4 Isolation:** Proofs target button-path badge behavior; they need
  not re-prove tool listing, headers, invoke, or metrics already covered
  elsewhere.
- **NFR-5 Stability:** Checks must be deterministic under parallel
  `make test`.

### Constraints and Assumptions

- Parent epic: [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155).
- Origin: NON-BLOCKER follow-up 7 in
  `ai-tasks/PYPOST-1166/60-tech-debt.md`; Jira
  [PYPOST-1185](https://pypost.atlassian.net/browse/PYPOST-1185).
- Related story: [PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166)
  (draft chrome that introduced Connect / Disconnect / badge).
- Ticket summary still says “does not call MCPClientService” from the
  draft-shell era. Live Connect work after 1166 may intentionally invoke
  the outbound client on success; this requirements doc treats **hermetic
  isolation + badge transitions via button clicks** as the durable
  business contract (see FR-2.3 and Q&A).
- This task is verification debt, not a new UX feature.
- Presenter-direct logging of connect / disconnect already exists; this
  ticket adds or completes **control-click** proof.

## Q&A

- **Why do this if presenter logging already calls connect / disconnect?**
  Logging tests bypass the button. A broken Connect or Disconnect slot can
  still leave the badge wrong while presenter-only tests pass.
- **Does “assert run is not called” still mean successful Connect must
  never touch the outbound client?**
  No as a frozen product rule. In the 1166 draft-shell debt note it meant
  Connect was local chrome and CI must not open network. After live
  Connect, successful Connect may use an isolated outbound client; the
  business need is hermetic Connected / Disconnected proof via the
  buttons, not forever forbidding client invocation on success.
- **Does this change what users see?**
  No. Same Connect / Disconnect / badge behavior; stronger proof only.
- **Is tool listing or invoke part of this ticket?**
  No. Observing Connected / Disconnected is enough; tool browser and
  invoke belong to sibling MCP Client stories.
- **Is a product bug fix in scope if a proof fails?**
  Yes, only to restore the existing Connect / Disconnect chrome contract —
  not to expand features.

## References

- [PYPOST-1185](https://pypost.atlassian.net/browse/PYPOST-1185) — this
  debt item
- [PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166) — MCP
  Client draft shell (source story)
- [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155) — parent
  epic
- `ai-tasks/PYPOST-1166/60-tech-debt.md` — follow-up 7 (source)
- `ai-tasks/PYPOST-1166/10-requirements.md` — draft-shell business contract
