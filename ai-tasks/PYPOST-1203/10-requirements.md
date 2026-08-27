# PYPOST-1203: Decompose epic — mitigate QWidgetItem GC-teardown crash

## Goals

Epic [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115)
(follow-up to [PYPOST-1040](https://pypost.atlassian.net/browse/PYPOST-1040))
asks maintainers to **attempt mitigation** of an intermittent native
SIGSEGV/SIGBUS during Qt/PySide widget teardown. PYPOST-1040 diagnosed the
crash (upstream PySide6/shiboken6 `QWidgetItem` lifecycle defect triggered by
pytest's forced cyclic GC on `SettingsDialog`'s nested-layout subtree) but
did not fix it. The epic was promoted from Debt because its estimate (8 SP)
exceeded the SP>6 threshold; story points were cleared on the epic. This
story ([PYPOST-1203](https://pypost.atlassian.net/browse/PYPOST-1203))
exists so the epic can be split into **implementable child issues** (each
≤5 SP preferred), each sized for a full Top-Down cycle (Steps 1–8).

**Business goal:** Planners and implementers get clear, separately deliverable
slices that together satisfy PYPOST-1115 acceptance (materially lower crash
rate on the stress detector; no e2e assertion regression), without one
oversized ticket blocking sprint flow.

**Why mitigation matters (parent epic):** The crash reproduces on the
supported CI combination (Linux / Python 3.13 / PySide6-shiboken6 6.11.1) at
~32.5% per e2e run. The exercised path mirrors real Settings-dialog and
session-shutdown behavior. Leaving it unmitigated keeps flaky native
process death in agent dialog settle coverage and weakens trust in green CI
for that path.

## Programming Language

- **This task (PYPOST-1203):** English Markdown planning artifacts and Jira
  issue creation (no product code change required for decomposition itself).
- **Child stories under PYPOST-1115:** Python (PyPost desktop, agent
  lifecycle, dependency pins, pytest stress/e2e), with English Markdown for
  developer docs.

## User Stories

- As a **sprint planner**, I want PYPOST-1115 broken into ≤5 SP children with
  clear acceptance criteria, so each can enter Top-Down without re-estimating
  an 8 SP blob.
- As an **implementer**, I want each child scoped to one primary outcome
  (evaluation contract, dependency-pin attempt, or application-side
  mitigation/settlement), so Steps 1–8 stay coherent.
- As a **CI owner**, I want future mitigation work to prove success against
  the existing stress detector and leave settle e2e assertions intact, so
  native teardown risk is visibly reduced without trading away coverage.
- As a **maintainer**, I want sibling follow-ups from PYPOST-1040 (e.g.
  duration-report xfail labeling) left out of this epic, so mitigation
  decomposition stays focused.

## Definition of Done

PYPOST-1203 is done when:

1. Epic PYPOST-1115 scope is inventoried against the PYPOST-1040 diagnosis,
   shipped stress detector, and documented settle teardown guidance.
2. Natural work slices are identified and recorded as proposed children
   (provisional IDs MITIGATE-1 … MITIGATE-3) with summaries, preferred SP ≤5,
   dependencies, and acceptance criteria.
3. Out-of-epic siblings and explicit non-goals are listed.
4. Child Jira issues are created under PYPOST-1115 with clear acceptance
   criteria — done in Step 4:
   [PYPOST-1209](https://pypost.atlassian.net/browse/PYPOST-1209),
   [PYPOST-1210](https://pypost.atlassian.net/browse/PYPOST-1210),
   [PYPOST-1211](https://pypost.atlassian.net/browse/PYPOST-1211).
5. Each child is suitable for its own Top-Down Steps 1–8 (single primary
   outcome; testable or docs-verifiable acceptance).
6. `ai-tasks/PYPOST-1203/10-requirements.md` and `00-roadmap.md` exist and
   Step 1 has passed its acceptance gate.

## Task Description

### Problem

PYPOST-1115 is an oversized epic: attempt one or more mitigations for the
intermittent PySide6/shiboken6 `QWidgetItem` GC-teardown crash diagnosed by
PYPOST-1040. As a single ticket it exceeds the preferred ≤5 SP top-down unit.
At Step 1 inventory time only PYPOST-1203 sat under the epic;
implementation children
PYPOST-1209 / PYPOST-1210 / PYPOST-1211 were created in Step 4.

### Current state (inventory)

- **Diagnosis (done)** — PYPOST-1040: upstream binding lifecycle defect;
  trigger surface is `SettingsDialog` nested layouts under pytest forced
  cyclic GC; measured **32.5% (13/40)** on Linux/Python 3.13.5 /
  PySide6-shiboken6 **6.11.1** (CI pin). Gap: no mitigation applied.
- **Stress detector** — `tests/test_agent_dialog_settle_teardown_stress.py`
  (`STRESS_ITERATIONS = 25`, `xfail(strict=False)`, `slow`). Gap: still
  expects crashes until a mitigation lands (future XPASS is the signal).
- **Settle e2e** — `tests/test_agent_dialog_settle_e2e.py` assertions must
  remain valid. Gap: process may still die post-PASS under GC.
- **Binding pin** — `pyproject.toml` pins `PySide6==6.11.1`. Gap: pin-change
  experiment not yet run against the stress harness.
- **Session shutdown** — `AgentAppSession.shutdown` completes successfully
  before the crash (not implicated as a bug). Gap: optional deliberate
  post-shutdown collection is an untried candidate.
- **Docs** — `doc/dev/agent_dialog_settle.md` documents the diagnosis and
  detector. Gap: mitigation outcome and any marker/doc updates still open.
- **Related debt** — PYPOST-1116 (duration-report xfail labeling); distinct
  large-batch GUI instability notes under PYPOST-1070. Gap: separate tickets
  — not this epic.

Epic acceptance (must be covered by the **set** of children, not each child):

- Stress harness (`N=25`) shows a **materially reduced** crash rate
- No regression to `tests/test_agent_dialog_settle_e2e.py` assertions
- Candidates named by the epic remain available until success or exhaustion:
  pin a different PySide6/shiboken6 patch; break the reference cycle; explicit
  `gc.collect` after shutdown

### Scope (this task)

- Inventory epic vs PYPOST-1040 diagnosis, detector, pin, and docs.
- Propose ≤5 SP child slices with acceptance criteria and preferred SP.
- Record decisions and create Jira children under PYPOST-1115 (Step 4:
  PYPOST-1209 / PYPOST-1210 / PYPOST-1211).
- Keep wording at business/product level (no mitigation design here).

### Out of scope (this task)

- Implementing any mitigation in product or dependency code.
- Creating Jira children in Step 1 (deferred to Step 4; done).
- Re-diagnosing the crash (PYPOST-1040 is closed for diagnosis).
- Delivering PYPOST-1116 or unrelated GUI-batch instability work.
- Guaranteeing an upstream PySide fix (mitigation may be local only).
- User-facing `doc/user/` docs unless a child explicitly requires them.

### Functional Requirements (decomposition)

- FR1: Requirements name every proposed child with summary, preferred SP
  (Fibonacci ≤5), dependencies, and acceptance criteria.
- FR2: Together, children cover evaluation contract, dependency-pin attempt,
  application-side candidates, and epic success measurement (stress + e2e).
- FR3: Children exclude unrelated PYPOST-1040 siblings (e.g. PYPOST-1116).
- FR4: Each child is independently runnable through Top-Down Steps 1–8.
- FR5: Step 4 created Story issues under parent PYPOST-1115 with labels
  consistent with the epic (`tech-debt`, `qwitem-gc-mitigate` per
  architecture).

### Non-Functional Requirements

- **NFR-1 Clarity:** Child summaries and AC are unambiguous for estimation
  and review without re-reading the full PYPOST-1040 architecture.
- **NFR-2 Size:** Preferred story points ≤5; avoid recreating an 8 SP child.
- **NFR-3 Traceability:** Provisional IDs map to Jira keys once created
  (record mapping in roadmap after creation).
- **NFR-4 Stop-on-success:** Later candidates need not be executed if an
  earlier child already meets epic success criteria (record skip with
  evidence). Soft-skip must not orphan detector marker/docs settlement —
  transfer ownership to the succeeding child’s AC at create time.
- **NFR-5 Measurement:** Crash-rate claims use the existing stress detector
  (`N=25`) unless a child documents a justified equivalent protocol.

### Constraints and Assumptions

- PYPOST-1040 diagnosis stands: upstream defect + known trigger surface;
  mitigations may be dependency- or application-side without claiming a
  full upstream fix.
- Original epic estimate was 8 SP; three children totaling about that effort
  is preferred over many micro-slices.
- “Materially reduced” must be defined in MITIGATE-1 before pin/app work
  claims success (e.g. relative to the diagnosed ~32.5% baseline).
- Stress detector remains `slow` / opt-in unless a child explicitly changes
  that policy.
- Autonomous decisions below stand unless review rejects them.

### Main Entities (business)

| Entity | Role |
| --- | --- |
| Settle e2e path | Opens/dismisses Settings via agent session; may crash post-PASS |
| Stress detector | Repeated isolated child runs that surface native teardown death |
| Settings dialog subtree | Trigger surface for the binding lifecycle defect |
| Binding pin | Locked PySide6/shiboken6 version used by app and CI |
| Application-side mitigation | Local lifecycle change that avoids deferred cyclic GC harm |
| Evaluation contract | Shared success threshold, candidate order, and stop rules |
| Epic success | Material crash-rate drop + intact e2e assertions |

### Proposed Child Story Breakdown (under PYPOST-1115)

Provisional IDs **MITIGATE-1 … MITIGATE-3** mapped to Jira Stories created under
PYPOST-1115 in Step 4 of PYPOST-1203.

| Provisional ID | Jira key | Browse |
| --- | --- | --- |
| MITIGATE-1 | [PYPOST-1209](https://pypost.atlassian.net/browse/PYPOST-1209) | https://pypost.atlassian.net/browse/PYPOST-1209 |
| MITIGATE-2 | [PYPOST-1210](https://pypost.atlassian.net/browse/PYPOST-1210) | https://pypost.atlassian.net/browse/PYPOST-1210 |
| MITIGATE-3 | [PYPOST-1211](https://pypost.atlassian.net/browse/PYPOST-1211) | https://pypost.atlassian.net/browse/PYPOST-1211 |

#### MITIGATE-1 — [PYPOST-1209](https://pypost.atlassian.net/browse/PYPOST-1209) Document mitigation evaluation contract and baseline

- **Preferred SP / estimated SP:** 2 / 2
- **Depends on:** —
- **Acceptance:**
  - Dev-facing notes state the diagnosed baseline crash rate and environment.
  - “Materially reduced” success threshold is explicit and reviewable.
  - Candidate order and stop-on-success rules are written (pin before
    application-side attempts unless justified otherwise), including which
    child owns detector marker/docs settlement when MITIGATE-3 is skipped.
  - Stress detector (`N=25`) and settle e2e no-regression are named as the
    proof surfaces for later children.

#### MITIGATE-2 — [PYPOST-1210](https://pypost.atlassian.net/browse/PYPOST-1210) Attempt PySide6/shiboken6 pin mitigation

- **Preferred SP / estimated SP:** 3 / 3
- **Depends on:** MITIGATE-1 / PYPOST-1209 (contract)
- **Acceptance:**
  - A different PySide6/shiboken6 patch (or documented decision not to change
    pin, with reason) is evaluated against the stress detector.
  - Crash-rate outcome vs baseline is recorded.
  - Settle e2e assertions remain green for the evaluated pin choice.
  - If epic success is already met, later application-side work may be
    skipped per MITIGATE-1 stop rules **only when** this child’s AC also
    covers detector marker/docs settlement for that success path (so
    soft-skip of MITIGATE-3 does not leave settlement without an owner).
  - When create-time drafts allow soft-skip of MITIGATE-3 on pin success,
    this child’s acceptance **must** include updating detector marker/docs
    to match the pin outcome.

#### MITIGATE-3 — [PYPOST-1211](https://pypost.atlassian.net/browse/PYPOST-1211) Attempt application-side mitigations and settle outcome

- **Preferred SP / estimated SP:** 5 / 5
- **Depends on:** MITIGATE-1 / PYPOST-1209; MITIGATE-2 / PYPOST-1210
  inconclusive or insufficient (soft gate — skip with evidence if pin
  already succeeded **and** MITIGATE-2 owns marker/docs settlement for
  that path)
- **Acceptance:**
  - At least one application-side candidate from the epic is attempted
    (break reference cycle and/or deliberate post-shutdown collection)
    unless MITIGATE-2 already met epic success.
  - Stress detector result vs baseline is recorded for the chosen attempt(s).
  - Settle e2e assertions show no regression.
  - When this child runs: detector marker/docs are updated to match the
    final outcome (success, partial, or all candidates exhausted with
    evidence). Soft-skip is allowed only if MITIGATE-2 already accepted
    settlement ownership for the pin-success path.

**Suggested order:** PYPOST-1209 (MITIGATE-1) → PYPOST-1210 (MITIGATE-2) →
PYPOST-1211 (MITIGATE-3) (MITIGATE-3 only when pin work does not already
satisfy the epic; settlement always has an owner — MITIGATE-2 /
PYPOST-1210 on pin-success skip, otherwise MITIGATE-3 / PYPOST-1211).

**Sizing note:** Preferred total 2+3+5 = 10 SP is slightly above the former
8 SP debt estimate to keep each child ≤5 and Top-Down-friendly. Do not merge
MITIGATE-2 and MITIGATE-3 back into one >5 SP ticket. Do not split
application-side candidates into separate >5-total micro-tickets unless
review requires it — they share one measurement surface and stop rule.

**Explicitly not children of PYPOST-1115:**

| Ticket / topic | Why excluded |
| --- | --- |
| PYPOST-1040 | Diagnosis complete; this epic is mitigation only |
| PYPOST-1116 | Duration-report xfail/XPASS labeling (separate debt) |
| PYPOST-1070 batch GUI notes | Related class, not same confirmed root cause; separate |

## Q&A

- Q: Why decompose instead of implementing mitigation in 1203?
  A: Sprint goal is epic decomposition (PYPOST-1202–1205); implement
  mitigation via children under 1115.
- Q: Why three children, not one per candidate?
  A: Pin vs application-side are different risk surfaces; evaluation
  contract must come first; combining both app-side candidates under
  MITIGATE-3 keeps total slices near the original 8 SP without an 8 SP
  child.
- Q: Must all three candidates be tried?
  A: **No** — stop when epic success is met; remaining candidates are
  skipped with recorded evidence.
- Q: Is the exact pin version or cycle-break technique chosen here?
  A: **No** — Step 1 forbids architecture; children state outcomes only.
- Q: Does success require removing the stress `xfail`?
  A: Outcome settlement (marker/docs) must always have an owner. Default
  owner is MITIGATE-3 when it runs. If MITIGATE-3 is soft-skipped because
  the pin already meets epic success, MITIGATE-2 AC must include
  marker/docs settlement. Exact marker policy is decided in child
  Top-Down, not here.
- Q: Are existing children under 1115?
  A: After Step 4: PYPOST-1203 plus implementation children
     PYPOST-1209 / PYPOST-1210 / PYPOST-1211 (MITIGATE-1..3).

## References

- [PYPOST-1203](https://pypost.atlassian.net/browse/PYPOST-1203) — this
  decompose story
- [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115) — parent
  epic
- [PYPOST-1040](https://pypost.atlassian.net/browse/PYPOST-1040) —
  diagnosis and stress detector
- [PYPOST-1116](https://pypost.atlassian.net/browse/PYPOST-1116) —
  excluded sibling (duration-report xfail labeling)
- `ai-tasks/PYPOST-1040/20-architecture.md` — root-cause evidence
- `ai-tasks/PYPOST-1040/60-tech-debt.md` — mitigation candidates source
- `doc/dev/agent_dialog_settle.md` — teardown stress detector docs
- `tests/test_agent_dialog_settle_teardown_stress.py` — stress harness
- `tests/test_agent_dialog_settle_e2e.py` — settle e2e assertions
