# PYPOST-1202: Decompose epic — attach sidecar to running desktop PyPost

## Goals

Epic [PYPOST-991](https://pypost.atlassian.net/browse/PYPOST-991)
([PYPOST-952](https://pypost.atlassian.net/browse/PYPOST-952) TD-2) asks for the
ability to attach the agent-UI MCP sidecar to an **already-running desktop
PyPost**, not only to a fresh session the sidecar owns. That epic was promoted
from Debt because its estimate (8 SP) exceeded the SP>6 threshold; story points
were cleared on the epic. This story
([PYPOST-1202](https://pypost.atlassian.net/browse/PYPOST-1202)) exists so the
epic can be split into **implementable child issues** (each ≤5 SP preferred),
each sized for a full Top-Down cycle (Steps 1–8).

**Business goal:** Planners and implementers get clear, separately deliverable
slices that together satisfy PYPOST-991 acceptance (documented attach path;
trust and lifecycle defined; tests as feasible), without one oversized ticket
blocking sprint flow.

**Why attach matters (parent epic):** Today the shipped stdio agent-UI MCP
sidecar ([PYPOST-952](https://pypost.atlassian.net/browse/PYPOST-952)) always
launches its own `AgentAppSession` (typically empty, often offscreen). External
agents cannot drive the operator’s **already-open** desktop PyPost (real
collections, tabs, and UI state). Attach unlocks desktop-assist workflows
beyond a second nested app.

## Programming Language

- **This task (PYPOST-1202):** English Markdown planning artifacts and Jira
  issue creation (no product code change required for decomposition itself).
- **Child stories under PYPOST-991:** Python (PyPost desktop, agent package,
  tests), with English Markdown for developer docs.

## User Stories

- As a **sprint planner**, I want PYPOST-991 broken into ≤5 SP children with
  clear acceptance criteria, so each can enter Top-Down without re-estimating
  an 8 SP blob.
- As an **implementer**, I want each child scoped to one primary outcome
  (contract/docs, attach capability, or verification), so Steps 1–8 stay
  coherent.
- As an **external MCP client operator**, I want the future attach work to
  preserve a documented path and defined trust/lifecycle, so I can safely
  drive a live desktop without confusing it with product HTTP MCP.
- As a **maintainer**, I want sibling PYPOST-952 follow-ups (HTTP transport,
  seed injection, spawn-session call_tool tests) left out of this epic, so
  attach decomposition stays focused.

## Definition of Done

PYPOST-1202 is done when:

1. Epic PYPOST-991 scope is inventoried against current shipped behavior and
   documented limitations.
2. Natural work slices are identified and recorded as proposed children
   (provisional IDs ATTACH-1 … ATTACH-3) with summaries, preferred SP ≤5,
   dependencies, and acceptance criteria.
3. Out-of-epic siblings and explicit non-goals are listed.
4. Child Jira issues are created under PYPOST-991 with clear acceptance
   criteria — done in Step 4:
   [PYPOST-1206](https://pypost.atlassian.net/browse/PYPOST-1206),
   [PYPOST-1207](https://pypost.atlassian.net/browse/PYPOST-1207),
   [PYPOST-1208](https://pypost.atlassian.net/browse/PYPOST-1208).
5. Each child is suitable for its own Top-Down Steps 1–8 (single primary
   outcome; testable or docs-verifiable acceptance).
6. `ai-tasks/PYPOST-1202/10-requirements.md` and `00-roadmap.md` exist and
   Step 1 has passed its acceptance gate.

## Task Description

### Problem

PYPOST-991 is an oversized epic: attach agent-UI MCP to a running desktop
PyPost, with documented path, trust/lifecycle, and tests as feasible. As a
single ticket it exceeds the preferred ≤5 SP top-down unit. At Step 1
inventory time only PYPOST-1202 sat under the epic; implementation children
PYPOST-1206 / PYPOST-1207 / PYPOST-1208 were created in Step 4.

### Current state (inventory)

- **Agent-UI MCP sidecar** — Stdio entry
  (`pypost-agent-ui-mcp` / module / make target) ships UI tools.
  Gap: no attach-to-running-desktop mode.
- **Session ownership** — Sidecar **owns** `AgentAppSession`.
  Gap: cannot reuse interactive desktop session.
- **Product MCP** — `MCPServerImpl` request tools; UI tools forbidden there.
  Gap: unchanged; attach must stay a separate trust surface.
- **Docs** — `doc/dev/agent_ui_actions_mcp.md` states attach unsupported.
  Gap: need documented attach path + trust/lifecycle.
- **Trust model docs** — Product inbound MCP local-trust posture documented.
  Gap: attach surface not yet defined as its own boundary.
- **Tests** — Sidecar list_tools / packaging covered; attach out of scope.
  Gap: “tests as feasible” still open.
- **Related debt** — PYPOST-990 HTTP transport; PYPOST-992 call_tool tests;
  PYPOST-993 seed. Gap: separate tickets — not this epic.

Epic acceptance (must be covered by the **set** of children, not each child):

- Documented attach path
- Trust and lifecycle defined
- Tests as feasible

### Scope (this task)

- Inventory epic vs shipped agent-UI MCP and docs.
- Propose ≤5 SP child slices with acceptance criteria and preferred SP.
- Record decisions so later steps can create Jira children under PYPOST-991.
- Keep wording at business/product level (no attach protocol design here).

### Out of scope (this task)

- Implementing attach capability in product code.
- Creating Jira children in Step 1 (deferred to later steps).
- Redesigning product `MCPServerImpl` or mounting UI tools there.
- Delivering PYPOST-990 / PYPOST-992 / PYPOST-993.
- Interactive human UX redesign beyond what attachability requires.
- User-facing `doc/user/` docs unless a child explicitly requires them.

### Functional Requirements (decomposition)

- FR1: Requirements name every proposed child with summary, preferred SP
  (Fibonacci ≤5), dependencies, and acceptance criteria.
- FR2: Together, children cover documented attach path, trust/lifecycle, and
  tests as feasible.
- FR3: Children exclude unrelated PYPOST-952 follow-ups.
- FR4: Each child is independently runnable through Top-Down Steps 1–8.
- FR5: Later steps create Story (or Debt) issues under parent PYPOST-991 with
  labels consistent with the epic (`agent`, `mcp`, and decomposition lineage
  as decided in architecture).

### Non-Functional Requirements

- **NFR-1 Clarity:** Child summaries and AC are unambiguous for estimation and
  review without reading PYPOST-952 architecture.
- **NFR-2 Size:** Preferred story points ≤5; avoid recreating an 8 SP child.
- **NFR-3 Traceability:** Provisional IDs map to Jira keys once created
  (record mapping in roadmap after creation).
- **NFR-4 Separation:** Attach remains outside product request-tool MCP
  catalog (inherit PYPOST-918 / PYPOST-952 packaging rule).

### Constraints and Assumptions

- Spawn-session sidecar remains valid; attach is an **additional** path.
- Original epic estimate was 8 SP; three children totaling about that effort
  is preferred over many micro-slices.
- “Tests as feasible” may allow documenting CI limits if full desktop attach
  cannot run in default offscreen CI — a child must still define what is
  proven automatically vs manually.
- Production UI must not gain a hard dependency on agent packaging beyond
  whatever attachability the architecture later chooses (constraint for
  children; not designed here).
- Autonomous decisions below stand unless review rejects them.

### Main Entities (business)

| Entity | Role |
| --- | --- |
| Desktop PyPost | Interactive app the operator already has open |
| Agent-UI MCP sidecar | Out-of-process UI-action MCP surface (stdio today) |
| Attach path | Operator/agent procedure to bind sidecar to live desktop |
| Spawn-session path | Current sidecar behavior (owns its own session) |
| Trust boundary | Who may attach and what power attach grants |
| Attach lifecycle | Connect, use, detach, and end-of-host/sidecar rules |
| Product MCP | Separate inbound request-tool surface (not UI drive) |

### Proposed Child Story Breakdown (under PYPOST-991)

Provisional IDs **ATTACH-1 … ATTACH-3** mapped to Jira Stories created under
PYPOST-991 in Step 4 of PYPOST-1202.

| Provisional ID | Jira key | Browse |
| --- | --- | --- |
| ATTACH-1 | [PYPOST-1206](https://pypost.atlassian.net/browse/PYPOST-1206) | https://pypost.atlassian.net/browse/PYPOST-1206 |
| ATTACH-2 | [PYPOST-1207](https://pypost.atlassian.net/browse/PYPOST-1207) | https://pypost.atlassian.net/browse/PYPOST-1207 |
| ATTACH-3 | [PYPOST-1208](https://pypost.atlassian.net/browse/PYPOST-1208) | https://pypost.atlassian.net/browse/PYPOST-1208 |

#### ATTACH-1 — [PYPOST-1206](https://pypost.atlassian.net/browse/PYPOST-1206) Document attach path, trust boundary, and lifecycle

- **Preferred SP / estimated SP:** 2 / 2
- **Depends on:** —
- **Acceptance:**
  - Dev docs describe how operators attach vs spawn-session.
  - Trust relative to product MCP and local-host posture is stated.
  - Lifecycle covers attach success/fail, detach, host exit, sidecar exit.
  - Spawn-session limitation wording is updated.

#### ATTACH-2 — [PYPOST-1207](https://pypost.atlassian.net/browse/PYPOST-1207) Attach agent-UI MCP to already-running desktop PyPost

- **Preferred SP / estimated SP:** 5 / 5
- **Depends on:** ATTACH-1 / PYPOST-1206 (contract may iterate)
- **Acceptance:**
  - Operator/agent can bind agent-UI MCP to a running desktop instance.
  - Existing UI-action catalog drives that live UI.
  - Spawn-session path still works.
  - UI tools remain off product MCP.

#### ATTACH-3 — [PYPOST-1208](https://pypost.atlassian.net/browse/PYPOST-1208) Verify attach path with tests as feasible

- **Preferred SP / estimated SP:** 3 / 3
- **Depends on:** ATTACH-2 / PYPOST-1207
- **Acceptance:**
  - Automated tests prove attach (or the largest feasible subset) under
    project make/test norms.
  - Any non-automatable gap is documented with a manual check.
  - Docs and tests agree.

**Suggested order:** PYPOST-1206 (ATTACH-1) → PYPOST-1207 (ATTACH-2) →
PYPOST-1208 (ATTACH-3) (ATTACH-1 docs may be refined when ATTACH-2 lands).

**Sizing note:** Preferred total 2+5+3 = 10 SP is slightly above the former
8 SP debt estimate to keep each child ≤5 and Top-Down-friendly. Do not merge
ATTACH-2 and ATTACH-3 back into one >5 SP ticket.

**Explicitly not children of PYPOST-991:**

| Ticket | Why excluded |
| --- | --- |
| PYPOST-990 | Streamable HTTP transport for agent-UI MCP (separate debt) |
| PYPOST-992 | Spawn-session `call_tool` integration tests |
| PYPOST-993 | Seed/collection injection for sidecar-owned session |

## Q&A

- Q: Why decompose instead of implementing attach in 1202?
  A: Sprint goal is epic decomposition (PYPOST-1202–1205); implement
  attach via children under 991.
- Q: Why three children, not two?
  A: Separates contract/docs, core attach capability, and verification so
  none exceeds 5 SP and each has a clear DoD.
- Q: Does ATTACH-1 block all coding?
  A: Prefer contract first; ATTACH-2 may refine docs — treat ATTACH-1 as a
  soft prerequisite, not a hard code freeze.
- Q: Is IPC / transport chosen here?
  A: **No** — Step 1 forbids architecture; children state outcomes only.
- Q: Must attach replace spawn-session?
  A: **No** — both paths remain; attach is the missing desktop-assist path.
- Q: May UI tools move to product MCP?
  A: **No** — packaging separation from PYPOST-918/952 stays mandatory.
- Q: Are existing children under 991?
  A: PYPOST-1202 (this decompose story) plus implementation children
     PYPOST-1206 / PYPOST-1207 / PYPOST-1208 (ATTACH-1..3).

## References

- [PYPOST-1202](https://pypost.atlassian.net/browse/PYPOST-1202) — this decompose story
- [PYPOST-991](https://pypost.atlassian.net/browse/PYPOST-991) — parent epic
- [PYPOST-952](https://pypost.atlassian.net/browse/PYPOST-952) — shipped stdio agent-UI MCP
- `ai-tasks/PYPOST-952/60-tech-debt.md` — source of attach follow-up
- `doc/dev/agent_ui_actions_mcp.md` — current sidecar docs and attach limitation
- `doc/dev/agent_lifecycle.md` — `AgentAppSession` launch/ready/shutdown
- `doc/dev/mcp_trust_model.md` — inbound product MCP trust posture
- `doc/dev/ui_actions.md` — UI-action packaging contract
