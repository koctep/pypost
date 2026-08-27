# PYPOST-1180: Prove blank-tab protocol picker outcomes in CI

## Goals

The blank-tab protocol picker (shipped in
[PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157) under epic
[PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155)) is the product
gate that turns a new-tab request into **HTTP Request**, **WebSocket**, or
**no tab** (cancel). Maintainers must trust that the picker’s *outcome*
mapping stays correct: choosing HTTP yields HTTP, choosing WebSocket yields
WebSocket, and dismissing yields no protocol.

Today’s automated suite already proves menu construction (HTTP first /
default) and proves blank-tab routing when a fake picker is injected so CI
never opens a live blocking popup. That leaves the production picker’s own
choice → protocol (or cancel → no choice) path under-covered for the two
primary protocols and for dismissal. A regression there could ship while
presenter tests still pass against stubs.

This debt item closes that verification gap so CI fails if those three
outcomes drift, without introducing a live blocking popup that hangs the
suite.

**Implementation language**: Python (PyPost desktop client automated tests;
no new runtime language).

## User Stories

- As a **maintainer**, I want automated proof that confirming **HTTP Request**
  in the blank-tab protocol picker yields the HTTP protocol choice, so a
  mapping regression cannot silently open the wrong blank-tab kind.
- As a **maintainer**, I want automated proof that confirming **WebSocket**
  yields the WebSocket protocol choice, so the documented WebSocket new-tab
  path stays locked at the picker boundary.
- As a **maintainer**, I want automated proof that dismissing the picker
  yields no protocol choice, so cancel continues to mean “create no tab”
  at the source of that decision.
- As a **CI runner / developer**, I want those proofs to finish without a
  live blocking popup, so the suite stays hermetic and time-bounded.
- As an **end user** of `Ctrl+N` / tab-bar **+**, I want no change to picker
  labels, defaults, or cancel/confirm behavior — only stronger automated
  proof that those outcomes stay correct.

## Definition of Done

PYPOST-1180 is done when:

1. Automated checks prove the production blank-tab protocol picker returns
   the **HTTP** protocol when the user confirms the **HTTP Request** option.
2. Automated checks prove it returns the **WebSocket** protocol when the
   user confirms the **WebSocket** option.
3. Automated checks prove it returns **no protocol choice** when the picker
   is dismissed without a selection.
4. Those checks do **not** open a live blocking popup in CI (no suite hang
   from a real modal wait).
5. Existing construction coverage (HTTP first / default active option) and
   injected-picker presenter / plus-tab coverage remain green.
6. Product picker behavior for real users is unchanged except as required to
   keep the verified outcome contract; no new end-user feature is in scope.
7. Sibling epic work (draft editor, close-last-tab picker reuse, MCP Client
   product changes, user-doc rewrite) stays out of scope except as context.

## Task Description

### Programming Language

Python — PyPost desktop client and its automated test suite.

### Problem

PYPOST-1157 delivered the blank-tab protocol picker and routing. Its tests
cover:

- Menu construction: **HTTP Request** first and default.
- Presenter / plus-click / golden paths with an *injected* picker so CI
  never waits on a live blocking popup.

What remains unproven for this debt item is the production picker’s
outcome mapping for the three outcomes that drive blank-tab creation:

| User outcome | Expected picker result |
| --- | --- |
| Confirm **HTTP Request** | HTTP protocol |
| Confirm **WebSocket** | WebSocket protocol |
| Dismiss / cancel | No protocol (no tab) |

Without that lock, a broken mapping could pass CI while stubs still feed
correct protocols into the presenter.

### Business Need

Engineers need a hermetic regression signal that the picker still translates
confirm and cancel into the right protocol decision. That protects the
business contract from PYPOST-1157: choose protocol before a blank tab
opens; cancel creates nothing; HTTP and WebSocket remain distinct first-class
choices. End users do not get a new feature; maintainers get trustworthy
proof.

### Scope (this task)

**In scope**

- Automated proof of picker outcomes for HTTP confirm, WebSocket confirm,
  and dismiss / no choice.
- Keeping those proofs free of a live blocking popup so CI cannot hang on
  that wait.
- Preserving existing construction and injected-picker coverage.

**Out of scope**

- Changing picker labels, option order, default selection, or user-visible
  confirm/cancel behavior (unless a new assertion reveals a real defect).
- Live keyboard / mouse interaction against a real blocking popup in CI
  (intentionally deferred; same hermetic constraint as PYPOST-1157).
