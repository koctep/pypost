# PYPOST-1205: Decompose epic — Stabilize test_live_collection_tree_missing_option_raises

## Goals

Epic [PYPOST-1188](https://pypost.atlassian.net/browse/PYPOST-1188)
(former Debt from [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167)
`60-tech-debt.md` item 6) asks maintainers to **stabilize** the flaky
node
`tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises`
under parallel `make test`. The epic was promoted from Debt because its
estimate (8 SP) exceeded the SP>6 threshold; story points were cleared
on the epic. This story
([PYPOST-1205](https://pypost.atlassian.net/browse/PYPOST-1205)) exists
so the epic can be split into **implementable child issues** (each ≤5 SP
preferred), each sized for a full Top-Down cycle (Steps 1–8).

**Business goal:** Planners and implementers get clear, separately
deliverable slices that together satisfy PYPOST-1188 acceptance
(reliable green under parallel `make test` for this node; intended
negative `ui_select` assertion preserved), without one oversized ticket
blocking sprint flow.

**Why stabilization matters (parent epic):** The live
`COLLECTION_TREE` missing-option negative path is a regression lock for
agent UI-select error behavior (PYPOST-975). Under parallel
`make test` it flakes; the same file in isolation passes. Unrelated to
MCP Client headers (PYPOST-1167). Leaving it unstable weakens trust in
green CI for agent e2e UI-actions coverage and forces ad-hoc
re-runs/tribal knowledge of “run that file alone.”

## Programming Language

- **This task (PYPOST-1205):** English Markdown planning artifacts and
  Jira issue creation (no product code change required for
  decomposition itself).
- **Child stories under PYPOST-1188:** Python (PyPost desktop/agent e2e,
  Qt/PySide tests, pytest suite), with English Markdown for developer
  docs.

## User Stories

- As a **sprint planner**, I want PYPOST-1188 broken into ≤5 SP children
  with clear acceptance criteria, so each can enter Top-Down without
  re-estimating an 8 SP blob.
- As an **implementer**, I want each child scoped to one primary outcome
  (repro baseline, root-cause diagnosis, or stabilize/fix), so
  Steps 1–8 stay coherent.
- As a **CI owner**, I want future work to leave this node trustworthy
  under the default parallel `make test` path, so green CI does not
  depend on isolating `tests/test_ui_actions.py`.
- As a **maintainer**, I want PYPOST-1117 (large-batch `apply_theme`
  segfault) and PYPOST-1115 (QWidgetItem GC teardown) left as related
  prior art until shared root cause is proven, so this flake epic stays
  focused on the named node id.

## Definition of Done

PYPOST-1205 is done when:

1. Epic PYPOST-1188 scope is inventoried against the PYPOST-1167 finding,
   known parallel-vs-isolated behavior, suspected race class, and related
   GUI/batch epics (explicitly distinguished).
2. Natural work slices are identified and recorded as proposed children
   (provisional IDs REPRO-1, DIAG-1, FIX-1) with summaries, preferred
   SP ≤5, dependencies, and acceptance criteria.
3. Out-of-epic siblings and explicit non-goals are listed.
4. Child Jira issues are created under PYPOST-1188 with clear acceptance
   criteria — done in Step 4:
   [PYPOST-1215](https://pypost.atlassian.net/browse/PYPOST-1215),
   [PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216),
   [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217).
5. Each child is suitable for its own Top-Down Steps 1–8 (single primary
   outcome; testable or docs-verifiable acceptance).
6. `ai-tasks/PYPOST-1205/10-requirements.md` and `00-roadmap.md` exist
   and Step 1 has passed its acceptance gate.

## Task Description

### Problem

PYPOST-1188 is an oversized epic: stabilize flaky
`tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises`
(suspected Qt `apply_theme` vs uvicorn import race under parallel
`make test`). As a single ticket it exceeds the preferred ≤5 SP top-down
unit. At Step 1 inventory time only PYPOST-1205 sat under the epic;
implementation children PYPOST-1215 / PYPOST-1216 / PYPOST-1217 were
created in Step 4.

### Current state (inventory)

- **Flaky node** —
  `tests/test_ui_actions.py::test_live_collection_tree_missing_option_raises`
  (live `COLLECTION_TREE` missing label → `UiTargetNotInteractableError`
  with `"option not found"`; PYPOST-975). Gap: unstable under parallel
  suite load.
- **Repro contrast** — Fails intermittently under parallel `make test`;
  isolated file (or node) run passes. Gap: no owned, repeatable
  evidence baseline for the flake yet.
- **Suspected class** — Qt `apply_theme` vs uvicorn import race
  (recorded in PYPOST-1167 tech-debt item 6 / epic description). Gap:
  suspicion only; not confirmed or refuted with evidence.
- **Base commit** — `353370cdbd19c7a3338e2ed05c292b0a404d7b90` (HEAD
  before PYPOST-1167 edits). Gap: children should be able to bisect /
  contrast against this baseline without re-deriving from chat.
- **Independence from MCP headers** — Observed during PYPOST-1167 Step 4;
  unrelated to headers-table assertions. Gap: keep MCP Client work out
  of this epic’s children.
- **Related prior art** — PYPOST-1117 large-batch `apply_theme`
  segfault; PYPOST-1115 / PYPOST-1040 SettingsDialog/QWidgetItem GC
  teardown. Gap: related Qt/theme/lifetime class possible, but different
  symptom (assertion flake on one live UI-actions node vs native death /
  GC teardown); do not merge scopes until diagnosis proves otherwise.
- **Sibling live negative** —
  `test_live_collection_tree_index_out_of_range_raises` shares the live
  `COLLECTION_TREE` fixture path. Gap: not named by the epic; include
  only if diagnosis shows the same race, else leave out.
- **Source** — `ai-tasks/PYPOST-1167/60-tech-debt.md` item 6; former
  ~8 SP Debt promoted to Epic; labels `failing-test`, `tech-debt`;
  unlinked from former parent epic PYPOST-1155. Gap: closed in Step 4 —
  children PYPOST-1215 / PYPOST-1216 / PYPOST-1217 created under the
  epic.

Epic acceptance (must be covered by the **set** of children, not each
child):

- Owned repro/evidence that the parallel flake is (or is not)
  reproducible on the named node
- Root-cause determination for the flake class (confirm/refute
  `apply_theme` vs uvicorn race, or justified alternative)
- Stabilization so the node is reliable under parallel `make test`
  without losing the intended negative assertion

### Scope (this task)

- Inventory epic vs PYPOST-1167 finding, parallel-vs-isolated facts, and
  related prior art.
- Propose ≤5 SP child slices with acceptance criteria and preferred SP.
- Record decisions and create Jira children under PYPOST-1188 (Step 4:
  PYPOST-1215 / PYPOST-1216 / PYPOST-1217).
- Keep wording at business/product level (no harness or fix design here).

### Out of scope (this task)

- Implementing repro harness, diagnosis instrumentation, or
  stabilization in product or test code.
- Creating Jira children in Step 1 (deferred to Step 4; done).
- Merging this work into PYPOST-1117 or PYPOST-1115 (related class, not
  confirmed same root cause).
- Changing MCP Client headers / PYPOST-1167 product behavior.
- Expanding scope to all `test_ui_actions.py` flakiness unless a child
  proves the same root cause.
- User-facing `doc/user/` docs unless a child explicitly requires them.
- Red automated tests on PYPOST-1205 itself — Step 3 is N/A for this
  decompose ticket; failing repros belong to child Top-Down cycles
  (especially REPRO-1).

### Functional Requirements (decomposition)

- FR1: Requirements name every proposed child with summary, preferred
  SP (Fibonacci ≤5), dependencies, and acceptance criteria.
- FR2: Together, children cover deterministic/owned flake evidence,
  root-cause diagnosis vs related GUI epics, and stabilization of the
  named node under parallel `make test`.
- FR3: Children exclude PYPOST-1117 / PYPOST-1115 implementation scope
  and unrelated MCP-TM follow-ups unless diagnosis proves a shared
  root cause (then cross-link, do not silently fold).
- FR4: Each child is independently runnable through Top-Down Steps 1–8.
- FR5: Step 4 created Story issues under parent PYPOST-1188 with labels
  consistent with the epic (`tech-debt`, `failing-test`,
  `qt-uvicorn-race` per architecture).

### Non-Functional Requirements

- **NFR-1 Clarity:** Child summaries and AC are unambiguous for
  estimation and review without re-reading the full PYPOST-1167
  tech-debt write-up.
- **NFR-2 Size:** Preferred story points ≤5; avoid recreating an 8 SP
  child.
- **NFR-3 Traceability:** Provisional IDs map to Jira keys (recorded in
  roadmap and this file after Step 4 create).
- **NFR-4 Distinction:** Children must treat PYPOST-1117 / PYPOST-1115
  as related prior art until diagnosis proves otherwise — do not
  silently fold scopes.
- **NFR-5 Evidence:** Flake and pass/fail claims in child work must cite
  reproducible commands/results (parallel vs isolated), not anecdote
  alone.

### Constraints and Assumptions

- Original epic estimate was 8 SP; three children totaling about that
  effort is preferred over many micro-slices.
- Isolated-file pass vs parallel flake remains the known contrast until
  a child updates that evidence.
- Stabilization may be test-isolation, ordering, import/lifecycle, or
  product-side — decided by children after diagnosis, not here.
- The intended assertion (missing option → `"option not found"`) must
  remain; “stabilize” does not mean delete or weaken the lock without
  an explicit child AC saying so.
- Autonomous decisions below stand unless review rejects them.

### Main Entities (business)

| Entity | Role |
| --- | --- |
| Named flake node | `test_live_collection_tree_missing_option_raises` under parallel load |
| Parallel `make test` | Default suite run that surfaces the intermittent failure |
| Isolated file run | Contrast that currently passes for the same node |
| Live COLLECTION_TREE negative | Intended UI-select error lock (`option not found`) |
| Suspected race class | Qt `apply_theme` vs uvicorn import interaction (unconfirmed) |
| Related GUI epics | PYPOST-1117 / PYPOST-1115 prior art (distinct unless proven same) |
| Stabilization outcome | Reliable green under parallel `make test` for the named node |

### Proposed Child Story Breakdown (under PYPOST-1188)

Provisional IDs **REPRO-1**, **DIAG-1**, **FIX-1** mapped to Jira
Stories created under PYPOST-1188 in Step 4 of PYPOST-1205.

| Provisional ID | Jira key | Browse |
| --- | --- | --- |
| REPRO-1 | [PYPOST-1215](https://pypost.atlassian.net/browse/PYPOST-1215) | https://pypost.atlassian.net/browse/PYPOST-1215 |
| DIAG-1 | [PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216) | https://pypost.atlassian.net/browse/PYPOST-1216 |
| FIX-1 | [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217) | https://pypost.atlassian.net/browse/PYPOST-1217 |

#### REPRO-1 — [PYPOST-1215](https://pypost.atlassian.net/browse/PYPOST-1215) Owned parallel flake evidence and baseline

- **Preferred SP / estimated SP:** 2 / 2
- **Depends on:** —
- **Acceptance:**
  - A documented, repeatable procedure reproduces the intermittent
    failure of the named node under parallel `make test` load (or a
    justified equivalent that matches the epic’s failure class), and
    contrasts with isolated-file (or isolated-node) pass.
  - Baseline evidence records environment, command shape, base commit
    reference (`353370cd…`), and observed failure mode.
  - Later children can cite this baseline without re-deriving from
    PYPOST-1167 notes alone.

#### DIAG-1 — [PYPOST-1216](https://pypost.atlassian.net/browse/PYPOST-1216) Root-cause diagnosis (race class vs alternatives)

- **Preferred SP / estimated SP:** 3 / 3
- **Depends on:** REPRO-1 / PYPOST-1215 (stable evidence/baseline)
- **Acceptance:**
  - A written diagnosis confirms, refutes, or replaces the suspected
    Qt `apply_theme` vs uvicorn import race with an evidence-backed
    class.
  - Distinction from PYPOST-1117 (large-batch `apply_theme` segfault)
    and PYPOST-1115/1040 (QWidgetItem GC teardown) is explicit
    (same class vs different class; symptom/trigger comparison).
  - Evidence is sufficient for FIX-1 to choose a stabilization approach
    without re-opening the class question.
  - Dev-facing notes record the conclusion for future maintainers.

#### FIX-1 — [PYPOST-1217](https://pypost.atlassian.net/browse/PYPOST-1217) Stabilize named node under parallel `make test`

- **Preferred SP / estimated SP:** 3 / 3
- **Depends on:** REPRO-1 / PYPOST-1215; DIAG-1 / PYPOST-1216 (diagnosis
  informs what “safe stabilize” means)
- **Acceptance:**
  - The named node is reliable under parallel `make test` (flake
    eliminated or residual risk documented with owner and follow-up).
  - Intended negative assertion remains
    (`UiTargetNotInteractableError` / `"option not found"`) unless an
    explicit, reviewed AC change documents otherwise.
  - Outcome is proven against the REPRO-1 procedure (or an updated
    equivalent recorded with the fix).
  - No silent merge into PYPOST-1117 / PYPOST-1115 scope; cross-links
    stay explicit if shared cause is found.

**Suggested order:** REPRO-1 → DIAG-1 → FIX-1.

**Sizing note:** Preferred total 2+3+3 = 8 SP matches the former debt
estimate while keeping each child ≤5 and Top-Down-friendly. Do not merge
DIAG-1 and FIX-1 back into one >5 SP ticket. Do not add a fourth
docs-only child unless review requires it — diagnosis notes fold into
DIAG-1 / FIX-1.

**Explicitly not children of PYPOST-1188:**

| Ticket / topic | Why excluded |
| --- | --- |
| PYPOST-1117 | Large-batch `apply_theme` segfault (related surface; separate epic) |
| PYPOST-1115 / PYPOST-1040 | SettingsDialog/QWidgetItem GC teardown (distinct site/trigger) |
| PYPOST-1167 MCP headers | Discovery context only; headers work is unrelated |
| PYPOST-1169 / PYPOST-1170 / … | MCP-TM follow-ups; not this flake |
| `test_live_collection_tree_index_out_of_range_raises` | Sibling live negative; include only if same root cause proven |

## Q&A

- Q: Why decompose instead of stabilizing in 1205?
  A: Sprint goal is epic decomposition (PYPOST-1202–1205); implement
  via children under 1188.
- Q: Why three children (REPRO / DIAG / FIX)?
  A: Mirrors the closest decompose pattern (PYPOST-1204): owned
  evidence, class determination, then stabilize — keeps each ≤5 SP and
  near the former 8 SP total.
- Q: Why not fold this into PYPOST-1117?
  A: Different failure mode (assertion flake on one live UI-actions
  node vs native segfault under ~110-module GUI batch). Treat as prior
  art until DIAG-1 proves otherwise.
- Q: Is the exact repro harness or fix mechanism chosen here?
  A: **No** — Step 1 forbids architecture; children state outcomes only.
- Q: Does PYPOST-1205 itself get a red test in Step 3?
  A: **No** — this ticket is decompose/planning only. Step 3 is N/A;
  red tests belong to child Top-Down cycles (especially REPRO-1).
- Q: Must FIX-1 change production `apply_theme` or uvicorn usage?
  A: **Not required** — test-side isolation/ordering can satisfy the
  epic if diagnosis supports it and the parallel suite stays reliable.
- Q: Are existing implementation children under 1188?
  A: After Step 4: PYPOST-1205 plus implementation children
     PYPOST-1215 / PYPOST-1216 / PYPOST-1217 (REPRO-1 / DIAG-1 /
     FIX-1).

## References

- [PYPOST-1205](https://pypost.atlassian.net/browse/PYPOST-1205) — this
  decompose story
- [PYPOST-1188](https://pypost.atlassian.net/browse/PYPOST-1188) —
  parent epic
- [PYPOST-1167](https://pypost.atlassian.net/browse/PYPOST-1167) —
  discovery source
- [PYPOST-975](https://pypost.atlassian.net/browse/PYPOST-975) —
  original live COLLECTION_TREE negative coverage
- [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117) —
  related prior-art epic (large-batch `apply_theme`; excluded scope)
- [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115) —
  related mitigation epic (excluded sibling scope)
- `ai-tasks/PYPOST-1167/60-tech-debt.md` — former ~8 SP debt source
  (item 6)
- `ai-tasks/PYPOST-1204/10-requirements.md` — closest decompose artifact
  pattern (REPRO / DIAG / stabilize)
- `tests/test_ui_actions.py` — named node and sibling live negatives
- `doc/dev/testing.md` — live COLLECTION_TREE negative documentation
