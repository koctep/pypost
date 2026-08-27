# PYPOST-1206: Document attach path, trust boundary, and lifecycle

## Goals

Epic [PYPOST-991](https://pypost.atlassian.net/browse/PYPOST-991)
([PYPOST-952](https://pypost.atlassian.net/browse/PYPOST-952) TD-2) needs
operators and implementers to understand how the agent-UI MCP sidecar binds
to an **already-running desktop PyPost** (attach) versus the shipped
**spawn-session** path (sidecar owns its own session). Today, developer docs
state that attach is unsupported and only point at follow-up tickets; they do
not define the attach path, trust relative to product MCP and local-host
posture, or attach lifecycle outcomes.

**Business goal:** Publish clear developer documentation so operators can
distinguish attach from spawn-session, know the trust implications of driving
a live desktop, and understand success/fail/detach/exit behavior — before
(or as soft contract for) attach capability
([PYPOST-1207](https://pypost.atlassian.net/browse/PYPOST-1207) / ATTACH-2).

**Why this matters:** Without a documented attach path and trust/lifecycle,
desktop-assist workflows remain ambiguous, attach implementation can drift
from operator expectations, and spawn-session limitation wording stays stale.

**Provisional ID:** ATTACH-1 (from
[PYPOST-1202](https://pypost.atlassian.net/browse/PYPOST-1202) decomposition).

## Programming Language

- **This task (PYPOST-1206):** English Markdown for developer documentation
  and Top-Down artifacts. Docs-only — no product runtime change.
- **Related product code (context only):** Python (desktop PyPost, agent-UI
  MCP sidecar, tests). Not modified by this story.

## User Stories

- As an **external MCP client operator**, I want documented attach versus
  spawn-session paths, so I know which path drives my already-open desktop
  versus a sidecar-owned session.
- As an **operator or security-conscious user**, I want trust relative to
  product MCP and local-host posture stated for attach, so I do not confuse
  UI drive with collection request tools or underestimate local privilege.
- As an **operator**, I want attach lifecycle outcomes (success, fail,
  detach, host exit, sidecar exit) documented, so I know what happens when
  binding starts, ends, or either side goes away.
- As a **maintainer**, I want spawn-session limitation wording updated, so
  `doc/dev` no longer only says “attach unsupported” without the ATTACH-1
  contract.
- As an **ATTACH-2 implementer**, I want ATTACH-1 docs as a soft contract,
  so capability work can align with (and later refine) documented outcomes.

## Definition of Done

PYPOST-1206 is done when:

1. Developer docs describe how operators use **attach** versus
   **spawn-session** (roles, when to choose each, high-level operator
   procedure at product level — not an unimplemented CLI design dump).
2. Trust relative to **product MCP** (request-tool surface) and **local-host
   posture** is stated for the agent-UI attach/sidecar surface.
3. Lifecycle documentation covers at least: attach **success**, attach
   **fail**, **detach**, **host exit**, and **sidecar exit**.
4. Existing **spawn-session limitation** wording in relevant `doc/dev`
   surfaces is updated to match the documented attach path / contract
   (replace or supersede the “attach not supported / tickets only” framing
   as appropriate for ATTACH-1 deliverables).
5. Non-goals below are respected: no attach implementation, no attach test
   suite, no PYPOST-990/992/993 work, no product IPC/transport catalog
   changes.
6. `ai-tasks/PYPOST-1206/10-requirements.md` and `00-roadmap.md` exist and
   Step 1 has passed its acceptance gate.

## Task Description

### Problem

Shipped agent-UI MCP (stdio sidecar) always owns its own `AgentAppSession`.
Operators cannot rely on docs for attaching to an already-running desktop:
limitations say attach is unsupported and defer to
[PYPOST-991](https://pypost.atlassian.net/browse/PYPOST-991) children.
Epic acceptance still requires a **documented** attach path, trust, and
lifecycle (capability and tests are sibling stories).

### Current state (inventory)

- **Agent-UI MCP sidecar docs** —
  `doc/dev/agent_ui_actions_mcp.md` describes spawn-session entry points and
  Limitations: attach unsupported; pointers to PYPOST-1206/1207/1208.
  Gap: no attach-vs-spawn operator narrative; no lifecycle; limitation
  wording not yet the ATTACH-1 contract.
- **Trust model docs** — `doc/dev/mcp_trust_model.md` covers product inbound
  MCP local-trust posture; notes agent-UI as a separate boundary without
  attach-specific operator guidance.
  Gap: attach trust relative to product MCP and local-host posture not
  spelled out for operators.
- **Agent lifecycle docs** — `doc/dev/agent_lifecycle.md` covers
  sidecar-owned / harness `AgentAppSession` launch → ready → shutdown.
  Gap: does not define attach bind/unbind or host/sidecar exit outcomes for
  a live desktop.
- **UI actions packaging** — `doc/dev/ui_actions.md` keeps UI tools off
  product `MCPServerImpl`.
  Gap: unchanged rule; docs must keep attach on the agent-UI surface, not
  expand product MCP blast radius.
- **Capability / tests** — ATTACH-2 (PYPOST-1207) and ATTACH-3 (PYPOST-1208)
  own implementation and verification.
  Gap: out of this story’s deliverables.

### Scope (this task)

- Document attach path versus spawn-session for operators in `doc/dev`
  (primary surface: agent-UI MCP docs; cross-links to trust / lifecycle /
  packaging docs as needed).
- State trust relative to product MCP and local-host posture for the
  agent-UI attach surface.
- Define attach lifecycle outcomes: success, fail, detach, host exit,
  sidecar exit (product/operator meaning, not protocol design).
- Update spawn-session limitation wording to align with the documented
  attach contract.
- Keep packaging separation: UI tools remain off product MCP catalog.

### Out of scope (this task)

- Implementing attach capability (**ATTACH-2** /
  [PYPOST-1207](https://pypost.atlassian.net/browse/PYPOST-1207)).
- Attach verification tests (**ATTACH-3** /
  [PYPOST-1208](https://pypost.atlassian.net/browse/PYPOST-1208)).
- [PYPOST-990](https://pypost.atlassian.net/browse/PYPOST-990) (HTTP
  transport for agent-UI MCP).
- [PYPOST-992](https://pypost.atlassian.net/browse/PYPOST-992) (spawn-session
  `call_tool` tests).
- [PYPOST-993](https://pypost.atlassian.net/browse/PYPOST-993) (seed
  injection for sidecar-owned session).
- Product IPC/transport changes or product HTTP MCP catalog changes.
- User-facing `doc/user/` docs (unless a later step explicitly requires a
  pointer).
- Redesigning interactive human UX beyond what documentation of attach
  requires.

### Functional Requirements

- **FR1:** Dev docs explain **spawn-session**: sidecar starts and owns its
  session; typical use (empty/offscreen session; not the operator’s already
  open desktop).
- **FR2:** Dev docs explain **attach**: bind agent-UI MCP to an
  already-running desktop PyPost so UI tools drive that live UI; when
  operators should choose attach over spawn-session.
- **FR3:** Docs state that attach and spawn-session are **both** valid
  paths; attach does not replace spawn-session.
- **FR4:** Trust section states that agent-UI attach/sidecar is a **separate
  trust surface** from product request-tool MCP; UI tools must not appear on
  product MCP.
- **FR5:** Trust section states **local-host posture** implications for
  attach (same-machine privilege / who can drive the live desktop), aligned
  in spirit with existing local-trust guidance for inbound MCP without
  merging the two surfaces.
- **FR6:** Lifecycle docs cover **attach success** (bound; UI tools apply to
  the live desktop).
- **FR7:** Lifecycle docs cover **attach fail** (not bound; operator-visible
  meaning of failure at product level).
- **FR8:** Lifecycle docs cover **detach** (binding ends; desktop and/or
  sidecar continue per documented rules).
- **FR9:** Lifecycle docs cover **host exit** (desktop PyPost ends while
  sidecar/client may still be present).
- **FR10:** Lifecycle docs cover **sidecar exit** (sidecar ends while
  desktop may still be present).
- **FR11:** Spawn-session **limitation wording** in relevant `doc/dev`
  pages is updated so it no longer leaves attach as “unsupported + ticket
  pointers only” without the ATTACH-1 path/trust/lifecycle content.
- **FR12:** Docs may note that **runtime attach capability** lands in
  ATTACH-2 / PYPOST-1207 if not yet shipped, without omitting the
  operator-facing contract required by FR1–FR11.

### Non-Functional Requirements

- **NFR-1 Clarity:** An operator reading `doc/dev` can tell attach from
  spawn-session without reading Jira or architecture artifacts.
- **NFR-2 Consistency:** Trust and packaging statements stay consistent with
  `mcp_trust_model.md` / `ui_actions.md` separation rules.
- **NFR-3 Traceability:** Docs remain linkable to epic PYPOST-991 and
  siblings PYPOST-1207 / PYPOST-1208 where useful.
- **NFR-4 Soft contract:** ATTACH-1 wording may be refined when ATTACH-2
  lands; prefer stable outcome language over speculative mechanism detail.
- **NFR-5 Lint:** Delivered Markdown meets project doc lint / link norms
  used for `doc/dev`.

### Constraints and Assumptions

- Spawn-session remains valid after attach is documented and later
  implemented.
- ATTACH-1 is a **soft** prerequisite for ATTACH-2 (contract may iterate).
- This story does not choose IPC or transport mechanisms; product-level
  outcomes only.
- Related product language is Python; this story changes English Markdown
  only.
- Primary doc surfaces to update or cross-link:
  `doc/dev/agent_ui_actions_mcp.md`, `doc/dev/mcp_trust_model.md`,
  `doc/dev/agent_lifecycle.md`, `doc/dev/ui_actions.md` (as needed for
  consistency — not all four must gain large new sections).

### Main Entities (business)

| Entity | Role |
| --- | --- |
| Desktop PyPost | Interactive app the operator already has open |
| Agent-UI MCP sidecar | Out-of-process UI-action MCP surface |
| Spawn-session path | Sidecar owns its own session (shipped today) |
| Attach path | Bind sidecar/client to live desktop session |
| Product MCP | Separate inbound request-tool surface (not UI drive) |
| Trust boundary | Who may use attach and what power it grants |
| Attach lifecycle | Success, fail, detach, host exit, sidecar exit |
| Operator | Person or agent client configuring MCP to drive UI |

### Doc outcome mapping (acceptance)

| Acceptance criterion | Requirement coverage |
| --- | --- |
| Attach vs spawn-session described | FR1–FR3, FR12 |
| Trust vs product MCP and local-host | FR4–FR5 |
| Lifecycle success/fail/detach/exits | FR6–FR10 |
| Spawn-session limitation wording updated | FR11 |

## Q&A

- Q: Why document attach before it is implemented?
  A: Epic PYPOST-991 requires a documented path and trust/lifecycle;
  ATTACH-1 is the soft contract for ATTACH-2 and clears stale “unsupported
  only” limitation wording.
- Q: Does this story implement attach?
  A: **No** — ATTACH-2 / PYPOST-1207 owns capability.
- Q: Does this story add attach tests?
  A: **No** — ATTACH-3 / PYPOST-1208 owns verification.
- Q: Must attach replace spawn-session?
  A: **No** — both paths remain.
- Q: May UI tools move onto product MCP for attach?
  A: **No** — packaging separation from PYPOST-918/952 stays mandatory.
- Q: Is IPC/transport designed here?
  A: **No** — Step 1 forbids architecture; later steps may name doc
  structure only, not product HTTP MCP catalog changes.
- Q: Which docs are in play?
  A: Primarily `doc/dev/agent_ui_actions_mcp.md`, with trust/lifecycle/
  packaging cross-links as needed
  (`mcp_trust_model.md`, `agent_lifecycle.md`, `ui_actions.md`).

## References

- [PYPOST-1206](https://pypost.atlassian.net/browse/PYPOST-1206) — this story
  (ATTACH-1)
- [PYPOST-991](https://pypost.atlassian.net/browse/PYPOST-991) — parent epic
- [PYPOST-1202](https://pypost.atlassian.net/browse/PYPOST-1202) —
  decompose story / ATTACH-1..3 mapping
- [PYPOST-1207](https://pypost.atlassian.net/browse/PYPOST-1207) — ATTACH-2
  capability (out of scope)
- [PYPOST-1208](https://pypost.atlassian.net/browse/PYPOST-1208) — ATTACH-3
  tests (out of scope)
- [PYPOST-952](https://pypost.atlassian.net/browse/PYPOST-952) — shipped
  stdio agent-UI MCP
- `ai-tasks/PYPOST-1202/10-requirements.md` — ATTACH-1 context
- `doc/dev/agent_ui_actions_mcp.md` — current sidecar docs / limitations
- `doc/dev/mcp_trust_model.md` — product MCP local-trust posture
- `doc/dev/agent_lifecycle.md` — session launch/ready/shutdown
- `doc/dev/ui_actions.md` — UI-action packaging contract
