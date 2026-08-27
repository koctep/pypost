# PYPOST-1204: Decompose epic — Diagnose large-batch Qt/PySide6 GUI test segfault

## Goals

Epic [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117)
(former Debt from [PYPOST-1070](https://pypost.atlassian.net/browse/PYPOST-1070)
`60-tech-debt.md`) asks maintainers to **diagnose** a pre-existing native
segfault under large-batch Qt/PySide6 GUI pytest load in `apply_theme`,
produce a deterministic repro, decide shared-lifetime vs distinct
QStyle/QPalette accumulation, evaluate safe mitigation (bounded batches
and/or process isolation), and document CI/test-infrastructure ownership.
The epic was promoted from Debt because its estimate (13 SP) exceeded the
SP>6 threshold; story points were cleared on the epic. This story
([PYPOST-1204](https://pypost.atlassian.net/browse/PYPOST-1204)) exists so
the epic can be split into **implementable child issues** (each ≤5 SP
preferred), each sized for a full Top-Down cycle (Steps 1–8).

**Business goal:** Planners and implementers get clear, separately
deliverable slices that together satisfy PYPOST-1117 acceptance
(deterministic repro; root-cause determination vs PYPOST-1040/1115;
safe mitigation; CI ownership documented), without one oversized ticket
blocking sprint flow.

**Why diagnosis and mitigation matter (parent epic):** When ~110
GUI-heavy test modules run together in one pytest process with
`QT_QPA_PLATFORM=offscreen`, the process dies natively at
`pypost/ui/styles/style_manager.py:102` in `apply_theme` (around
`app.setStyle(...)` / `QStyleFactory.create("Fusion")`). Individual
modules and eight bounded batches pass (~1,384 tests). Leaving this
undiagnosed and unmitigated blocks trustworthy single-process full GUI
batches and forces ad-hoc batching without owned CI policy.

## Programming Language

- **This task (PYPOST-1204):** English Markdown planning artifacts and
  Jira issue creation (no product code change required for decomposition
  itself).
- **Child stories under PYPOST-1117:** Python (PyPost desktop styles,
  pytest GUI suite, CI/test harness), with English Markdown for
  developer docs.

## User Stories

- As a **sprint planner**, I want PYPOST-1117 broken into ≤5 SP children
  with clear acceptance criteria, so each can enter Top-Down without
  re-estimating a 13 SP blob.
- As an **implementer**, I want each child scoped to one primary outcome
  (repro baseline, root-cause diagnosis, or mitigation plus CI
  ownership), so Steps 1–8 stay coherent.
- As a **CI owner**, I want future work to leave a documented ownership
  boundary and tradeoffs for how GUI tests are batched or isolated, so
  green CI does not depend on tribal knowledge of “run in eight chunks.”
- As a **maintainer**, I want PYPOST-1040 / PYPOST-1115 left as related
  prior art (distinct crash site/trigger), not merged into this epic’s
  children, so large-batch `apply_theme` work stays focused.

## Definition of Done

PYPOST-1204 is done when:

1. Epic PYPOST-1117 scope is inventoried against the PYPOST-1070 finding,
   known pass/fail batch behavior, and related PYPOST-1040/1115 prior
   art (explicitly distinguished).
2. Natural work slices are identified and recorded as proposed children
   (provisional IDs REPRO-1, DIAG-1, MITIGATE-1) with summaries,
   preferred SP ≤5, dependencies, and acceptance criteria.
3. Out-of-epic siblings and explicit non-goals are listed.
4. Child Jira issues are created under PYPOST-1117 with clear acceptance
   criteria — done in Step 4:
   [PYPOST-1212](https://pypost.atlassian.net/browse/PYPOST-1212),
   [PYPOST-1213](https://pypost.atlassian.net/browse/PYPOST-1213),
   [PYPOST-1214](https://pypost.atlassian.net/browse/PYPOST-1214).
5. Each child is suitable for its own Top-Down Steps 1–8 (single primary
   outcome; testable or docs-verifiable acceptance).
6. `ai-tasks/PYPOST-1204/10-requirements.md` and `00-roadmap.md` exist and
   Step 1 has passed its acceptance gate.

## Task Description

### Problem

PYPOST-1117 is an oversized epic: diagnose large-batch Qt/PySide6 GUI
test segfault in `apply_theme`, create a deterministic subprocess-level
repro, determine root-cause class vs PYPOST-1040/1115, evaluate and
implement safe mitigation, and document CI ownership. As a single ticket
it exceeds the preferred ≤5 SP top-down unit. At Step 1 inventory time
only PYPOST-1204 sat under the epic; implementation children
PYPOST-1212 / PYPOST-1213 / PYPOST-1214 were created in Step 4.

### Current state (inventory)

- **Observed crash** — Native segfault when ~110 GUI-heavy modules run
  in one pytest process (`QT_QPA_PLATFORM=offscreen`). Crash site:
  `pypost/ui/styles/style_manager.py:102` in `apply_theme` (around
  `app.setStyle(...)` / `QStyleFactory.create("Fusion")`). Gap: no
  owned deterministic repro artifact or diagnosis conclusion yet.
- **Independence from PYPOST-1070** — Reproduces against pre-PYPOST-1070
  test contents; unrelated to that task’s import-order / `pytestmark`
  restructure. Gap: still treated as environment/batch-load instability.
- **Bounded batches pass** — Individual modules and eight bounded
  batches pass (~1,384 tests). Gap: sustained single-process GUI load
  still crashes; batching is an informal workaround, not owned policy.
- **Related prior art** — PYPOST-1040 / PYPOST-1115:
  SettingsDialog/QWidgetItem GC-teardown crash (different site and
  trigger). Gap: open whether large-batch `apply_theme` shares
  Shiboken/Qt object-lifetime root cause or is distinct
  QStyle/QPalette accumulation under repeated theme apply.
- **Mitigation candidates (named by epic, unevaluated)** — Bounded
  GUI-test batches and/or process isolation; CI/test-infra ownership
  and tradeoffs must be documented. Gap: neither implemented as owned
  policy nor proven against a deterministic repro.
- **Source** — `ai-tasks/PYPOST-1070/60-tech-debt.md` (former ~13 SP
  debt promoted to epic). Gap: closed in Step 4 — children PYPOST-1212 /
  PYPOST-1213 / PYPOST-1214 created under the epic.

Epic acceptance (must be covered by the **set** of children, not each
child):

- Deterministic subprocess-level repro and evidence baseline
- Root-cause determination (shared lifetime vs distinct
  QStyle/QPalette accumulation; distinguish from PYPOST-1040/1115)
- Safe mitigation evaluated/implemented (bounded batches and/or process
  isolation)
- CI/test-infrastructure ownership and tradeoffs documented

### Scope (this task)

- Inventory epic vs PYPOST-1070 finding, batch pass/fail facts, and
  related prior art.
- Propose ≤5 SP child slices with acceptance criteria and preferred SP.
- Record decisions and create Jira children under PYPOST-1117 (Step 4:
  PYPOST-1212 / PYPOST-1213 / PYPOST-1214).
- Keep wording at business/product level (no repro harness or
  mitigation design here).

### Out of scope (this task)

- Implementing diagnosis, repro harness, or mitigation in product or
  CI code.
- Creating Jira children in Step 1 (deferred to Step 4; done).
- Merging this work into PYPOST-1040 / PYPOST-1115 (related class, not
  confirmed same root cause).
- Guaranteeing an upstream PySide/Shiboken fix (mitigation may be
  test-infra only).
- User-facing `doc/user/` docs unless a child explicitly requires them.
- Red automated tests on PYPOST-1204 itself — Step 3 is N/A for this
  decompose ticket; failing repros belong to child Top-Down cycles
  (especially REPRO-1).

### Functional Requirements (decomposition)

- FR1: Requirements name every proposed child with summary, preferred
  SP (Fibonacci ≤5), dependencies, and acceptance criteria.
- FR2: Together, children cover deterministic repro/baseline, root-cause
  diagnosis vs PYPOST-1040/1115, mitigation, and CI ownership docs.
- FR3: Children exclude PYPOST-1040 mitigation epic work (PYPOST-1115)
  and unrelated PYPOST-1070 follow-ups.
- FR4: Each child is independently runnable through Top-Down Steps 1–8.
- FR5: Step 4 created Story issues under parent PYPOST-1117 with labels
  consistent with the epic (`tech-debt`, `failing-test`,
  `gui-batch-segfault` per architecture).

### Non-Functional Requirements

- **NFR-1 Clarity:** Child summaries and AC are unambiguous for
  estimation and review without re-reading the full PYPOST-1070
  tech-debt write-up.
- **NFR-2 Size:** Preferred story points ≤5; avoid recreating a 13 SP
  child.
- **NFR-3 Traceability:** Provisional IDs map to Jira keys (recorded in
  roadmap and this file after Step 4 create).
- **NFR-4 Distinction:** Children must treat PYPOST-1040/1115 as related
  prior art until diagnosis proves otherwise — do not silently fold
  scopes.
- **NFR-5 Evidence:** Crash-site and batch-size claims in child work
  must cite reproducible commands/results, not anecdote alone.

### Constraints and Assumptions

- Original epic estimate was 13 SP; three children totaling about that
  effort is preferred over many micro-slices or a separate tiny docs-only
  fourth child (CI ownership folded into MITIGATE-1).
- Individual modules and eight bounded batches remain the known-good
  contrast to the crashing full single-process batch until a child
  updates that evidence.
- Mitigation may be test-infrastructure-only; production
  `apply_theme` behavior need not change if isolation/batching is the
  accepted safe path — decided by children, not here.
- Autonomous decisions below stand unless review rejects them.

### Main Entities (business)

| Entity | Role |
| --- | --- |
| Large-batch GUI pytest run | Single-process run of many GUI-heavy modules that triggers the crash |
| Bounded batch run | Smaller chunked GUI runs that currently pass |
| Theme apply path | `apply_theme` / style factory surface where the crash is observed |
| Deterministic repro | Owned, repeatable subprocess-level procedure that surfaces the crash |
| Root-cause class | Shared Shiboken/Qt lifetime vs distinct QStyle/QPalette accumulation |
| Related teardown epic | PYPOST-1040/1115 SettingsDialog/QWidgetItem GC crash (distinct site) |
| Safe mitigation | Bounded GUI-test batches and/or process isolation that stops native death |
| CI ownership | Who owns batching/isolation policy and documented tradeoffs |

### Proposed Child Story Breakdown (under PYPOST-1117)

Provisional IDs **REPRO-1**, **DIAG-1**, **MITIGATE-1** mapped to Jira
Stories created under PYPOST-1117 in Step 4 of PYPOST-1204.

| Provisional ID | Jira key | Browse |
| --- | --- | --- |
| REPRO-1 | [PYPOST-1212](https://pypost.atlassian.net/browse/PYPOST-1212) | https://pypost.atlassian.net/browse/PYPOST-1212 |
| DIAG-1 | [PYPOST-1213](https://pypost.atlassian.net/browse/PYPOST-1213) | https://pypost.atlassian.net/browse/PYPOST-1213 |
| MITIGATE-1 | [PYPOST-1214](https://pypost.atlassian.net/browse/PYPOST-1214) | https://pypost.atlassian.net/browse/PYPOST-1214 |

#### REPRO-1 — [PYPOST-1212](https://pypost.atlassian.net/browse/PYPOST-1212) Deterministic repro and evidence baseline

- **Preferred SP / estimated SP:** 3 / 3
- **Depends on:** —
- **Acceptance:**
  - A documented, repeatable subprocess-level procedure reproduces the
    large-batch native crash (or a justified equivalent that matches the
    epic’s crash site and load class).
  - Baseline evidence records environment, command shape, and contrast
    that bounded batches / individual modules pass.
  - Crash observation is tied to the known `apply_theme` / style-factory
    site (or updated with evidence if the site moves under the repro).
  - Later children can cite this baseline without re-deriving the
    procedure from PYPOST-1070 notes alone.

#### DIAG-1 — [PYPOST-1213](https://pypost.atlassian.net/browse/PYPOST-1213) Root-cause diagnosis (lifetime vs QStyle/QPalette)

- **Preferred SP / estimated SP:** 5 / 5
- **Depends on:** REPRO-1 / PYPOST-1212 (stable repro/baseline)
- **Acceptance:**
  - A written diagnosis concludes whether the large-batch crash shares
    Shiboken/Qt object-lifetime behavior with PYPOST-1040/1115 or is a
    distinct QStyle/QPalette accumulation issue (or another justified
    class with evidence).
  - Distinction from SettingsDialog/QWidgetItem GC-teardown is explicit
    (same class vs different class; site/trigger comparison).
  - Evidence is sufficient for MITIGATE-1 to choose mitigation without
    re-opening the class question.
  - Dev-facing notes record the conclusion for future maintainers.

#### MITIGATE-1 — [PYPOST-1214](https://pypost.atlassian.net/browse/PYPOST-1214) Safe mitigation and CI ownership docs

- **Preferred SP / estimated SP:** 5 / 5
- **Depends on:** REPRO-1 / PYPOST-1212; DIAG-1 / PYPOST-1213 (diagnosis
  informs which mitigation is “safe”)
- **Acceptance:**
  - At least one epic-named mitigation path is evaluated and, if safe,
    implemented: bounded GUI-test batches and/or process isolation
    (or a justified equivalent that stops the native death under the
    repro).
  - Outcome is proven against the REPRO-1 procedure (crash avoided or
    residual risk documented with owner).
  - CI/test-infrastructure ownership and tradeoffs are documented
    (who owns the policy; what is gained/lost vs single-process full
    batches).
  - No silent merge into PYPOST-1115 scope; cross-links stay explicit.

**Suggested order:** REPRO-1 → DIAG-1 → MITIGATE-1.

**Sizing note:** Preferred total 3+5+5 = 13 SP matches the former debt
estimate while keeping each child ≤5 and Top-Down-friendly. CI ownership
is folded into MITIGATE-1 (no fourth CI-only child) to keep total
children ≤3. Do not merge DIAG-1 and MITIGATE-1 back into one >5 SP
ticket.

**Explicitly not children of PYPOST-1117:**

| Ticket / topic | Why excluded |
| --- | --- |
| PYPOST-1040 | Distinct SettingsDialog/QWidgetItem diagnosis (prior art only) |
| PYPOST-1115 | Mitigation for that distinct teardown crash (separate epic) |
| PYPOST-1070 | Import-order / E402 work that discovered but did not own this crash |
| PYPOST-1110 / PYPOST-1111 | Pre-existing unrelated suite failures from PYPOST-1070 notes |

## Q&A

- Q: Why decompose instead of diagnosing/mitigating in 1204?
  A: Sprint goal is epic decomposition (PYPOST-1202–1205); implement
  via children under 1117.
- Q: Why three children, not four (separate CI docs)?
  A: CI ownership is inseparable from choosing bounded batches / process
  isolation; folding docs into MITIGATE-1 keeps total children ≤3 and
  total SP near the former 13.
- Q: Why not fold this into PYPOST-1115?
  A: Different crash site and trigger; PYPOST-1070 explicitly
  recommended a separate ticket until shared root cause is proven.
- Q: Is the exact repro harness or isolation mechanism chosen here?
  A: **No** — Step 1 forbids architecture; children state outcomes only.
- Q: Does PYPOST-1204 itself get a red test in Step 3?
  A: **No** — this ticket is decompose/planning only. Step 3 is N/A;
  red tests belong to child Top-Down cycles (especially REPRO-1).
- Q: Must mitigation change production `apply_theme`?
  A: **Not required** — test-infra mitigation can satisfy the epic if
  diagnosis supports it and CI ownership is documented.
- Q: Are existing children under 1117?
  A: After Step 4: PYPOST-1204 plus implementation children
     PYPOST-1212 / PYPOST-1213 / PYPOST-1214 (REPRO-1 / DIAG-1 /
     MITIGATE-1).

## References

- [PYPOST-1204](https://pypost.atlassian.net/browse/PYPOST-1204) — this
  decompose story
- [PYPOST-1117](https://pypost.atlassian.net/browse/PYPOST-1117) —
  parent epic
- [PYPOST-1070](https://pypost.atlassian.net/browse/PYPOST-1070) —
  discovery source
- [PYPOST-1040](https://pypost.atlassian.net/browse/PYPOST-1040) —
  related prior-art diagnosis (distinct crash)
- [PYPOST-1115](https://pypost.atlassian.net/browse/PYPOST-1115) —
  related mitigation epic (excluded sibling scope)
- `ai-tasks/PYPOST-1070/60-tech-debt.md` — former ~13 SP debt source
- `ai-tasks/PYPOST-1202/10-requirements.md` — decompose artifact pattern
- `ai-tasks/PYPOST-1203/10-requirements.md` — decompose artifact pattern
