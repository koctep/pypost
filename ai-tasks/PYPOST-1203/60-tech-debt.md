# PYPOST-1203: Technical Debt Analysis

DECOMPOSE / planning task — Markdown artifacts and Jira children under
[PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115) only. No product
runtime, tests, or make targets changed on this ticket.

**Verdict:** No blockers for closing PYPOST-1203. Mitigation implementation and
verification remain on the already-created children
([PYPOST-1209](https://pypost.atlassian.net/browse/PYPOST-1209),
[PYPOST-1210](https://pypost.atlassian.net/browse/PYPOST-1210),
[PYPOST-1211](https://pypost.atlassian.net/browse/PYPOST-1211)).

## Shortcuts Taken

- **Self-estimation at create** — Step 4 could not nest the preferred
  estimation subagent; children were self-estimated per
  `_shared/story-points.md`. Preferred SP matched (2 / 3 / 5); no separate
  estimation `tokens_used` worklog on the child keys.
- **Optional Jira “blocks” links omitted** — Architecture allowed optional
  issue links among MITIGATE-1→2→3 after keys existed. Dependency order is
  recorded in `10-requirements.md` / `20-architecture.md` / roadmap; children
  currently have empty `issuelinks` in Jira.
- **Soft MITIGATE-3 gate + settlement ownership** — MITIGATE-3 may soft-skip
  when pin already meets epic success **only if** MITIGATE-2 AC owns
  marker/docs settlement for that path. Intentional stop-on-success design;
  settlement is never orphaned, at the cost of dual-path ownership rules
  reviewers must keep straight.

## Code Quality Issues

- Stale narrative in `40-code-cleanup.md` / `50-observability.md` still notes
  Steps 5 / 6 as left `[/]` while the roadmap now shows those steps accepted
  (`[x]`). Cosmetic only; does not affect decomposition correctness.
- Child Top-Down cycles own product/docs/tests quality; this ticket has no
  `pypost/` surface to refactor.

## Missing Tests

None for PYPOST-1203 — Step 3 was N/A (no behavioral change); no product or
test files were added.

Timeout-marker / pytest coverage obligations belong to child cycles
(especially PYPOST-1210 / PYPOST-1211), not this decompose story.

**No timeout-marker blockers on this ticket.**

## Performance Concerns

None — no runtime component shipped by PYPOST-1203.

## Follow-up Tasks

### Blockers

None.

### Non-blockers (already ticketed — epic children)

| Item | Class | Jira |
| ---- | ----- | ---- |
| Document mitigation evaluation contract and baseline (MITIGATE-1) | Implementation child | [PYPOST-1209](https://pypost.atlassian.net/browse/PYPOST-1209) (SP 2) |
| Attempt PySide6/shiboken6 pin mitigation (MITIGATE-2) | Implementation child | [PYPOST-1210](https://pypost.atlassian.net/browse/PYPOST-1210) (SP 3) |
| Attempt application-side mitigations and settle outcome (MITIGATE-3) | Implementation child | [PYPOST-1211](https://pypost.atlassian.net/browse/PYPOST-1211) (SP 5) |

Suggested order remains 1209 → 1210 → 1211 (1211 only when pin work does not
already satisfy the epic; settlement always has an owner — 1210 on
pin-success skip, otherwise 1211). Epic PYPOST-1115 closes when the **set**
of children meets epic acceptance — not when this decompose story closes.

### Non-blockers (process residual — no new ticket)

| Item | Class | Notes |
| ---- | ----- | ----- |
| Optional Jira blocks links among 1209/1210/1211 | Low / NON-BLOCKER — accept residual | Order is documented in artifacts; add links later only if sprint boards need them |
| Estimation worklogs absent on child keys | Low / NON-BLOCKER — accept residual | Create-time self-estimate; SP field is set (2/3/5) |
| Preferred child total 10 SP vs former 8 SP debt | Accepted by design | Keeps each child ≤5; do not merge 1210+1211 |

### Explicitly not follow-ups of this decompose (siblings remain outside PYPOST-1115)

| Ticket | Why |
| ---- | --- |
| [PYPOST-1040](https://pypost.atlassian.net/browse/PYPOST-1040) | Diagnosis complete; this epic is mitigation only |
| [PYPOST-1116](https://pypost.atlassian.net/browse/PYPOST-1116) | Duration-report xfail/XPASS labeling (separate debt) |
| [PYPOST-1070](https://pypost.atlassian.net/browse/PYPOST-1070) | Batch GUI notes — related class, not same confirmed root cause |

## Deviations from Architecture

None material. Children created under PYPOST-1115 with labels
`tech-debt` / `qwitem-gc-mitigate`, SP ≤5, settlement-ownership AC on
MITIGATE-2 for pin-success soft-skip, and MITIGATE-N → key mapping recorded
in requirements, architecture, and roadmap as planned.
