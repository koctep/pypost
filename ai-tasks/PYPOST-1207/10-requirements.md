# PYPOST-1207: Attach agent-UI MCP to already-running desktop PyPost

## Goals

Epic [PYPOST-991](https://pypost.atlassian.net/browse/PYPOST-991)
([PYPOST-952](https://pypost.atlassian.net/browse/PYPOST-952) TD-2) needs
operators and external agents to **drive an already-running desktop PyPost**
through the agent-UI MCP surface. Today the shipped sidecar only supports
**spawn-session**: it owns its own session (typically empty/offscreen), so it
cannot apply the existing UI-action catalog to the operator’s live window
(collections, tabs, and UI state).

**Business goal:** Deliver the **attach** capability so an operator/agent can
bind agent-UI MCP to a running desktop instance, drive that live UI with the
existing UI-action tools, keep spawn-session working, and keep UI tools off
product MCP.

**Why this matters:** Without attach, desktop-assist workflows require a
second nested app and lose the operator’s real workspace. Attach unlocks
driving the interactive desktop the human already has open.

**Provisional ID:** ATTACH-2 (from
[PYPOST-1202](https://pypost.atlassian.net/browse/PYPOST-1202) decomposition).
Soft-depends on ATTACH-1 /
[PYPOST-1206](https://pypost.atlassian.net/browse/PYPOST-1206) (docs Done;
contract may iterate when attach lands).

## Programming Language

- **This task (PYPOST-1207):** Python (desktop PyPost, agent-UI MCP sidecar,
  related tests). English Markdown for Top-Down artifacts and any doc
  refinements required when capability lands.

## User Stories

- As an **external MCP client operator**, I want to bind agent-UI MCP to my
  already-open desktop PyPost, so UI tools drive that live window instead of
  a sidecar-owned empty/offscreen session.
- As an **operator or agent**, I want the **existing** UI-action catalog to
  apply to the attached desktop, so I do not need a separate tool set for
  attach versus spawn-session.
- As an **automation user**, I want the **spawn-session** path to keep
  working, so isolated/CI/offscreen sessions remain available.
- As a **security-conscious maintainer**, I want UI-action tools to remain
  **off** product MCP, so attach does not expand the product request-tool
  blast radius.
- As an **ATTACH-3 verifier**, I want attach outcomes to match the ATTACH-1
  soft contract (success, fail, detach, host/sidecar exit), so tests and
  docs can agree once capability ships.

## Definition of Done

PYPOST-1207 is done when:

1. An operator/agent can **bind** agent-UI MCP to an **already-running**
   desktop PyPost instance (attach path is runnable, not docs-only).
2. After successful attach, the **existing** UI-action catalog drives that
   **live** desktop UI (same product-level tools operators already know).
3. The **spawn-session** path still works (sidecar-owned session remains a
   valid, selectable path).
4. UI-action tools remain **off** product MCP (separate agent-UI surface;
   packaging separation preserved).
5. Attach lifecycle outcomes align at product level with the ATTACH-1 soft
   contract in `doc/dev/agent_ui_actions_mcp.md` (success, fail, detach,
   host exit, sidecar exit) — mechanism is out of Step 1; behavior must
   match documented operator meaning.
6. Non-goals below are respected: primary docs/trust owned by PYPOST-1206
   (may refine when attach lands); full verification suite owned by
   PYPOST-1208; no PYPOST-990/992/993; no mounting UI tools on product MCP.
7. `ai-tasks/PYPOST-1207/10-requirements.md` and `00-roadmap.md` exist and
   Step 1 has passed its acceptance gate.

## Task Description

### Problem

Shipped agent-UI MCP always launches and owns its own session. Operators
cannot bind that surface to a desktop they already run, so external agents
cannot assist against real collections/tabs/UI state. ATTACH-1 documented
the path, trust, and lifecycle as a soft contract; this story must make
attach **real** while preserving spawn-session and packaging separation.

### Current state (inventory)

- **Agent-UI MCP sidecar** — Stdio agent-UI surface ships UI tools and
  spawn-session entry. Gap: no runtime attach-to-running-desktop mode.
- **Session ownership** — Sidecar owns its session today. Gap: cannot reuse
  the interactive desktop the operator already has open.
- **UI-action catalog** — Existing `ui_*` tools drive sidecar-owned UI.
  Gap: same catalog must drive an attached live desktop after bind.
- **Product MCP** — Request tools only; UI tools forbidden. Gap: unchanged;
  attach must stay on the agent-UI trust surface.
- **Docs (ATTACH-1 Done)** — `doc/dev/agent_ui_actions_mcp.md` documents
  attach vs spawn-session, trust, lifecycle, and notes runtime attach is
  this story. Gap: capability note still says attach not shipped.
- **Verification** — ATTACH-3 / PYPOST-1208 owns tests as feasible.
  Gap: out of this story’s primary deliverables (basic proof may appear
  during development; full suite is sibling).

### Scope (this task)

- Deliver runtime **attach**: bind agent-UI MCP to an already-running
  desktop PyPost so UI tools apply to that live UI.
- Reuse the **existing** UI-action catalog for the attached desktop (no
  separate attach-only tool product).
- Preserve **spawn-session** as a working path alongside attach.
- Preserve **packaging separation**: UI tools stay off product MCP.
- Honor ATTACH-1 product-level lifecycle meanings (success, fail, detach,
  host exit, sidecar exit).
- Allow doc refinements when capability lands (soft-contract iteration);
  primary docs/trust work remains ATTACH-1 ownership.

### Out of scope (this task)

- Primary attach path / trust / lifecycle **documentation** as a first-time
  contract (**ATTACH-1** /
  [PYPOST-1206](https://pypost.atlassian.net/browse/PYPOST-1206)) — already
  Done; this story may refine docs when attach ships.
- Full attach **verification suite** / CI vs manual gaps (**ATTACH-3** /
  [PYPOST-1208](https://pypost.atlassian.net/browse/PYPOST-1208)).
- [PYPOST-990](https://pypost.atlassian.net/browse/PYPOST-990) (HTTP
  transport for agent-UI MCP).
- [PYPOST-992](https://pypost.atlassian.net/browse/PYPOST-992) (spawn-session
  `call_tool` tests).
- [PYPOST-993](https://pypost.atlassian.net/browse/PYPOST-993) (seed
  injection for sidecar-owned session).
- Mounting UI tools on product MCP (forbidden).
- Redesigning the interactive human UX beyond what attachability requires.
- Choosing or documenting IPC/transport mechanisms in this Step 1 artifact
  (architecture owns that later).

### Functional Requirements

- **FR1:** An operator/agent can start (or keep) a **desktop PyPost** running
  and bind the agent-UI MCP surface to that instance (attach).
- **FR2:** On **attach success**, UI-action tool calls apply to the **bound
  live desktop**, not to a fresh sidecar-owned empty session.
- **FR3:** On **attach fail**, the surface is **not bound**; failure is
  operator-visible at product level (aligned with ATTACH-1 meaning).
- **FR4:** The **existing** UI-action catalog (same product-level tools as
  spawn-session) drives the attached desktop after success.
- **FR5:** **Spawn-session** remains available and functional as a separate
  path (sidecar owns its own session when that path is chosen).
- **FR6:** Operators can choose attach when they need the live desktop, and
  spawn-session when they need an isolated/sidecar-owned session; attach
  does **not** replace spawn-session.
- **FR7:** **Detach** ends the binding without requiring that either the
  desktop or the sidecar be destroyed by default (ATTACH-1 meaning).
- **FR8:** **Host exit** (desktop ends) ends the attach binding; sidecar or
  client may remain without implying a live bound desktop.
- **FR9:** **Sidecar exit** ends the attach binding from the sidecar side;
  the desktop is not implied destroyed.
- **FR10:** UI-action tools must **not** appear on product MCP; attach stays
  on the agent-UI surface.
- **FR11:** After attach ships, developer docs that still say runtime attach
  is unavailable must be updated so capability status matches behavior
  (refinement of ATTACH-1 soft contract, not a new docs epic).

### Non-Functional Requirements

- **NFR-1 Local-host posture:** Attach assumes same-machine privilege to
  drive the live desktop; it remains a separate trust surface from product
  request-tool MCP (consistent with ATTACH-1 / trust docs).
- **NFR-2 Continuity:** Spawn-session behavior used today must not regress
  when attach is added.
- **NFR-3 Catalog parity:** Attached desktop is driven by the same
  operator-facing UI-action tool set as the sidecar path (no silent
  tool-set fork).
- **NFR-4 Packaging:** Production packaging rules that keep UI tools off
  product MCP remain enforced.
- **NFR-5 Soft-contract alignment:** Product-visible attach outcomes match
  documented ATTACH-1 meanings; docs may iterate when mechanism lands.
- **NFR-6 Traceability:** Work remains under epic PYPOST-991 with clear
  sibling boundaries (1206 docs, 1208 tests).

### Constraints and Assumptions

- Language is **Python** for product changes.
- ATTACH-1 / PYPOST-1206 is **Done** and is a **soft** prerequisite;
  contract may iterate when this capability lands.
- Spawn-session remains valid after attach ships.
- Full automated attach verification is **ATTACH-3**; this story owns
  capability, not the complete “tests as feasible” suite.
- Production UI must not gain a hard dependency on agent packaging beyond
  what attachability requires (constraint for architecture/development;
  not designed here).
- Step 1 does **not** choose IPC, transport, CLI flags, or wire formats.

### Main Entities (business)

| Entity | Role |
| --- | --- |
| Desktop PyPost | Interactive app the operator already has open |
| Agent-UI MCP surface | Out-of-process UI-action MCP surface (not product MCP) |
| Spawn-session path | Sidecar owns its own session (shipped today) |
| Attach path | Bind agent-UI MCP to the live desktop session |
| UI-action catalog | Existing operator-facing UI tools (`ui_*`) |
| Product MCP | Separate inbound request-tool surface (not UI drive) |
| Attach binding | Active link between agent-UI surface and live desktop |
| Attach lifecycle | Success, fail, detach, host exit, sidecar exit |
| Operator / agent client | Configures MCP and drives UI via tools |

### Acceptance mapping

| Acceptance criterion (Jira) | Requirement coverage |
| --- | --- |
| Bind agent-UI MCP to running desktop | FR1–FR3 |
| Existing UI-action catalog drives live UI | FR2, FR4, NFR-3 |
| Spawn-session path still works | FR5–FR6, NFR-2 |
| UI tools remain off product MCP | FR10, NFR-1, NFR-4 |

## Q&A

- Q: Why is this not a docs-only story?
  A: ATTACH-1 documented the contract; ATTACH-2 delivers the missing
  runtime bind so operators can drive a live desktop.
- Q: Does attach replace spawn-session?
  A: **No** — both paths remain valid.
- Q: May UI tools move onto product MCP for attach?
  A: **No** — packaging separation from PYPOST-918/952 stays mandatory.
- Q: Who owns attach tests?
  A: **ATTACH-3** / PYPOST-1208 owns the full verification suite; this
  story owns capability.
- Q: Who owns the attach trust/lifecycle narrative?
  A: **ATTACH-1** / PYPOST-1206 (Done). This story may refine docs when
  capability lands.
- Q: Is IPC/transport chosen here?
  A: **No** — Step 1 forbids architecture; outcomes only.
- Q: What catalog drives the attached desktop?
  A: The **existing** UI-action catalog — same product-level tools as
  spawn-session, applied to the live bound desktop.
- Q: Soft dependency on PYPOST-1206?
  A: Yes — docs Done; treat as soft contract that may iterate with
  ATTACH-2.

## References

- [PYPOST-1207](https://pypost.atlassian.net/browse/PYPOST-1207) — this story
  (ATTACH-2)
- [PYPOST-991](https://pypost.atlassian.net/browse/PYPOST-991) — parent epic
- [PYPOST-1202](https://pypost.atlassian.net/browse/PYPOST-1202) —
  decompose story / ATTACH-1..3 mapping
- [PYPOST-1206](https://pypost.atlassian.net/browse/PYPOST-1206) — ATTACH-1
  docs (soft dependency, Done)
- [PYPOST-1208](https://pypost.atlassian.net/browse/PYPOST-1208) — ATTACH-3
  tests (out of scope)
- [PYPOST-952](https://pypost.atlassian.net/browse/PYPOST-952) — shipped
  stdio agent-UI MCP
- `ai-tasks/PYPOST-1202/10-requirements.md` — ATTACH-2 context
- `ai-tasks/PYPOST-1206/10-requirements.md` — soft-contract requirements
- `doc/dev/agent_ui_actions_mcp.md` — attach path / trust / lifecycle
- `doc/dev/ui_actions.md` — UI-action packaging contract
- `doc/dev/mcp_trust_model.md` — separate trust surfaces
- `doc/dev/agent_lifecycle.md` — session and attach outcomes
