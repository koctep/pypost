# PYPOST-1202: Technical Debt Analysis

DECOMPOSE / planning task — Markdown artifacts and Jira children under
[PYPOST-991](https://pypost.atlassian.net/browse/PYPOST-991) only. No product
runtime, tests, or make targets changed on this ticket.

**Verdict:** No blockers for closing PYPOST-1202. Attach implementation and
verification remain on the already-created children
([PYPOST-1206](https://pypost.atlassian.net/browse/PYPOST-1206),
[PYPOST-1207](https://pypost.atlassian.net/browse/PYPOST-1207),
[PYPOST-1208](https://pypost.atlassian.net/browse/PYPOST-1208)).

## Shortcuts Taken

- **Self-estimation at create** — Step 4 could not nest the preferred
  estimation subagent; children were self-estimated per
  `_shared/story-points.md`. Preferred SP matched (2 / 5 / 3); no separate
  estimation `tokens_used` worklog on the child keys.
- **Optional Jira “blocks” links omitted** — Architecture allowed optional
  issue links among ATTACH-1→2→3 after keys existed. Dependency order is
  recorded in `10-requirements.md` / `20-architecture.md` / roadmap; children
  currently have empty `issuelinks` in Jira.
- **Soft ATTACH-1 prerequisite** — Docs/contract may iterate when ATTACH-2
  lands; intentional to avoid a hard code freeze, at the cost of possible
  doc churn on PYPOST-1206 after PYPOST-1207.

## Code Quality Issues

- Stale narrative in `40-code-cleanup.md` still notes Step 4 as `[/]` while
  the roadmap now shows Step 4 accepted (`[x]`). Cosmetic only; does not
  affect decomposition correctness.
- Child Top-Down cycles own product/docs/tests quality; this ticket has no
  `pypost/` surface to refactor.

## Missing Tests

None for PYPOST-1202 — Step 3 was N/A (no behavioral change); no product or
test files were added.

Timeout-marker / pytest coverage obligations belong to child cycles
(especially PYPOST-1207 / PYPOST-1208), not this decompose story.

**No timeout-marker blockers on this ticket.**

## Performance Concerns

None — no runtime component shipped by PYPOST-1202.

## Follow-up Tasks

### Blockers

None.

### Non-blockers (already ticketed — epic children)

| Item | Class | Jira |
| ---- | ----- | ---- |
| Document attach path, trust boundary, and lifecycle (ATTACH-1) | Implementation child | [PYPOST-1206](https://pypost.atlassian.net/browse/PYPOST-1206) (SP 2) |
| Attach agent-UI MCP to already-running desktop PyPost (ATTACH-2) | Implementation child | [PYPOST-1207](https://pypost.atlassian.net/browse/PYPOST-1207) (SP 5) |
| Verify attach path with tests as feasible (ATTACH-3) | Implementation child | [PYPOST-1208](https://pypost.atlassian.net/browse/PYPOST-1208) (SP 3) |

Suggested order remains 1206 → 1207 → 1208. Epic PYPOST-991 closes when the
**set** of children meets epic acceptance — not when this decompose story
closes.

### Non-blockers (process residual — no new ticket)

| Item | Class | Notes |
| ---- | ----- | ----- |
| Optional Jira blocks links among 1206/1207/1208 | Low / NON-BLOCKER — accept residual | Order is documented in artifacts; add links later only if sprint boards need them |
| Estimation worklogs absent on child keys | Low / NON-BLOCKER — accept residual | Create-time self-estimate; SP field is set (2/5/3) |
| Preferred child total 10 SP vs former 8 SP debt | Accepted by design | Keeps each child ≤5; do not merge 1207+1208 |

### Explicitly not follow-ups of this decompose (siblings remain outside PYPOST-991)

| Ticket | Why |
| ---- | --- |
| [PYPOST-990](https://pypost.atlassian.net/browse/PYPOST-990) | HTTP transport for agent-UI MCP |
| [PYPOST-992](https://pypost.atlassian.net/browse/PYPOST-992) | Spawn-session `call_tool` tests |
| [PYPOST-993](https://pypost.atlassian.net/browse/PYPOST-993) | Seed/collection injection for owned session |

## Deviations from Architecture

None material. Children created under PYPOST-991 with labels
`agent` / `mcp` / `attach-sidecar`, SP ≤5, and ATTACH-N → key mapping recorded
in requirements, architecture, and roadmap as planned.
