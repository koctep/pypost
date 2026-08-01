# PYPOST-943: CI make install smoke (slow) job fails on main

## Goals

The **make install smoke (slow)** GitHub Actions job is a dedicated CI gate
that proves a fresh contributor can run `make install` in an isolated
workspace with the real project dependency manifest. When this job is red,
maintainers lose continuous signal that the Makefile install path still
works end-to-end — even when unrelated changes (such as documentation-only
commits) land on `dev`.

On 2026-08-01 the job failed on push to `dev` while other CI jobs on the
same run — including agent e2e, which also runs `make install` from a full
checkout — completed successfully. The slow smoke failure is therefore
specific to the isolated install smoke contract, not a blanket pipeline
outage.

**Business need:** Restore a trustworthy green **make install smoke (slow)**
gate on `dev` so dependency and Makefile install regressions are caught
automatically without blocking merges on false positives from contract drift,
environment issues, or unrelated warnings.

**Source:** [PYPOST-943](https://pypost.atlassian.net/browse/PYPOST-943);
evidence from GitHub Actions run
[30691352912](https://github.com/koctep/pypost/actions/runs/30691352912).

## Programming Language

Python (pytest contract / smoke tests, `.cursor/lsr/do-python.md`,
`.cursor/lsr/do-testing.md`). Makefile and CI workflow remain the primary
automation interface. Developer documentation in English Markdown
(`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **maintainer**, I want the slow Makefile install smoke CI job to pass
  on `dev` when only documentation changes land, so a red pipeline means a
  real install or dependency problem.
- As a **contributor**, I want `make test-slow` (local equivalent of the CI
  smoke job) to reflect the same install contract CI enforces, so I can
  reproduce and fix failures before push.
- As a **reviewer**, I want the slow smoke job to distinguish real install
  regressions from infrastructure noise (cache warnings, runner deprecations),
  so merge decisions are not blocked by unrelated annotations.
- As a **release / dependency reviewer**, I want continuous proof that
  `make install` succeeds with the committed project manifest in an isolated
  workspace, so packaging or lock changes cannot silently break first-time
  setup.

## Definition of Done

- [ ] Root cause of the smoke job failure is identified and classified
  (test contract gap vs environment/cache vs flake).
- [ ] The **make install smoke (slow)** CI job on `dev` is green again for
  the documented install contract.
- [ ] Local `make test-slow` (or equivalent slow marker invocation) aligns
  with CI smoke behavior and passes for the same contract.
- [ ] If the failure is deterministic (non-flake), regression coverage or CI
  hardening is added or adjusted so the gap cannot recur unnoticed.
- [ ] Workflow annotations that are confirmed noise (Node.js 20 deprecation,
  pip cache HTTP 400 restore warning) do not block closure unless they are
  found to cause the failure.
- [ ] `make check` (or project-equivalent quality gate) remains green for the
  change set.
- [ ] Unticketed follow-ups (if any) live only in this task's
  `60-tech-debt.md`.

## Task Description

### Problem

The **make install smoke (slow)** CI job on `dev` is red. The job validates
that `make install` succeeds in an **isolated temporary workspace** with the
real committed project manifest — mirroring a fresh clone setup — separate
from the fast pytest matrix (PYPOST-559 / PYPOST-923).

The failure occurred on a push that changed only task documentation, not
Makefile, dependency, or workflow content. Other jobs on the same run that
exercise `make install` from a full repository checkout succeeded. The smoke
gate's business contract therefore appears broken while full-checkout install
paths still pass.

### Business need

Re-establish the slow smoke gate as a reliable, signal-rich check that the
Makefile install path works for new contributors, without false failures from
contract drift or environment issues unrelated to install behavior.

### In Scope

- Diagnose and fix the **make install smoke (slow)** CI failure on `dev`.
- Align local slow smoke (`make test-slow`) with the restored CI contract.
- Add or adjust regression coverage when the root cause is non-flake.
- Confirm whether pip-cache and Node deprecation annotations affect the
  failure or are incidental.

### Out of Scope

- Redesigning the full CI matrix or merging slow smoke into the fast job.
- Broad dependency lock refreshes unless required to restore install success.
- Product/application feature changes unrelated to install smoke.
- Creating Jira Debt tickets in this run (list follow-ups in
  `60-tech-debt.md` only).

## Functional Requirements

- FR1: The slow Makefile install smoke CI job must pass on `dev` when the
  install contract is satisfied.
- FR2: The slow smoke test must exercise `make install` in an isolated
  workspace with the real committed project manifest (not the minimal empty
  fixture used by fast Makefile tests).
- FR3: After install succeeds in that workspace, smoke must verify the
  installed environment is usable (import sanity check for a core dependency).
- FR4: Local `make test-slow` must remain the documented on-demand entry for
  the same slow marker suite CI runs.
- FR5: After root cause is classified, the slow smoke contract must continue
  to represent a realistic fresh install in an isolated workspace with the
  committed project manifest — including after packaging metadata changes
  (e.g. PYPOST-808 version unification).
- FR6: Fast CI and default `make test` must continue excluding
  `@pytest.mark.slow` tests.

## Non-Functional Requirements

- NFR1: Prefer the Makefile as the primary interface (`make test-slow`,
  `make install`).
- NFR2: Slow smoke may remain network-heavy; it stays in a separate CI job
  with pip caching (existing PYPOST-559 design).
- NFR3: Per-test timeouts per `do-testing.md` must be preserved for slow tests.
- NFR4: Isolated workspace tests must not modify the repository `.venv`.
- NFR5: Docs stay in English; line length ≤ 100 where practical.

## Constraints and Assumptions

- Root `Makefile` and `.github/workflows/test.yml` are the automation source
  of truth unless this task explicitly changes them.
- The slow smoke job already provisions Qt/EGL system libraries (PYPOST-923);
  collection failures from missing PySide6 runtime are out of scope unless
  regression is found.
- The triggering push is assumed unrelated to install behavior; the failure
  predates or persists independently of that docs-only change.
- Related prior work: PYPOST-559 (slow smoke job), PYPOST-806 (pyproject-based
  install), PYPOST-905 (stamp cache), PYPOST-923 (Qt/EGL parity),
  PYPOST-808 (version metadata unification).

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Slow install smoke job | Dedicated CI gate for isolated `make install` |
| Slow marker test suite | Pytest tests excluded from fast matrix |
| Isolated workspace | Temporary directory mimicking fresh clone install |
| Project manifest | Committed dependency/packaging definition used by install |
| Makefile install target | Contributor entry for editable install with extras |
| Fast test matrix | Primary CI feedback loop (excludes slow marker) |
| Maintainer / contributor | Relies on green CI and local slow smoke for install confidence |

## Q&A

| Q | A |
| --- | --- |
| Did the triggering push cause the failure? | No — docs-only; unrelated to install behavior. |
| Why do peer jobs pass? | Smoke uses isolated workspace; others use full checkout. |
| Are cache / Node warnings blocking? | Unknown until classified; must not block if incidental. |
| Relation to PYPOST-923? | 923 fixed smoke env parity; separate gap to classify. |
| Relation to PYPOST-808? | 808 changed packaging metadata; smoke must stay valid. |
