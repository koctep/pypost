# PYPOST-1183: Prove MCP Client stub title, identity, and last-tab count

## Goals

[PYPOST-1165](https://pypost.atlassian.net/browse/PYPOST-1165) (MCP-TM-1)
already ships a blank **MCP Client** workspace tab: users who choose that
protocol from the blank-tab picker get a dedicated stub tab titled
**New MCP Client**, with a stable widget identity so tooling and tests can
find it, and with the stub counted as a real workspace tab when deciding
whether the strip is empty.

Those product edges are live in production but not locked by automated
checks. A regression could rename the stub, lose its identity, or treat an
MCP-only (or MCP-plus-closing-last-HTTP) strip as “empty” and auto-create a
new HTTP tab — while existing tests still pass.

This debt item closes that verification gap so CI fails if stub title,
widget identity, or last-tab counting drift from the PYPOST-1165 contract.
End users get no new feature; maintainers get trustworthy proof.

**Implementation language**: Python (PyPost desktop client automated tests;
no new runtime language).

## User Stories

- As a **maintainer**, I want automated proof that opening a blank MCP
  Client tab shows the tab title **New MCP Client**, so users keep a
  recognizable non-HTTP label after an explicit MCP Client choice.
- As a **maintainer**, I want automated proof that the MCP Client stub
  keeps its stable widget identity (`pypost_mcp_client_tab_page`), so
  finders and later MCP draft work can locate the same page.
- As a **maintainer**, I want automated proof that closing the last HTTP
  tab while an MCP Client stub remains does **not** auto-open a new blank
  HTTP tab, so an MCP-only strip is not treated as an empty workspace.
- As a **maintainer**, I want the suite’s notion of “request / workspace
  tabs that count” to match production (HTTP, WebSocket, and MCP Client),
  so a drop of the stub from the production count cannot hide behind a
  narrower test helper.
- As a **CI runner / developer**, I want any MCP Client stub construction
  checks to be time-bounded and free of the MCP SDK, so the suite stays
  hermetic and fast.
- As an **end user** of blank MCP Client tabs, I want no change to title,
  identity, or close-last-tab behavior — only stronger automated proof
  that those edges stay correct.

## Definition of Done

PYPOST-1183 is done when:

1. Automated checks prove that after opening a blank MCP Client tab, the
   tab strip text is **New MCP Client**.
2. Automated checks prove that same tab page’s widget identity is
   `pypost_mcp_client_tab_page`.
3. Automated checks prove that closing the last HTTP tab while an MCP
   Client stub remains does **not** trigger creation of a new blank HTTP
   tab.
4. The automated suite’s count of tabs that keep the workspace “non-empty”
   includes HTTP, WebSocket, and MCP Client stubs — aligned with
   production so the stub cannot be silently ignored.
5. Optional construction-only coverage for the MCP Client stub page is
   allowed; if added, it must be time-bounded and must not pull in the
   MCP SDK.
6. Existing PYPOST-1165 picker, routing, and metrics coverage remains
   green.
7. Product stub behavior for real users is unchanged except as required
   to restore the verified PYPOST-1165 contract; no new end-user feature
   is in scope.
8. Sibling epic work (MCP draft shell, close-last-tab picker reuse, user
   docs, session restore for MCP) stays out of scope except as context.

## Task Description

### Programming Language

Python — PyPost desktop client and its automated test suite.

### Problem

PYPOST-1165 delivered the third picker item **MCP Client**, a dedicated
stub tab, and last-tab counting that treats the stub as a real workspace
tab. Its tests already prove picker construction, confirm routing to an
MCP Client stub (not HTTP / WebSocket), and metrics for protocol
`mcp_client`.

What remains unproven for this debt item:

| Product edge (already shipped) | Gap today |
| --- | --- |
| Tab title **New MCP Client** | Not asserted after blank MCP open |
| Widget identity `pypost_mcp_client_tab_page` | Not asserted |
| Closing last HTTP while MCP stub remains | Not proven to avoid auto-new HTTP |
| Suite “non-empty tab” count vs production | Helper can ignore WebSocket / MCP |

Without those locks, a broken title, identity, or count could pass CI
while broader MCP routing tests still pass.

### Business Need

Engineers need a hermetic regression signal that the MCP Client stub still
presents the intended title and identity, and that an MCP stub still
counts toward a non-empty workspace when HTTP tabs are gone. That
protects the PYPOST-1165 business contract: MCP Client is a first-class
blank-tab kind, visibly distinct from HTTP, and not silently replaced by
an auto-opened HTTP tab when it is the remaining content. End users do
not get a new feature; maintainers get trustworthy proof.

### Scope (this task)

**In scope**

- Automated proof of tab title **New MCP Client** after opening a blank
  MCP Client tab.
- Automated proof of widget identity `pypost_mcp_client_tab_page` for
  that stub page.
- Automated proof that closing the last HTTP tab while an MCP Client stub
  remains does not auto-create a new blank HTTP tab.
- Aligning the suite’s non-empty workspace tab count with production
  (HTTP, WebSocket, and MCP Client).
- Optional construction-only MCP Client stub checks that are time-bounded
  and do not use the MCP SDK.

**Out of scope**

- Changing stub title, widget identity, picker labels, or close-last-tab
  product rules (unless a new assertion reveals a real defect against the
  PYPOST-1165 contract).
- MCP Client draft shell (URL bar, Connect, tools, restore) —
  [PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166).
- Close-last-tab / empty-workspace picker reuse (still HTTP-only
  fallback product rule) —
  [PYPOST-1159](https://pypost.atlassian.net/browse/PYPOST-1159).
- Session persist / restore of MCP tabs (intentional omission until
  PYPOST-1166).
- Blank-tab picker HTTP / WebSocket / cancel outcome mapping —
  [PYPOST-1180](https://pypost.atlassian.net/browse/PYPOST-1180).
- User documentation rewrite —
  [PYPOST-1168](https://pypost.atlassian.net/browse/PYPOST-1168).
- MCP SDK, network, or outbound connect / list_tools / call_tool work.
- Sibling suite flakes (for example
  [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115)).

### Main Entities (Business Perspective)

- **MCP Client stub tab** — Placeholder blank workspace tab opened when
  the user chooses **MCP Client**; not an HTTP request tab.
- **Tab title** — User-visible strip label; for the stub, **New MCP
  Client**.
- **Widget identity** — Stable page id
  `pypost_mcp_client_tab_page` used to locate the stub page.
- **Non-empty workspace tab count** — Which open tabs prevent treating
  the strip as empty (HTTP, WebSocket, and MCP Client stubs).
- **Last-HTTP close with MCP remaining** — Closing the final HTTP tab
  while an MCP Client stub is still open must leave the stub and must
  not auto-open a new blank HTTP tab.
- **CI verification** — Automated proof of the above without MCP SDK or
  open-ended waits.

### Functional Requirements

#### FR-1: Stub tab title

- FR-1.1 After opening a blank MCP Client tab, automated checks must
  prove the tab strip text is **New MCP Client**.
- FR-1.2 That title must remain distinguishable from blank HTTP and
  WebSocket tab titles already used by the product.

#### FR-2: Stub widget identity

- FR-2.1 After opening a blank MCP Client tab, automated checks must
  prove the stub page’s widget identity is
  `pypost_mcp_client_tab_page`.
- FR-2.2 That identity must be stable enough for later MCP draft work to
  keep the same page locator (PYPOST-1166 context; not implemented here).

#### FR-3: Last-HTTP close with MCP remaining

- FR-3.1 Automated checks must prove that closing the last HTTP tab while
  an MCP Client stub remains does **not** create a new blank HTTP tab.
- FR-3.2 An MCP-only strip after that close must still be treated as
  non-empty for the purpose of that auto-create decision.

#### FR-4: Suite count aligned with production

- FR-4.1 The automated suite’s helper (or equivalent) used to count
  non-empty workspace tabs must include HTTP, WebSocket, and MCP Client
  stubs — the same kinds production uses for that decision.
- FR-4.2 A regression that drops MCP Client from the production count
  must be detectable by the suite (the helper must not silently ignore
  the stub).

#### FR-5: Optional construction-only stub coverage

- FR-5.1 Construction-only checks for the MCP Client stub page are
  optional for this ticket.
- FR-5.2 If added, they must not require the MCP SDK and must be
  time-bounded like the rest of the suite.

#### FR-6: No product expansion

- FR-6.1 This task does not add picker options, change stub chrome beyond
  the existing contract, or change empty-workspace product policy for
  other protocols.
- FR-6.2 If a new proof fails against current product behavior, treat it
  as a real defect and correct the product only as needed to restore the
  documented PYPOST-1165 edges.

### Non-Functional Requirements

- **NFR-1 Time-bounded suite:** New checks must finish within normal suite
  timeout expectations; no open-ended waits and no MCP SDK startup.
- **NFR-2 Regression signal:** Broken stub title, widget identity, or
  last-HTTP-close-with-MCP-remaining behavior must fail CI.
- **NFR-3 Isolation:** Proofs target stub presentation and last-tab
  counting; they do not re-prove picker menu construction or metrics
  (already covered by PYPOST-1165).
- **NFR-4 Hermetic CI:** Optional construction checks must not depend on
  network or the MCP SDK.
- **NFR-5 Stability:** Checks must be deterministic under parallel
  `make test`.

### Constraints and Assumptions

- Parent epic: [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155).
- Origin: NON-BLOCKER follow-up 2 in
  `ai-tasks/PYPOST-1165/60-tech-debt.md`; Jira
  [PYPOST-1183](https://pypost.atlassian.net/browse/PYPOST-1183).
- Related story: [PYPOST-1165](https://pypost.atlassian.net/browse/PYPOST-1165)
  (stub title, identity, and count already shipped in production).
- The intended product edges are already correct for users; this task is
  verification debt, not a new UX feature.
- Empty-workspace auto-create remains HTTP-only by product policy
  (PYPOST-1159); this ticket only locks that an MCP stub counts so
  MCP-remaining strips are not treated as empty.
- Construction-only MCP Client stub coverage is optional, not mandatory
  for Done if FR-1 through FR-4 are met.

## Q&A

- **Why do this if presenter tests already open an MCP Client stub?**
  Existing checks prove type / routing. They do not lock the visible
  title, widget identity, or last-HTTP-close-with-MCP-remaining count
  edge.
- **Why mention widget identity in requirements?**
  It is part of the shipped PYPOST-1165 stub contract and the locator
  later MCP draft work is expected to keep; losing it is a product
  regression, not an implementation detail of this ticket.
- **Does this change what users see?**
  No. Same title, identity, and close behavior; stronger proof only.
- **Is MCP draft shell part of this ticket?**
  No. That is PYPOST-1166. This ticket only verifies the existing stub
  edges.
- **Must construction-only stub tests be added?**
  No. They are optional. Title, identity, last-HTTP-close, and count
  alignment are mandatory.
- **Is a product bug fix in scope if a proof fails?**
  Yes, only to restore the existing PYPOST-1165 contract — not to expand
  features.

## References

- [PYPOST-1183](https://pypost.atlassian.net/browse/PYPOST-1183) — this
  debt item
- [PYPOST-1165](https://pypost.atlassian.net/browse/PYPOST-1165) — MCP
  Client picker + stub story
- [PYPOST-1155](https://pypost.atlassian.net/browse/PYPOST-1155) — parent
  epic
- [PYPOST-1166](https://pypost.atlassian.net/browse/PYPOST-1166) — MCP
  Client draft shell (out of scope)
- [PYPOST-1159](https://pypost.atlassian.net/browse/PYPOST-1159) —
  close-last-tab picker reuse (out of scope)
- `ai-tasks/PYPOST-1165/60-tech-debt.md` — follow-up 2 (source)
- `ai-tasks/PYPOST-1165/10-requirements.md` — stub business contract
