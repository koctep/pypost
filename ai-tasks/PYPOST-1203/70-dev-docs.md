# PYPOST-1203: Developer Documentation (Step 8)

DECOMPOSE / planning task — children under
[PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115) already exist.
This step records the `doc/dev` decision for the decompose story only.

## Decision

**Minimal product-doc change only** — a ticket pointer, not mitigation
docs.

| Change | Rationale |
| --- | --- |
| Update `doc/dev/agent_dialog_settle.md` | Point at ticketed children |
| Do **not** document evaluation contract | Owned by PYPOST-1209 |
| Do **not** document pin outcome / settlement | Owned by PYPOST-1210 |
| Do **not** document app-side / default settle | Owned by PYPOST-1211 |
| No new `doc/dev/<feature>.md` | No product feature on PYPOST-1203 |
| No `doc/user/` | Out of scope for this decompose story |

Child browse links:

- MITIGATE-1 —
  [PYPOST-1209](https://pypost.atlassian.net/browse/PYPOST-1209)
- MITIGATE-2 —
  [PYPOST-1210](https://pypost.atlassian.net/browse/PYPOST-1210)
- MITIGATE-3 —
  [PYPOST-1211](https://pypost.atlassian.net/browse/PYPOST-1211)

## What was updated

In `doc/dev/agent_dialog_settle.md` § Teardown stress detector
(PYPOST-1040), a short pointer names epic PYPOST-1115 and Stories
PYPOST-1209 / 1210 / 1211, and states that evaluation contract, pin
outcome, and marker/docs settlement belong to those children. The Related
entry for `ai-tasks/PYPOST-1040/60-tech-debt.md` now lists the same child
keys.

## Skill sections (template mapping)

For this ticket type, the td-70 template (Overview / Architecture / Usage /
Configuration / Troubleshooting) is **satisfied by the existing settle
sidecar doc** plus the mitigation pointer. Full mitigation sections land
when MITIGATE-1..3 run their own Step 8.

## Completion criteria (this step)

- [x] `doc/dev` touched only as needed (pointer; no mitigation prose)
- [x] Decision recorded in roadmap Step 8 notes and this artifact
- [ ] Gate: leave Step 8 `[/]` until review / acceptance
