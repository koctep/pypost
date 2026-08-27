# PYPOST-1205: Technical Debt Analysis

DECOMPOSE / planning task — Markdown artifacts and Jira children under
[PYPOST-1188](https://pypost.atlassian.net/browse/PYPOST-1188) only. No product
runtime, tests, or make targets changed on this ticket.

**Verdict:** No blockers for closing PYPOST-1205. Repro, diagnosis, and
stabilization remain on the already-created children
([PYPOST-1215](https://pypost.atlassian.net/browse/PYPOST-1215),
[PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216),
[PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217)).

## Shortcuts Taken

- **Optional Jira “blocks” links omitted** — Architecture allowed optional
  issue links among REPRO-1→DIAG-1→FIX-1 after keys existed. Dependency
  order is recorded in `10-requirements.md` / `20-architecture.md` /
  roadmap; children may have empty `issuelinks` in Jira.
- **Hard REPRO → DIAG → FIX chain** — No soft-skip of DIAG or FIX when
  earlier children “feel done.” Intentional evidence gate; costs serial
  delivery vs parallelizing fix design before diagnosis lands.
- **Diagnosis notes folded into DIAG-1 / FIX-1** — No fourth docs-only
  child; keeps total children ≤3 and total SP near the former 8, at the
  cost of a broader DIAG-1 / FIX-1 DoD.

## Code Quality Issues

- Child Top-Down cycles own product/docs/tests quality; this ticket has no
  `pypost/` surface to refactor.
- No stale post–Step 4 narrative found in requirements / architecture /
  roadmap during Step 5 cleanup.

## Missing Tests

None for PYPOST-1205 — Step 3 was N/A (no behavioral change); no product or
test files were added.

Timeout-marker / pytest coverage obligations belong to child cycles
(especially PYPOST-1215 / PYPOST-1217), not this decompose story.

**No timeout-marker blockers on this ticket.**

## Performance Concerns

None — no runtime component shipped by PYPOST-1205.

## Follow-up Tasks

### Blockers

None.

### Non-blockers (already ticketed — epic children)

| Item | Class | Jira |
| ---- | ----- | ---- |
| Owned parallel flake evidence and baseline (REPRO-1) | Implementation child | [PYPOST-1215](https://pypost.atlassian.net/browse/PYPOST-1215) (SP 2) |
| Root-cause diagnosis race class vs alternatives (DIAG-1) | Implementation child | [PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216) (SP 3) |
| Stabilize named node under parallel `make test` (FIX-1) | Implementation child | [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217) (SP 3) |

Suggested order remains 1215 → 1216 → 1217 (hard chain). Epic PYPOST-1188
closes when the **set** of children meets epic acceptance — not when this
decompose story closes.

**No new unticketed debt requiring Phase D create** — follow-ups are
already PYPOST-1215 / 1216 / 1217.

### Non-blockers (process residual — no new ticket)

| Item | Class | Notes |
| ---- | ----- | ----- |
| Optional Jira blocks links among 1215/1216/1217 | Low / NON-BLOCKER — accept residual | Order is documented in artifacts; add links later only if sprint boards need them |
| Preferred child total 8 SP matches former debt | Accepted by design | Keeps each child ≤5; do not merge 1216+1217; no fourth docs-only child |

### Explicitly not follow-ups of this decompose (siblings remain outside PYPOST-1188)

| Ticket | Why |
| ---- | --- |
| [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117) | Large-batch `apply_theme` segfault (related surface; separate epic) |
| [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115) / [PYPOST-1040](https://pypost.atlassian.net/browse/PYPOST-1040) | SettingsDialog/QWidgetItem GC teardown (distinct site/trigger) |
| [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167) | Discovery context only; MCP headers work unrelated |
| MCP-TM follow-ups (e.g. PYPOST-1169 / 1170) | Not this flake |

## Deviations from Architecture

None material. Children created under PYPOST-1188 with labels
`tech-debt` / `failing-test` / `qt-uvicorn-race`, SP ≤5, hard
REPRO→DIAG→FIX chain, and REPRO-1 / DIAG-1 / FIX-1 → key mapping
recorded in requirements, architecture, and roadmap as planned.
