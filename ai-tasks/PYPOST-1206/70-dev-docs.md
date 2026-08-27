# PYPOST-1206: Developer Documentation (Step 8)

ATTACH-1 under epic
[PYPOST-991](https://pypost.atlassian.net/browse/PYPOST-991). Step 4 already
landed the primary attach contract in `doc/dev`. This step **verified**
FR1–FR12 and the architecture surface plan, applied Troubleshooting polish
on the primary page, and recorded the gate artifact.

## Decision

**Confirm + polish existing ATTACH-1 `doc/dev` surfaces** — no new feature
page; no attach capability invented.

| Surface | Step 8 action |
| --- | --- |
| `doc/dev/agent_ui_actions_mcp.md` | Confirmed primary contract; polished Troubleshooting for spawn vs attach / soft contract |
| `doc/dev/mcp_trust_model.md` | Confirmed satellite trust (no further edit) |
| `doc/dev/agent_lifecycle.md` | Confirmed attach bind/unbind outcomes (no further edit) |
| `doc/dev/ui_actions.md` | Confirmed packaging pointer (no further edit) |
| New `doc/dev/<feature>.md` | **Not created** — primary page already owns the narrative |
| `doc/user/` | Out of scope |

Sibling ownership unchanged: capability
[PYPOST-1207](https://pypost.atlassian.net/browse/PYPOST-1207); tests
[PYPOST-1208](https://pypost.atlassian.net/browse/PYPOST-1208).

## FR1–FR12 checklist (verified)

| FR | Coverage in `doc/dev` | Status |
| --- | --- | --- |
| FR1 Spawn-session | Overview table + Spawn-session path | Met |
| FR2 Attach + when to choose | Attach path | Met |
| FR3 Both paths valid | Overview + Attach path | Met |
| FR4 Separate trust surface | Trust boundary + `mcp_trust_model.md` | Met |
| FR5 Local-host posture | Trust boundary + `mcp_trust_model.md` | Met |
| FR6 Attach success | Attach lifecycle table (+ `agent_lifecycle.md`) | Met |
| FR7 Attach fail | Same | Met |
| FR8 Detach | Same | Met |
| FR9 Host exit | Same | Met |
| FR10 Sidecar exit | Same | Met |
| FR11 Limitation wording | Limitations (contract + sibling pointers) | Met |
| FR12 Capability note | Attach path FR12 note + Limitations | Met |

Acceptance mapping (requirements DoD): attach vs spawn FR1–FR3/FR12; trust
FR4–FR5; lifecycle FR6–FR10; limitation wording FR11 — all reflected.

## Architecture surface plan (verified)

Matches `20-architecture.md`: primary
`agent_ui_actions_mcp.md`; satellites `mcp_trust_model.md`,
`agent_lifecycle.md`, `ui_actions.md`. Soft-contract outcome vocabulary
preserved; packaging separation preserved; no IPC/mechanism dump.

## Skill sections (template mapping)

| td-70 section | Where on primary page |
| --- | --- |
| Overview | Overview (two valid paths) |
| Architecture | Architecture + mermaid |
| Usage | Spawn-session path; Attach path (procedure + FR12) |
| Configuration | Configuration (spawn flags; attach bind deferred) |
| Troubleshooting | Troubleshooting (spawn ops + attach soft-contract clarity) |

## What Step 8 changed

In `doc/dev/agent_ui_actions_mcp.md` § Troubleshooting:

- Clarified hang-at-start applies to **spawn-session** ready wait.
- Added bullets for: expected live desktop but got spawn-session; attach
  does not replace spawn-session; attach is not on product MCP.

No product code, no attach capability, no sprint registry / `AGENTS.md` /
gurushots edits.

## Completion criteria (this step)

- [x] `doc/dev` reflects FR1–FR12 and architecture surface plan
- [x] Overview / Usage / Troubleshooting clarity polished on attach contract
- [x] Decision and verification recorded in this artifact + roadmap Step 8
- [ ] Gate: leave Step 8 `[/]` until review / acceptance
