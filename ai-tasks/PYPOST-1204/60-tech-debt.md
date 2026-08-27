# PYPOST-1204: Technical Debt Analysis

DECOMPOSE / planning task — Markdown artifacts and Jira children under
[PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117) only. No product
runtime, tests, or make targets changed on this ticket.

**Verdict:** No blockers for closing PYPOST-1204. Repro, diagnosis, and
mitigation remain on the already-created children
([PYPOST-1212](https://pypost.atlassian.net/browse/PYPOST-1212),
[PYPOST-1213](https://pypost.atlassian.net/browse/PYPOST-1213),
[PYPOST-1214](https://pypost.atlassian.net/browse/PYPOST-1214)).

## Shortcuts Taken

- **Optional Jira “blocks” links omitted** — Architecture allowed optional
  issue links among REPRO-1→DIAG-1→MITIGATE-1 after keys existed. Dependency
  order is recorded in `10-requirements.md` / `20-architecture.md` /
  roadmap; children currently have empty `issuelinks` in Jira.
- **MITIGATE-1 estimation worklog absent** — Create-time Fibonacci estimate
  set SP 5 on [PYPOST-1214](https://pypost.atlassian.net/browse/PYPOST-1214)
  with estimate `tokens_used` 0; estimation worklogs exist on 1212 / 1213
  only. SP field is set; no separate estimation audit trail on 1214.
- **Hard REPRO → DIAG → MITIGATE chain** — No soft-skip of DIAG or MITIGATE
  when earlier children “feel done.” Intentional evidence gate; costs
  serial delivery vs parallelizing mitigation design before diagnosis
  lands.
- **CI ownership folded into MITIGATE-1** — No fourth CI-docs-only child;
  keeps total children ≤3 and total SP near the former 13, at the cost of
  a broader MITIGATE-1 DoD.

## Code Quality Issues

- Stale narrative in `40-code-cleanup.md` / `50-observability.md` still notes
  Steps 5 / 6 as left `[/]` while the roadmap now shows those steps accepted
  (`[x]`). Cosmetic only; does not affect decomposition correctness.
- Child Top-Down cycles own product/docs/tests quality; this ticket has no
  `pypost/` surface to refactor.

## Missing Tests

None for PYPOST-1204 — Step 3 was N/A (no behavioral change); no product or
test files were added.

Timeout-marker / pytest coverage obligations belong to child cycles
(especially PYPOST-1212 / PYPOST-1214), not this decompose story.

**No timeout-marker blockers on this ticket.**

## Performance Concerns

None — no runtime component shipped by PYPOST-1204.

## Follow-up Tasks

### Blockers

None.

### Non-blockers (already ticketed — epic children)

| Item | Class | Jira |
| ---- | ----- | ---- |
| Deterministic repro and evidence baseline (REPRO-1) | Implementation child | [PYPOST-1212](https://pypost.atlassian.net/browse/PYPOST-1212) (SP 3) |
| Root-cause diagnosis lifetime vs QStyle/QPalette (DIAG-1) | Implementation child | [PYPOST-1213](https://pypost.atlassian.net/browse/PYPOST-1213) (SP 5) |
| Safe mitigation and CI ownership docs (MITIGATE-1) | Implementation child | [PYPOST-1214](https://pypost.atlassian.net/browse/PYPOST-1214) (SP 5) |

Suggested order remains 1212 → 1213 → 1214 (hard chain). Epic PYPOST-1117
closes when the **set** of children meets epic acceptance — not when this
decompose story closes.

### Non-blockers (process residual — no new ticket)

| Item | Class | Notes |
| ---- | ----- | ----- |
| Optional Jira blocks links among 1212/1213/1214 | Low / NON-BLOCKER — accept residual | Order is documented in artifacts; add links later only if sprint boards need them |
| MITIGATE-1 estimation worklog absent (`tokens_used` 0) | Low / NON-BLOCKER — accept residual | SP field is set (5); 1212/1213 have estimation worklogs |
| Preferred child total 13 SP matches former debt | Accepted by design | Keeps each child ≤5; do not merge 1213+1214; no fourth CI-only child |

### Explicitly not follow-ups of this decompose (siblings remain outside PYPOST-1117)

| Ticket | Why |
| ---- | --- |
| [PYPOST-1040](https://pypost.atlassian.net/browse/PYPOST-1040) | Distinct SettingsDialog/QWidgetItem GC diagnosis (prior art only) |
| [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115) | Mitigation for that distinct teardown crash (separate epic) |
| [PYPOST-1070](https://pypost.atlassian.net/browse/PYPOST-1070) | Import-order / E402 work that discovered but did not own this crash |
| [PYPOST-1110](https://pypost.atlassian.net/browse/PYPOST-1110) / [PYPOST-1111](https://pypost.atlassian.net/browse/PYPOST-1111) | Pre-existing unrelated suite failures from PYPOST-1070 notes |

## Deviations from Architecture

None material. Children created under PYPOST-1117 with labels
`tech-debt` / `failing-test` / `gui-batch-segfault`, SP ≤5, hard
REPRO→DIAG→MITIGATE chain, and REPRO-1 / DIAG-1 / MITIGATE-1 → key mapping
recorded in requirements, architecture, and roadmap as planned.
