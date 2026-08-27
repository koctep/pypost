# PYPOST-1204: Developer Documentation (Step 8)

DECOMPOSE / planning task — children under
[PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117) already exist.
This step records the `doc/dev` decision for the decompose story only.

## Decision

**Minimal product-doc change only** — a ticket pointer, not
diagnosis/mitigation docs.

| Change | Rationale |
| --- | --- |
| Update `doc/dev/gui_testing.md` Troubleshooting | Point at ticketed children (native crash / segfault surface) |
| Do **not** document repro or evidence baseline | Owned by PYPOST-1212 |
| Do **not** document root-cause diagnosis | Owned by PYPOST-1213 |
| Do **not** document mitigation or CI ownership | Owned by PYPOST-1214 |
| No new `doc/dev/<feature>.md` | No product feature on PYPOST-1204 |
| No `doc/user/` | Out of scope for this decompose story |

Child browse links:

- REPRO-1 —
  [PYPOST-1212](https://pypost.atlassian.net/browse/PYPOST-1212)
- DIAG-1 —
  [PYPOST-1213](https://pypost.atlassian.net/browse/PYPOST-1213)
- MITIGATE-1 —
  [PYPOST-1214](https://pypost.atlassian.net/browse/PYPOST-1214)

## What was updated

In `doc/dev/gui_testing.md` § Troubleshooting, a new row names epic
PYPOST-1117 and Stories PYPOST-1212 / 1213 / 1214 for large-batch
`apply_theme` segfaults, and states that repro, diagnosis, and
mitigation/CI ownership prose belong to those children. `doc/dev/testing.md`
already defers ELF/native-crash troubleshooting to `gui_testing.md`, so no
second pointer was added there.

## Skill sections (template mapping)

For this ticket type, the td-70 template (Overview / Architecture / Usage /
Configuration / Troubleshooting) is **satisfied by the existing GUI testing
doc** plus the segfault pointer. Full repro / diagnosis / mitigation
sections land when REPRO-1 / DIAG-1 / MITIGATE-1 run their own Step 8.

## Completion criteria (this step)

- [x] `doc/dev` touched only as needed (pointer; no child-ticket prose)
- [x] Decision recorded in roadmap Step 8 notes and this artifact
- [ ] Gate: leave Step 8 `[/]` until review / acceptance
