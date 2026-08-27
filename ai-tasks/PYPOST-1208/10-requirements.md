# PYPOST-1208: Verify attach path with tests as feasible

## Goals

Epic [PYPOST-991](https://pypost.atlassian.net/browse/PYPOST-991)
([PYPOST-952](https://pypost.atlassian.net/browse/PYPOST-952) TD-2) ships
attach so operators can drive an already-running desktop through agent-UI
MCP. ATTACH-2 /
[PYPOST-1207](https://pypost.atlassian.net/browse/PYPOST-1207) delivered
that capability with a baseline proof set. Operators and maintainers still
need **confidence** that attach behaves as documented across the full
feasible matrix—and a clear record of anything that cannot run under
project `make test` norms.

**Business goal:** Prove the attach path with automated tests under project
make/test norms (or the largest feasible subset). Document any
non-automatable gap with a manual check. Keep developer docs and tests in
agreement about what is proven versus what must be checked by hand.

**Why this matters:** Without ATTACH-3, epic “tests as feasible” remains
open: capability exists, but the broader lifecycle and catalog coverage are
only partially proven, and docs still point at this story for the matrix.
Verification closes the trust loop after ATTACH-1 docs and ATTACH-2
capability.

**Provisional ID:** ATTACH-3 (from
[PYPOST-1202](https://pypost.atlassian.net/browse/PYPOST-1202) decomposition).
Hard-depends on ATTACH-2 / PYPOST-1207 (Done).

## Programming Language

- **This task (PYPOST-1208):** Python (automated tests under project make/test
  norms; English Markdown for Top-Down artifacts and any doc alignment with
  proven vs manual coverage).

## User Stories

- As a **maintainer**, I want automated tests to prove attach (or the largest
  feasible subset) under `make test`, so regressions are caught in CI without
  relying on ad-hoc manual runs alone.
- As an **ATTACH-2 verifier**, I want remaining attach outcomes from the soft
  contract (catalog parity beyond click, host exit, sidecar exit, endpoint /
  version expectations where feasible) covered or explicitly marked manual,
  so docs and tests tell the same story.
- As an **operator reading developer docs**, I want the attach verification
  section to state clearly what automated tests prove and what I must check
  manually, so I do not assume unproven behavior.
- As a **security-conscious maintainer**, I want verification to confirm
  attach still does **not** expand UI tools onto product MCP and does **not**
  silently spawn when attach fails, so packaging and fail-closed posture stay
  intact.
- As an **epic owner**, I want PYPOST-991 “tests as feasible” acceptance
  satisfied together with ATTACH-1/2, so the attach epic can close without a
  second capability rewrite.

## Definition of Done

PYPOST-1208 is done when:

1. Automated tests prove attach (or the **largest feasible subset**) under
   project **make/test** norms.
2. Any scenario that cannot be automated under those norms is **documented
   with a manual check** (steps and expected outcome).
3. Developer docs and tests **agree**: what is claimed as proven matches what
   tests cover; gaps are explicit, not implied.
4. Baseline proofs already shipped with ATTACH-2 remain green and are treated
   as part of the attach verification surface (not discarded).
5. Non-goals are respected: no re-implementation of attach; no primary
   trust/lifecycle rewrite beyond aligning docs with proven/manual coverage;
   no PYPOST-990/992/993 work.
6. `ai-tasks/PYPOST-1208/10-requirements.md` and `00-roadmap.md` exist and
   Step 1 has passed its acceptance gate.

## Task Description

### Problem

ATTACH-2 shipped attach and a baseline automated proof (CLI attach mode,
no silent spawn on fail, unbound fail, host+client click round-trip,
detach/rebind). Docs still defer the **broader** verification matrix to this
story. ATTACH-2 tech-debt records uncovered feasible cases (remaining UI
catalog actions over attach, host-exit / sidecar-exit outcomes, endpoint /
protocol expectations, concurrent or race scenarios, and explicit manual/CI
gap documentation). Without ATTACH-3, the epic’s “tests as feasible”
acceptance is incomplete and docs/tests can drift.

### Current state (inventory)

- **Capability (ATTACH-2 Done)** — Attach path is runnable; spawn-session
  default preserved; UI tools remain off product MCP.
- **Baseline automated proofs** — Present under the attach test surface
  (`tests/test_agent_ui_attach.py` and related suite references in
  `doc/dev/agent_ui_actions_mcp.md`): CLI `--attach`, no-spawn on attach,
  unbound fail, host+client `ui_click` round-trip, detach/rebind; spawn /
  packaging regressions covered elsewhere.
- **Docs** — Attach path, trust, and lifecycle documented (ATTACH-1); capability
  note updated (ATTACH-2). Broader CI/manual matrix still points at
  PYPOST-1208.
- **Residual matrix (from ATTACH-2 tech-debt, owned here)** — Remaining UI
  catalog actions over attach (`ui_fill` / `ui_select` / `ui_send_key`);
  host exit → sidecar unbound; sidecar exit → host still listening; protocol
  version / endpoint override expectations as feasible; concurrent clients /
  stale-endpoint races as feasible; explicit manual / CI gap documentation.
- **Make/test norms** — Fast suite via `make test` (and documented
  PYTEST_ARGS targeting attach tests). Anything that cannot run under those
  norms must become a documented manual check, not an invisible hole.

### Scope (this task)

- Expand attach **verification** to the largest feasible automated subset
  under project make/test norms.
- Retain and keep green the ATTACH-2 baseline proofs as part of that surface.
- For each residual lifecycle or catalog scenario: either automate it under
  make/test norms, or document a **manual check** with expected outcome.
- Align developer docs so proven vs manual coverage matches reality (no claim
  of automated proof where only manual applies; no silent omission of known
  gaps).
- Satisfy epic PYPOST-991 “tests as feasible” together with ATTACH-1/2.

### Out of scope (this task)

- **Implementing** attach itself (**ATTACH-2** /
  [PYPOST-1207](https://pypost.atlassian.net/browse/PYPOST-1207)) — already
  Done; do not re-build the capability.
- Primary trust / lifecycle **documentation** as a first-time contract
  (**ATTACH-1** /
  [PYPOST-1206](https://pypost.atlassian.net/browse/PYPOST-1206)) — Done;
  this story may only align docs with what tests prove and what remains
  manual.
- [PYPOST-990](https://pypost.atlassian.net/browse/PYPOST-990) (HTTP
  transport for agent-UI MCP).
- [PYPOST-992](https://pypost.atlassian.net/browse/PYPOST-992) (spawn-session
  `call_tool` tests).
- [PYPOST-993](https://pypost.atlassian.net/browse/PYPOST-993) (seed
  injection for sidecar-owned session).
- Mounting UI tools on product MCP (forbidden).
- Redesigning interactive human UX.
- Choosing new IPC/transport mechanisms in this Step 1 artifact
  (architecture owns any test-harness design later; requirements stay on
  outcomes).

### Functional Requirements

- **FR1:** Automated tests under project make/test norms prove attach bind
  success against a live desktop-style UI target (or the largest feasible
  equivalent already used by baseline proofs).
- **FR2:** Automated tests prove **attach fail** stays unbound and does
  **not** silently take the spawn-session path.
- **FR3:** Automated tests prove **detach** ends the client binding while the
  host remains available to bind again (rebind).
- **FR4:** Automated tests prove at least one UI-action over attach against a
  live widget tree (baseline: click). Expand, as feasible under make/test
  norms, to the rest of the operator-facing UI-action catalog over attach
  (`fill`, `select`, `send_key`).
- **FR5:** **Host exit** outcome is either proven automatically (desktop /
  host ends → attach binding ends; sidecar/client is unbound) or documented
  as a manual check with expected outcome.
- **FR6:** **Sidecar exit** outcome is either proven automatically (sidecar
  ends → binding ends from sidecar side; host remains listening) or
  documented as a manual check with expected outcome.
- **FR7:** Endpoint override / default-endpoint operator expectations are
  either proven automatically under make/test norms or documented as a
  manual check.
- **FR8:** Protocol-version / handshake operator expectations that are
  product-visible are either proven as feasible or documented as a manual
  check (incomplete negotiation may remain a known gap if not automatable
  without capability changes—document, do not silently invent enforcement).
- **FR9:** Concurrent-client or stale-endpoint race scenarios are either
  covered by the largest feasible automated subset or explicitly listed as
  manual / accepted residual with a check.
- **FR10:** Packaging separation remains verified: UI-action tools stay off
  product MCP (existing packaging proofs may satisfy; attach verification
  must not regress or contradict them).
- **FR11:** Spawn-session path remains available and is not broken by
  attach verification work (regression coverage may reuse existing suite).
- **FR12:** Developer docs state which attach scenarios are **automated**
  under make/test and which require a **manual check**, in agreement with
  the test surface.
- **FR13:** Every non-automatable gap in the residual matrix has a written
  manual check (what to run, what “pass” looks like).

### Non-Functional Requirements

- **NFR-1 Make/test norms:** New automated proofs must run under project
  `make test` (fast suite norms); do not invent a parallel unverified runner
  as the only proof.
- **NFR-2 Feasibility honesty:** Prefer the largest feasible automated
  subset over claiming full matrix coverage that CI cannot run.
- **NFR-3 Docs/tests agreement:** Claims in `doc/dev/` about attach
  verification must match automated coverage; gaps must be explicit.
- **NFR-4 Continuity:** ATTACH-2 baseline proofs remain green; attach
  capability behavior is not rewritten under the guise of testing.
- **NFR-5 Traceability:** Work remains under epic PYPOST-991 with clear
  sibling boundaries (1206 docs, 1207 capability, 1208 verification).
- **NFR-6 Local-host posture:** Verification respects that attach is a
  same-machine trust surface separate from product request-tool MCP (do not
  require remote-sandbox proofs).

### Constraints and Assumptions

- Language is **Python** for test and any minimal doc-alignment edits.
- ATTACH-2 / PYPOST-1207 is **Done** and is a **hard** dependency;
  capability exists; this story verifies it.
- ATTACH-1 / PYPOST-1206 is **Done**; soft contract for lifecycle meanings
  (success, fail, detach, host exit, sidecar exit) remains the product
  reference for what to prove or manually check.
- “Largest feasible subset” may leave some race/concurrency or full
  interactive-desktop scenarios as manual; that is acceptable if documented.
- Step 1 does **not** prescribe test file layout, harness APIs, or IPC
  internals—only verification outcomes and doc/test agreement.
- Story points: 3 (verification and gap documentation after ATTACH-2; not a
  second full attach implementation).

### Main Entities (business)

| Entity | Role |
| --- | --- |
| Attach path | Bind agent-UI MCP to already-running desktop |
| Spawn-session path | Sidecar-owned session (must not regress) |
| Attach verification matrix | Scenarios to prove or mark manual |
| Automated proof | Test under project make/test norms |
| Manual check | Documented non-automatable verification step |
| Attach lifecycle outcomes | Success, fail, detach, host exit, sidecar exit |
| UI-action catalog | Operator-facing `ui_*` tools over attach |
| Product MCP packaging gate | Ensures UI tools stay off product MCP |
| Developer docs | State proven vs manual coverage |
| Operator / maintainer | Consumes proofs and manual checks |

### Acceptance mapping

| Acceptance criterion (Jira) | Requirement coverage |
| --- | --- |
| Automated tests prove attach (or largest feasible subset) under make/test norms | FR1–FR4, FR7–FR11, NFR-1, NFR-2 |
| Any non-automatable gap documented with a manual check | FR5–FR9, FR13, NFR-2 |
| Docs and tests agree | FR12, NFR-3 |

## Q&A

- Q: Why is this not another attach implementation story?
  A: ATTACH-2 already delivered capability. This story proves it and
  documents gaps so the epic’s “tests as feasible” acceptance can close.
- Q: What if some lifecycle cases cannot run under `make test`?
  A: Document a **manual check** with expected outcome; do not pretend they
  are automated.
- Q: Must every residual ATTACH-2 debt row become an automated test?
  A: **No** — automate the largest feasible subset; the rest must be
  explicit manual/residual documentation.
- Q: May this story rewrite attach or primary trust docs?
  A: **No** capability rewrite. Docs may only align proven vs manual
  coverage with ATTACH-1/2 narratives.
- Q: Does attach replace spawn-session under verification?
  A: **No** — both paths remain valid; spawn must not regress.
- Q: Who owns product MCP `call_tool` / HTTP / seed work?
  A: Out of scope — PYPOST-990 / 992 / 993.
- Q: Is test harness design chosen here?
  A: **No** — Step 1 forbids architecture; outcomes and agreement only.

## References

- [PYPOST-1208](https://pypost.atlassian.net/browse/PYPOST-1208) — this story
  (ATTACH-3)
- [PYPOST-991](https://pypost.atlassian.net/browse/PYPOST-991) — parent epic
- [PYPOST-1202](https://pypost.atlassian.net/browse/PYPOST-1202) —
  decompose story / ATTACH-1..3 mapping
- [PYPOST-1207](https://pypost.atlassian.net/browse/PYPOST-1207) — ATTACH-2
  capability (hard dependency, Done)
- [PYPOST-1206](https://pypost.atlassian.net/browse/PYPOST-1206) — ATTACH-1
  docs (Done)
- [PYPOST-952](https://pypost.atlassian.net/browse/PYPOST-952) — shipped
  stdio agent-UI MCP
- `ai-tasks/PYPOST-1207/60-tech-debt.md` — residual matrix owned by ATTACH-3
- `ai-tasks/PYPOST-1207/10-requirements.md` — capability requirements
- `ai-tasks/PYPOST-1202/10-requirements.md` — ATTACH-3 acceptance seed
- `doc/dev/agent_ui_actions_mcp.md` — attach path / lifecycle / test pointers
- `doc/dev/agent_lifecycle.md` — session and attach outcomes
- `doc/dev/mcp_trust_model.md` — separate trust surfaces
- `tests/test_agent_ui_attach.py` — ATTACH-2 baseline attach proofs
