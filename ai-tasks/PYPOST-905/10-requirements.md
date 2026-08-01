# PYPOST-905: Stamp/cache venv-test and venv-otel

## Goals

Developers, CI, and agent loops use `make test` (and related pytest Make
targets) as the primary quality entry points. After
[PYPOST-872](https://pypost.atlassian.net/browse/PYPOST-872), those targets
correctly ensure the **dev** and **OpenTelemetry** optional extras are
present via `venv-test` and `venv-otel`. That safety net still re-runs
package installation on **every** Make visit, even when the virtual
environment already has those extras current.

This Debt closes that gap: prerequisite installs for `venv-test` and
`venv-otel` must be **idempotent** — when extras are already up to date,
Make must not perform redundant pip work. Contributors keep the
fresh-venv safety net; they stop paying a repeated install tax on every
test invocation.

**Business need:** Faster, quieter local and agent test loops without
weakening the “pytest targets install what they need” contract from
PYPOST-872. Prefer `make install` once after clone remains valid; the
change is about avoiding waste when the environment is already ready.

**Source:** [PYPOST-905](https://pypost.atlassian.net/browse/PYPOST-905)
(follow-up from PYPOST-872 `60-tech-debt.md` item 1). Parent context:
`ai-tasks/PYPOST-872/`.

## Programming Language

Makefile (root build interface) with Python pytest contract / smoke tests
(`.cursor/lsr/do-python.md`, `.cursor/lsr/do-testing.md`). Developer
documentation in English Markdown (`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **developer iterating locally**, I want repeated `make test` (and
  related pytest targets) to skip reinstalling extras that are already
  current, so feedback stays fast after the first successful setup.
- As an **agent or CI-adjacent automation** that invokes Make test targets
  often, I want prerequisite installs to be idempotent, so wall-clock time
  is spent on tests rather than redundant pip.
- As a **new contributor on a bare venv**, I still want `venv-test` /
  `venv-otel` (or equivalent prerequisites) to install missing extras
  before pytest runs, so the PYPOST-872 safety net remains intact.
- As a **maintainer**, I want “extras out of date vs already current”
  behavior covered by automated Makefile contract or smoke checks, so the
  idempotent promise does not regress.

## Definition of Done

- Idempotent Make behavior: when `venv-test` / `venv-otel` extras are
  already current, invoking those prerequisites (directly or via pytest
  Make targets) does **not** perform redundant pip installs.
- When extras are missing or no longer current, prerequisites still
  install (or refresh) them so pytest-running targets keep working on a
  bare or stale environment.
- Existing PYPOST-872 dependency contract remains: pytest Make targets
  that today depend on `venv-test` and/or `venv-otel` continue to ensure
  those extras before running tests.
- Automated tests encode the “skip when current / install when needed”
  acceptance at a Make-contract or smoke level appropriate to the project.
- Developer docs that currently warn about non-stamped reinstall cost
  (`doc/dev/testing.md` and related setup notes) are updated to match the
  new idempotent behavior.
- Unticketed follow-ups (if any) live only in this task’s
  `60-tech-debt.md`.

## Task Description

### Problem

`venv-test` and `venv-otel` are ordinary recipe-bearing Make targets.
Each time Make considers them as prerequisites of `test`, `test-slow`,
`test-cov`, `test-agent-e2e`, or `typecheck` (for `venv-test`), the
install recipes run again. After PYPOST-872 enabled `venv-test` on the
main pytest targets alongside the existing `venv-otel` dependency, every
test invocation can pay **two** editable installs even when nothing
changed.

Docs already note this cost and recommend `make install` once; that
mitigation does not remove the repeated work when contributors rely on
the safety-net prerequisites (common in agent loops and fresh shells).

### Business need

Preserve reliable auto-install of test/OTel tooling while making
prerequisite evaluation cheap when the environment is already satisfied.

### In Scope

- Idempotent `venv-test` and `venv-otel` prerequisite behavior (skip
  redundant pip when extras are already current; install/refresh when
  not).
- Contract / smoke test coverage for the idempotent acceptance.
- Align `doc/dev` testing/setup wording that describes non-stamped
  reinstall cost today.
- Preserve the PYPOST-872 pytest-target prerequisite safety net.

### Out of Scope

- Changing which Make targets depend on `venv-test` / `venv-otel`
  (e.g. adding `venv-test` to `lint` — that is PYPOST-906).
- Redesigning `make install` into a different extras model, or replacing
  editable extras with a new packaging scheme.
- Broader CI workflow redesign unrelated to local Make idempotency.
- Product/application feature changes.
- Creating Jira Debt tickets in this run (list follow-ups in
  `60-tech-debt.md` only).

## Functional Requirements

- FR1: When the virtual environment already has the **dev** extra current,
  visiting `venv-test` as a Make prerequisite must not re-run a redundant
  pip install of that extra.
- FR2: When the virtual environment already has the **otel** extra
  current, visiting `venv-otel` as a Make prerequisite must not re-run a
  redundant pip install of that extra.
- FR3: When the corresponding extra is missing or not current, `venv-test`
  / `venv-otel` must still bring it to a current state so subsequent
  pytest (or typecheck) invocations succeed.
- FR4: Pytest-oriented Make targets that depend on `venv-test` and/or
  `venv-otel` today retain that dependency relationship (safety net from
  PYPOST-872 unchanged in intent).
- FR5: Automated checks lock the idempotent “skip when current” vs
  “install when needed” acceptance.
- FR6: Developer documentation no longer describes permanent non-stamped
  reinstall-on-every-visit behavior for these targets once the change
  ships.

## Non-Functional Requirements

- NFR1: Prefer the Makefile as the primary interface (workspace makefile
  rules).
- NFR2: Repeated `make test` after a ready environment must feel
  materially cheaper than today’s dual editable pip on every visit
  (seconds of avoidable install work eliminated in the common case).
- NFR3: Fresh / bare venv path must not become harder than today; first
  install may still take normal pip time.
- NFR4: Docs stay in English; line length ≤ 100 where practical.
- NFR5: Existing makefile smoke / dependency-chain tests that still apply
  remain green.

## Constraints and Assumptions

- Root `Makefile` is the source of truth for targets.
- Base venv creation already uses a version-aware marker
  (`VENV_MARKER`); extras installs do not yet share that class of
  “already done” semantics.
- `make install` remains the preferred one-shot path after clone
  (`[dev,otel]` together); this task does not remove that recommendation.
- Parent: PYPOST-872 deferred stamp/caching as Low-priority tech debt →
  this ticket.
- “Current” means the environment reflects the project’s declared extras
  for `[dev]` / `[otel]` sufficiently that reinstall is unnecessary until
  those declarations or the environment change in a way that invalidates
  currency (exact invalidation rules belong in architecture, not here).

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Dev extra install (`venv-test`) | Ensures pytest and related dev tooling in `.venv` |
| OTel extra install (`venv-otel`) | Ensures OpenTelemetry optional stack in `.venv` |
| Extra currency | Business notion that an extra is already satisfied vs needs work |
| Pytest Make targets | Entry points that depend on the installs as a safety net |
| Install-once path (`install`) | Preferred combined setup after clone |
| Contract / smoke tests | Encode idempotent Make promises |

## Q&A

| Q | A |
| --- | --- |
| Why is this needed if `make install` exists? | Safety-net prerequisites still run on every pytest Make visit; install-once reduces but does not eliminate the tax for bare-venv and agent loops. |
| Why both `venv-test` and `venv-otel`? | PYPOST-872 left both as non-idempotent recipe targets; acceptance names both. |
| Does this change which targets pull extras? | No — dependency graph intent stays; only redundant work when already current is removed. |
| Relation to PYPOST-906? | Separate: whether `lint` should depend on `venv-test`. Out of scope here. |
| Why not ask “why?” further? | Jira + parent debt already state the business reason: avoid redundant pip when the venv is up to date after ENABLE of auto prerequisites. |
