# PYPOST-924: Shared Qt/EGL apt install for test, smoke, and agent-e2e CI jobs

## Goals

[PYPOST-923](https://pypost.atlassian.net/browse/PYPOST-923) restored CI health by
installing the same Qt/EGL system libraries on the main `test` matrix, the
`make-install-smoke` job, and the `agent-e2e` job. That fix required copying the
identical apt package list into three separate workflow steps. A contract test
(`tests/test_ci_make_install_smoke_qt_runtime.py`) guards parity today, but
maintainers must still edit three YAML blocks whenever the runtime set changes.

**Business need:** Reduce CI maintenance cost and drift risk for Qt-dependent test
jobs by defining the Qt/EGL runner provisioning step once and reusing it everywhere
those jobs need it—without weakening the smoke parity guarantee PYPOST-923
introduced.

**Source:** [PYPOST-924](https://pypost.atlassian.net/browse/PYPOST-924);
follow-up [TD-1](https://pypost.atlassian.net/browse/PYPOST-923) from
`ai-tasks/PYPOST-923/60-tech-debt.md`. Parent:
[PYPOST-923](https://pypost.atlassian.net/browse/PYPOST-923).

## Programming Language

GitHub Actions workflow YAML for the shared CI step and job wiring. Python for
pytest contract updates (`.cursor/lsr/do-python.md`, `.cursor/lsr/do-testing.md`).
Developer documentation in English Markdown (`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **CI maintainer**, I want the Qt/EGL apt package list defined in one place,
  so adding or removing a runtime library for PySide6 headless collection does not
  require hunting for duplicate blocks in the Tests workflow.
- As a **contributor**, I want all Qt-using CI jobs to stay provisioned identically
  after workflow edits, so smoke, matrix, and agent e2e failures reflect real test
  or install problems—not accidental job-to-job environment skew.
- As a **reviewer**, I want an automated check that still proves smoke-job Qt/EGL
  parity (or that all three jobs reference the same shared provisioner), so
  consolidation does not silently drop packages from one job.

## Definition of Done

- [ ] Exactly **one** shared definition exists for installing the Qt/EGL runtime
  packages required by PySide6 headless collection on Ubuntu CI runners.
- [ ] Jobs **`test`**, **`make-install-smoke`**, and **`agent-e2e`** in
  `.github/workflows/test.yml` all consume that shared definition (no remaining
  inline triple copy of the apt install block).
- [ ] The installed package set remains the same as today (eight libraries:
  `libdbus-1-3`, `libegl1`, `libfontconfig1`, `libfreetype6`, `libglib2.0-0`,
  `libgl1`, `libxcb-cursor0`, `libxkbcommon0`) unless a deliberate, documented
  change is part of this task—which it is not.
- [ ] The smoke Qt contract test in `tests/test_ci_make_install_smoke_qt_runtime.py`
  is **green**, either unchanged or updated to assert shared-step usage while
  preserving the parity intent.
- [ ] `make check` (project quality gate) remains green for the change set.
- [ ] No product feature behavior or end-user documentation is intentionally
  changed; scope is CI workflow hygiene only.

## Task Description

### Problem

The Tests workflow currently repeats the same “Install Qt / EGL runtime (PySide6
headless)” step—`apt-get update` plus an identical `--no-install-recommends`
package list—in three jobs. PYPOST-923 accepted this duplication to restore a
green baseline quickly. The contract test mitigates drift but does not remove the
maintenance burden: a package update requires synchronized edits in three places,
and the `test` job is not fully covered by the current peer-equality assertion
(TD-2 in PYPOST-923 is a separate follow-up).

### In Scope

- Consolidate the Qt/EGL apt install into a single reusable CI step consumed by
  `test`, `make-install-smoke`, and `agent-e2e`.
- Remove the three duplicated inline install blocks from `.github/workflows/test.yml`.
- Keep or adapt the existing smoke Qt contract test so CI still enforces parity
  (exact package set and/or shared-step reference).
- Preserve `QT_QPA_PLATFORM: offscreen` and existing job ordering relative to
  checkout and Python setup (only the install step itself is unified).

### Out of Scope

- Changing **which** packages are installed (unless required to fix consolidation;
  default is parity with the current eight-package set).
- Deferring or removing the PySide6 import-at-collection behavior in
  `tests/conftest.py` (PYPOST-926 / TD-3).
- Strengthening the contract test to derive expected packages from peer YAML or
  assert all three jobs independently (PYPOST-925 / TD-2).
- New CI jobs, lock/inventory gates, or smoke test behavior changes beyond
  environment provisioning.
- End-user `doc/user/` documentation.
- Creating follow-up Jira tickets in this step (Step 7 owns debt capture).

### Constraints and Assumptions

- Ubuntu `ubuntu-latest` runners remain the target; provisioning uses `apt-get`
  with `--no-install-recommends` as today.
- All three jobs already depend on the same package set for shared conftest
  PySide6 import at collection; consolidation must not regress that behavior.
- Existing pinned third-party Actions versions elsewhere in the workflow should
  be followed when introducing any new local action reference.
- Autonomous sprint-task-runner execution: Step 1 artifacts are treated as
  pre-approved for this run (no interactive user gate).

### Main Entities (business domain)

| Entity | Role |
| --- | --- |
| Tests CI workflow | Primary merge-quality pipeline for pytest, smoke, and agent e2e |
| Qt/EGL runtime provisioner | Single shared step installing headless PySide6 system libs |
| `test` job | Matrix pytest gate (Python 3.11 / 3.13) |
| `make-install-smoke` job | Slow Makefile install smoke gate |
| `agent-e2e` job | Agent environment pack gate via `make test-agent-e2e` |
| Smoke Qt contract test | Automated guard that smoke (and peers) stay Qt/EGL-ready |

## Functional Requirements

1. **FR1 — Single source of truth:** The Qt/EGL apt install command and package
   list must exist in one maintained definition referenced by all three jobs.
2. **FR2 — Job coverage:** `test`, `make-install-smoke`, and `agent-e2e` must
   each invoke that shared definition before Python setup steps that can trigger
   PySide6 import during test collection.
3. **FR3 — Parity preservation:** After consolidation, CI jobs must still provide
   the same headless Qt runtime environment they had before PYPOST-924 (no missing
   libraries for shared fixtures).
4. **FR4 — Contract continuity:** An automated test must continue to verify the
   smoke/install parity intent—either by checking package equality as today or by
   asserting all jobs use the shared provisioner without dropping packages.
5. **FR5 — No product change:** Application code under `pypost/` and user-facing
   behavior remain unchanged.

## Non-Functional Requirements

- **Maintainability:** Future Qt/EGL package changes require editing one shared
  definition, not three workflow copies.
- **Signal quality:** CI failures after this change must not increase false
  positives from environment skew between the three jobs.
- **Scope discipline:** Debt reduction only—no unrelated workflow refactors.
- **Reproducibility:** Local `make check` and existing Makefile smoke targets
  remain valid; this task adjusts CI wiring, not local developer install docs
  (Step 8 may lightly update dev docs if the shared step path should be named).

## Q&A

| Question | Answer |
| --- | --- |
| Why not leave triple copy if contract test passes? | Detects drift, not edit burden; TD-1. |
| Will the package list change? | Not in scope; eight-package parity unless blocked. |
| Composite vs reusable workflow — who decides? | Step 1: one definition; Step 2: mechanism. |
| What about PYPOST-925 (stronger contract test)? | Separate ticket; shared usage OK; keep parity. |
| Interactive Step 1 approval? | Skipped — sprint-task-runner autonomous mode. |