- Blank WebSocket draft editor — [PYPOST-1158](https://pypost.atlassian.net/browse/PYPOST-1158).
- Close-last-tab / empty-workspace picker reuse —
  [PYPOST-1159](https://pypost.atlassian.net/browse/PYPOST-1159).
- MCP Client product / picker-item stories —
  [PYPOST-1165](https://pypost.atlassian.net/browse/PYPOST-1165) (and any
  existing MCP-outcome proof already present stays untouched unless it
  blocks this work).
- User documentation rewrite —
  [PYPOST-1163](https://pypost.atlassian.net/browse/PYPOST-1163).
- Presenter routing, metrics, or Collections new-tab paths beyond what is
  needed to keep existing coverage green.
- Sibling suite flakes (for example
  [PYPOST-1181](https://pypost.atlassian.net/browse/PYPOST-1181),
  [PYPOST-1182](https://pypost.atlassian.net/browse/PYPOST-1182)).

### Main Entities (Business Perspective)

- **Blank-tab protocol picker** — Asks which protocol a new blank workspace
  tab should use before any tab is created.
- **HTTP Request choice** — Default protocol option; confirm means open a
  blank HTTP draft.
- **WebSocket choice** — Opt-in protocol option; confirm means open a blank
  WebSocket tab.
- **Dismiss / cancel** — No protocol chosen; workspace must not gain a new
  tab.
- **Picker outcome** — The protocol decision (HTTP, WebSocket, or none)
  returned after the picker closes.
- **CI verification** — Automated proof of those outcomes without a live
  blocking popup.

### Functional Requirements

#### FR-1: HTTP confirm outcome

- FR-1.1 Automated checks must prove that confirming **HTTP Request** yields
  the HTTP protocol as the picker outcome.
- FR-1.2 That outcome must be distinguishable from WebSocket and from no
  choice.

#### FR-2: WebSocket confirm outcome

- FR-2.1 Automated checks must prove that confirming **WebSocket** yields
  the WebSocket protocol as the picker outcome.
- FR-2.2 That outcome must be distinguishable from HTTP and from no choice.

#### FR-3: Dismiss / cancel outcome

- FR-3.1 Automated checks must prove that dismissing the picker without a
  selection yields no protocol choice.
- FR-3.2 No-choice must not be confused with HTTP or WebSocket.

#### FR-4: Hermetic CI

- FR-4.1 The new proofs must not open a live blocking popup that waits for
  a real user (or hangs the suite) in CI.
- FR-4.2 Existing injected-picker paths that already avoid that wait must
  remain valid.

#### FR-5: No product expansion

- FR-5.1 This task does not add picker options, change defaults, or change
  cancel semantics for end users.
- FR-5.2 If a new proof fails against current product behavior, treat it as
  a real defect and correct the product only as needed to restore the
  documented PYPOST-1157 outcomes.

### Non-Functional Requirements

- **NFR-1 Time-bounded suite:** New checks must finish within normal suite
  timeout expectations; no open-ended modal waits.
- **NFR-2 Regression signal:** A broken HTTP / WebSocket / cancel mapping
  must fail CI.
- **NFR-3 Isolation:** Proofs target the picker’s outcome contract; they do
  not require re-proving full presenter tab insertion (already covered
  elsewhere).
- **NFR-4 Stability:** Checks must be deterministic under parallel
  `make test` (no flake from a real blocking popup).

### Constraints and Assumptions

- Parent epic: [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155).
- Origin: NON-BLOCKER follow-up 7 in
  `ai-tasks/PYPOST-1157/60-tech-debt.md`; Jira
  [PYPOST-1180](https://pypost.atlassian.net/browse/PYPOST-1180).
- Related story: [PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157)
  (picker UX and routing already shipped).
- The intended product outcomes (HTTP, WebSocket, cancel → no tab) are
  already correct for users; this task is verification debt, not a new UX
  feature.
- Live interactive popup coverage remains an intentional non-goal for CI
  (same hermetic constraint documented for PYPOST-1157).
- Menu construction coverage (order / default) remains in place and is not
  replaced by this work.

## Q&A

- **Why do this if presenter tests already inject a picker?**
  Injected stubs prove routing *given* a protocol; they do not prove the
  production picker still produces the right protocol (or none) from a
  confirm or dismiss.
- **Why not run a live blocking popup in CI?**
  A real modal wait blocks the Qt event loop and can hang the suite. CI
  must stay hermetic and time-bounded.
- **Does this change what users see?**
  No. Same labels, defaults, and cancel/confirm outcomes; stronger proof
  only.
- **Is MCP Client part of this ticket?**
  No. This debt item locks HTTP, WebSocket, and dismiss. MCP Client product
  work is tracked elsewhere (for example PYPOST-1165).
- **What if construction tests already cover the menu?**
  Construction proves order and default selection, not the confirm/dismiss
  → outcome mapping. Both layers are needed.
- **Is a product bug fix in scope if a proof fails?**
  Yes, only to restore the existing PYPOST-1157 outcome contract — not to
  expand features.

## References

- [PYPOST-1180](https://pypost.atlassian.net/browse/PYPOST-1180) — this debt
  item
- [PYPOST-1157](https://pypost.atlassian.net/browse/PYPOST-1157) — blank-tab
  protocol picker story
- [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155) — parent epic
- `ai-tasks/PYPOST-1157/60-tech-debt.md` — follow-up 7 (source)
- `ai-tasks/PYPOST-1157/10-requirements.md` — picker business contract
