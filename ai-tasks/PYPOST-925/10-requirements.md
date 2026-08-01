# PYPOST-925: Strengthen smoke Qt contract peer equality

## Goals

[PYPOST-924](https://pypost.atlassian.net/browse/PYPOST-924) consolidated the
Qt/EGL apt install for CI into a single shared composite action consumed by the
`test`, `make-install-smoke`, and `agent-e2e` jobs. The smoke Qt contract test
still treats a separately maintained hardcoded package list as the authoritative
expected set, while the composite action holds the real install definition.
Maintainers who add or remove a runtime library must edit both places and keep
them in sync manually.

**Business need:** Reduce CI maintenance cost and drift risk for Qt-dependent
test jobs by making the contract test enforce parity from one authoritative
definition—the shared Qt/EGL provisioner—so a package change requires a single
edit and any job that falls out of alignment fails CI immediately.

**Source:** [PYPOST-925](https://pypost.atlassian.net/browse/PYPOST-925);
follow-up [TD-2](https://pypost.atlassian.net/browse/PYPOST-923) from
`ai-tasks/PYPOST-923/60-tech-debt.md`, carried forward in
`ai-tasks/PYPOST-924/60-tech-debt.md`. Parent context:
[PYPOST-923](https://pypost.atlassian.net/browse/PYPOST-923),
[PYPOST-924](https://pypost.atlassian.net/browse/PYPOST-924).

## Programming Language

Python for pytest contract updates (`.cursor/lsr/do-python.md`,
`.cursor/lsr/do-testing.md`). Developer documentation in English Markdown
(`.cursor/lsr/do-markdown.md`) only if Step 8 needs a brief note about the
strengthened contract.

## User Stories

- As a **CI maintainer**, I want the Qt/EGL contract test to derive its expected
  package set from the shared provisioner definition alone, so updating headless
  PySide6 runtime libraries does not require maintaining a duplicate list in the
  test module.
- As a **contributor**, I want CI to fail when any Qt-using job drifts from the
  shared Qt/EGL package set, so smoke, matrix, and agent e2e failures reflect
  real test or install problems—not accidental job-to-job environment skew.
- As a **reviewer**, I want an automated check that proves all three Qt-using CI
  jobs remain aligned with the same provisioned runtime, so contract strengthening
  does not weaken the parity guarantee established by PYPOST-923 and PYPOST-924.

## Definition of Done

- [ ] The smoke Qt contract test no longer depends on a separately maintained
  hardcoded package frozenset as the authoritative expected set; the shared
  Qt/EGL provisioner definition is the single source of truth for which packages
  must be installed.
- [ ] The contract **fails** if the shared provisioner's package set changes
  without the test reflecting that change through the provisioner alone (no
  silent dual-edit requirement).
- [ ] The contract **fails** if any of the three Qt-using jobs—`test`,
  `make-install-smoke`, or `agent-e2e`—drifts from the shared Qt/EGL package
  set or stops using the shared provisioner.
- [ ] The installed package set remains the same as today (eight libraries:
  `libdbus-1-3`, `libegl1`, `libfontconfig1`, `libfreetype6`, `libglib2.0-0`,
  `libgl1`, `libxcb-cursor0`, `libxkbcommon0`) unless a deliberate, documented
  change is part of this task—which it is not.
- [ ] All contract tests in `tests/test_ci_make_install_smoke_qt_runtime.py`
  remain **green** on the current workflow and composite action.
- [ ] `make check` (project quality gate) remains green for the change set.
- [ ] No product feature behavior or end-user documentation is intentionally
  changed; scope is CI contract hygiene only.

## Task Description

### Problem

PYPOST-924 removed triple inline apt copy by introducing a shared composite
action, but the contract test still gates package parity against
`_PEER_QT_EGL_PACKAGES`, a hardcoded frozenset in the test module. The composite
`action.yml` and that frozenset must stay manually synchronized whenever the
runtime set changes. The contract also emphasizes smoke versus `agent-e2e` peer
checks rather than treating all three Qt-using jobs with equal weight.

### In Scope

- Strengthen the smoke Qt contract so the expected package set comes from the
  shared Qt/EGL provisioner definition (the composite action introduced by
  PYPOST-924), eliminating dual maintenance of package names.
- Ensure the contract detects drift for **all three** Qt-using jobs (`test`,
  `make-install-smoke`, `agent-e2e`), not only a subset of peer comparisons.
- Preserve existing contract intent: no inline apt duplication, composite usage,
  and full headless PySide6 runtime parity across jobs.
- Keep the current eight-package set unchanged unless blocked by consolidation
  fixes (default is parity with today's provisioner).

### Out of Scope

- Changing **which** packages are installed (unless required to complete contract
  strengthening; default is parity with the current eight-package set).
- Re-extracting or redesigning the shared composite action itself (owned by
  PYPOST-924; this task consumes it as the authoritative definition).
- Deferring or removing the PySide6 import-at-collection behavior in
  `tests/conftest.py` (PYPOST-926 / TD-3).
- Hardening workflow YAML parsing helpers or adopting a structured YAML parser
  (PYPOST-928 / TD-5).
- New CI jobs, lock/inventory gates, or smoke test behavior changes beyond
  contract enforcement.
- End-user `doc/user/` documentation.
- Creating follow-up Jira tickets in this step (Step 7 owns debt capture).

### Constraints and Assumptions

- The shared Qt/EGL provisioner at
  `.github/actions/install-qt-egl-runtime/action.yml` remains the maintained
  install definition for all three Qt-using jobs.
- Ubuntu `ubuntu-latest` runners and the current `apt-get --no-install-recommends`
  provisioning model are unchanged.
- All three jobs still require the same package set for shared conftest PySide6
  import at collection; contract strengthening must not regress that behavior.
- Autonomous sprint-task-runner execution: Step 1 artifacts are treated as
  pre-approved for this run (no interactive user gate).

### Main Entities (business domain)

| Entity | Role |
| --- | --- |
| Tests CI workflow | Primary merge-quality pipeline for pytest, smoke, and agent e2e |
| Qt/EGL runtime provisioner | Single shared definition installing headless PySide6 system libs |
| `test` job | Matrix pytest gate (Python 3.11 / 3.13) |
| `make-install-smoke` job | Slow Makefile install smoke gate |
| `agent-e2e` job | Agent environment pack gate via `make test-agent-e2e` |
| Smoke Qt contract test | Automated guard that all Qt-using jobs stay provisioned identically |

## Functional Requirements

1. **FR1 — Single authoritative expected set:** The contract test must treat
   the shared Qt/EGL provisioner definition as the sole source of truth for
   which packages constitute the required runtime set.
2. **FR2 — No duplicate package list in tests:** The contract must not require
   maintainers to update a separate hardcoded package list in the test module
   when the provisioner's package set changes.
3. **FR3 — Three-job coverage:** The contract must detect drift if any of
   `test`, `make-install-smoke`, or `agent-e2e` falls out of alignment with the
   shared provisioner or its package set.
4. **FR4 — Parity preservation:** After strengthening, CI jobs must still
   provide the same headless Qt runtime environment they had before this task
   (no missing libraries for shared fixtures).
5. **FR5 — Contract continuity:** Existing parity guarantees from PYPOST-923 and
   PYPOST-924 (composite usage, no inline apt duplication, full eight-package
   set) remain enforced—not weakened or removed without replacement checks.
6. **FR6 — No product change:** Application code under `pypost/` and user-facing
   behavior remain unchanged.

## Non-Functional Requirements

- **Maintainability:** A package set change requires editing the shared
  provisioner only; the contract test adapts automatically from that definition.
- **Signal quality:** CI failures after this change must clearly indicate which
  job or provisioner drifted, without increasing false positives from unrelated
  workflow edits.
- **Scope discipline:** Debt reduction only—no unrelated workflow or test refactors.
- **Reproducibility:** Local `make check` and existing Makefile smoke targets
  remain valid; this task adjusts contract enforcement, not local developer
  install requirements.

## Q&A

| Question | Answer |
| --- | --- |
| Why not leave dual maintenance if tests pass today? | Detects drift only after manual sync; TD-2 targets edit burden and missed updates. |
| Will the package list change? | Not in scope; eight-package parity unless blocked. |
| Derive from composite vs parse three job YAML blocks? | Prefer deriving from the shared provisioner (composite `action.yml`); triple YAML parsing is unnecessary now that PYPOST-924 consolidated install. |
| What about PYPOST-924's inline-libegl1 sentinel test? | In scope to preserve intent; Step 2 decides whether to keep, adapt, or fold into strengthened checks. |
| What about PYPOST-926 (lazy Qt import)? | Separate ticket; explicitly out of scope. |
| Interactive Step 1 approval? | Skipped — sprint-task-runner autonomous mode. |
