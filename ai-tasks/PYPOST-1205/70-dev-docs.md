# PYPOST-1205: Developer Documentation (Step 8)

DECOMPOSE / planning task — children under
[PYPOST-1188](https://pypost.atlassian.net/browse/PYPOST-1188) already exist.
This step records the `doc/dev` decision for the decompose story only.

## Decision

**Minimal product-doc change only** — ticket pointers, not
repro/diagnosis/fix docs.

| Change | Rationale |
| --- | --- |
| Extend `doc/dev/testing.md` mention of `test_live_collection_tree_missing_option_raises` | Point at ticketed epic/children where the named node is already documented |
| Update `doc/dev/gui_testing.md` Troubleshooting | Same pointer style as PYPOST-1204 segfault row (Qt/uvicorn race / flake surface) |
| Do **not** document parallel flake repro or evidence baseline | Owned by PYPOST-1215 |
| Do **not** document root-cause diagnosis | Owned by PYPOST-1216 |
| Do **not** document stabilize/fix under parallel `make test` | Owned by PYPOST-1217 |
| No new `doc/dev/<feature>.md` | No product feature on PYPOST-1205 |
| No `doc/user/` | Out of scope for this decompose story |

Child browse links:

- REPRO-1 —
  [PYPOST-1215](https://pypost.atlassian.net/browse/PYPOST-1215)
- DIAG-1 —
  [PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216)
- FIX-1 —
  [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217)

## What was updated

In `doc/dev/testing.md`, the existing live `COLLECTION_TREE` negatives
paragraph that names
`test_live_collection_tree_missing_option_raises` now points at epic
PYPOST-1188 and Stories PYPOST-1215 / 1216 / 1217 for parallel-suite
flake work, and states that repro, diagnosis, and fix prose belong to
those children.

In `doc/dev/gui_testing.md` § Troubleshooting, a new row names the same
epic and children for Qt/uvicorn race / flaky
`test_live_collection_tree_missing_option_raises` under parallel
`make test`.

## Skill sections (template mapping)

For this ticket type, the td-70 template (Overview / Architecture / Usage /
Configuration / Troubleshooting) is **satisfied by the existing testing /
GUI testing docs** plus these pointers. Full repro / diagnosis / fix
sections land when REPRO-1 / DIAG-1 / FIX-1 run their own Step 8.

## Completion criteria (this step)

- [x] `doc/dev` touched only as needed (pointers; no child-ticket prose)
- [x] Decision recorded in roadmap Step 8 notes and this artifact
- [ ] Gate: leave Step 8 `[/]` until review / acceptance
