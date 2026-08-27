# PYPOST-1206: Technical Debt Analysis

Docs-only ATTACH-1 — Soft-contract edits in `doc/dev/*` plus
`ai-tasks/PYPOST-1206/` Top-Down artifacts. No product runtime, tests, or
make-target behavior changed on this ticket.

**Verdict:** No blockers for closing PYPOST-1206 ATTACH-1 docs. Attach
capability and verification remain on the already-created siblings
([PYPOST-1207](https://pypost.atlassian.net/browse/PYPOST-1207),
[PYPOST-1208](https://pypost.atlassian.net/browse/PYPOST-1208)). **No new
unticketed debt** from this cycle; Phase D has nothing to open for ATTACH-2/3
scope.

## Shortcuts Taken

- **Soft contract before capability** — FR12 / NFR-4: publish attach path,
  trust, and lifecycle outcomes while runtime attach is still owned by
  ATTACH-2. Intentional epic ordering; expect wording refinement when
  [PYPOST-1207](https://pypost.atlassian.net/browse/PYPOST-1207) lands.
- **Outcome language only** — No IPC, discovery, CLI flags, or wire formats
  in docs (architecture non-goals). Mechanism detail deferred to ATTACH-2.
- **Satellite cross-links, not full duplicates** — Primary narrative in
  `agent_ui_actions_mcp.md`; short tables/pointers in
  `mcp_trust_model.md`, `agent_lifecycle.md`, `ui_actions.md`.

## Code Quality Issues

- Stale narrative in `40-code-cleanup.md` / `50-observability.md` still notes
  their steps as left `[/]` for the gate; the roadmap now shows Steps 5–6
  accepted (`[x]`). Cosmetic only; does not affect ATTACH-1 correctness.
- Pre-existing `>100` char table rows outside Step 4 ATTACH-1 edits (older
  Operator guidance / Actions rows) were left unchanged — out of ticket
  scope; Step 4 attach tables were normalized in Step 5.
- This ticket has no `pypost/` surface to refactor.

## Missing Tests

None for PYPOST-1206 — Step 3 was N/A (no behavioral change); no product or
test files were added.

Timeout-marker / pytest attach coverage obligations belong to
[PYPOST-1208](https://pypost.atlassian.net/browse/PYPOST-1208) (ATTACH-3),
not this docs story.

**No timeout-marker blockers on this ticket.**

## Performance Concerns

None — no runtime component shipped by PYPOST-1206.

## Follow-up Tasks

### Blockers

None.

### Non-blockers (already ticketed — do not duplicate)

| Item | Class | Jira |
| ---- | ----- | ---- |
| Soft-contract → runtime attach (bind/unbind, mechanism, any attach bind options) | ATTACH-2 capability | [PYPOST-1207](https://pypost.atlassian.net/browse/PYPOST-1207) |
| Attach-path verification tests as feasible | ATTACH-3 tests | [PYPOST-1208](https://pypost.atlassian.net/browse/PYPOST-1208) |
| Doc wording may iterate when capability ships (NFR-4) | Owned by ATTACH-2 cycle | [PYPOST-1207](https://pypost.atlassian.net/browse/PYPOST-1207) — refine ATTACH-1 prose there; do not open a second docs debt ticket |

Suggested sibling order remains 1206 (this) → 1207 → 1208. Epic
[PYPOST-991](https://pypost.atlassian.net/browse/PYPOST-991) closes when the
**set** of children meets epic acceptance.

### Non-blockers (process residual — no new ticket)

| Item | Class | Notes |
| ---- | ----- | ----- |
| Soft-contract vs shipped-path gap until ATTACH-2 | Accepted by design | Documented FR12; operators still use spawn-session today |
| Stale `[/]` notes in Step 5/6 artifacts | Low / NON-BLOCKER — accept residual | Roadmap is source of truth |
| Pre-existing long GFM rows outside ATTACH-1 edits | Low / NON-BLOCKER — accept residual | Not introduced by this story |

### Unticketed new debt

None. No `Jira: unset` items — nothing for Phase D to create from this
analysis.

### Explicitly not follow-ups of this ATTACH-1 docs story

| Ticket | Why |
| ---- | --- |
| [PYPOST-990](https://pypost.atlassian.net/browse/PYPOST-990) | HTTP transport for agent-UI MCP (stdio-only limitation remains) |
| [PYPOST-992](https://pypost.atlassian.net/browse/PYPOST-992) | Spawn-session `call_tool` tests |
| [PYPOST-993](https://pypost.atlassian.net/browse/PYPOST-993) | Seed/collection injection for owned session |

## Deviations from Architecture

None material. Doc-surface plan from `20-architecture.md` executed:
primary `agent_ui_actions_mcp.md` plus satellites; soft-contract outcome
vocabulary; packaging separation preserved; Step 3 N/A honored.
