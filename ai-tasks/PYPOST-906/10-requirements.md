# PYPOST-906: Optional lint depend on venv-test

## Goals

Contributors and agents use `make lint` as a primary static-analysis entry
point. After [PYPOST-872](https://pypost.atlassian.net/browse/PYPOST-872),
pytest-oriented Make targets ensure the **dev** optional extra via
`venv-test`, so flake8 and related tools appear without a separate install
step. `lint` was left marker-only (title scope), so a bare or incomplete
venv still fails `make lint` unless the contributor already ran
`make install` / `make venv-test`. Docs today tell people to install first.

[PYPOST-905](https://pypost.atlassian.net/browse/PYPOST-905) made
`venv-test` cheap when extras are already current (stamp/cache). That
removes the main historical reason to keep `lint` marker-only: pulling
dev tooling on every `make lint` is no longer an expensive reinstall tax.

This Debt closes that gap: **`make lint` must ensure test/dev tooling is
present**, so contributors get flake8 without a separate install step.
Documenting “why not” remains an acceptance fallback only if ensuring
tooling is rejected; the preferred outcome is ensuring presence now that
stamps make it cheap.

**Business need:** One less footgun for local and agent quality loops —
`make lint` (and thus `make check`) should not require a prior manual
extras install when the project already auto-installs `[dev]` for tests
and typecheck.

**Source:** [PYPOST-906](https://pypost.atlassian.net/browse/PYPOST-906)
(follow-up from PYPOST-872 / PYPOST-905 `60-tech-debt.md`). Parent
context: `ai-tasks/PYPOST-872/`, `ai-tasks/PYPOST-905/`.

## Programming Language

Makefile (root build interface) with Python pytest contract / smoke tests
(`.cursor/lsr/do-python.md`, `.cursor/lsr/do-testing.md`). Developer
documentation in English Markdown (`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **developer on a bare or incomplete venv**, I want `make lint` to
  bring in flake8 / `[dev]` tooling automatically, so I do not hit a
  confusing “command not found” / missing-tool failure after clone.
- As an **agent or CI-adjacent automation** that runs `make lint` or
  `make check`, I want lint to share the same “ensure tooling present”
  promise as typecheck / pytest targets, so loops do not need a separate
  install step before lint.
- As a **contributor with an already-ready venv**, I want that ensure step
  to stay cheap (no redundant install tax), so lint remains fast after
  PYPOST-905 stamps.
- As a **maintainer**, I want docs and Makefile contract tests to agree on
  whether `lint` ensures `[dev]` (preferred) or explicitly explain why not,
  so the acceptance contract cannot drift.

## Definition of Done

- `make lint` ensures test/dev tooling (`[dev]` / flake8 and peers) is
  present before running static analysis — **preferred acceptance** —
  **or** developer docs clearly state why `lint` remains install-first /
  marker-only (fallback only if ensure-tooling is not adopted).
- Preferred path aligns contributor experience with `typecheck` and
  pytest Make targets: lint no longer depends on a prior manual
  `install` / `venv-test` for a successful first run on a bare venv.
- Automated Makefile contract / smoke checks match the chosen acceptance
  (today’s tests assert `lint` does **not** pull `venv-test`; they must
  be updated if ensure-tooling ships).
- `doc/dev` wording that says `run` / `lint` stay marker-only is updated
  to match the chosen outcome (lint ensure vs documented exception).
- Unticketed follow-ups (if any) live only in this task’s
  `60-tech-debt.md`.

## Task Description

### Problem

`lint` depends only on the base venv marker. Flake8 lives in the **dev**
optional extra. Contributors who run `make lint` (or `make check`) before
`make install` / `make venv-test` fail even though pytest targets and
`typecheck` already auto-ensure `[dev]`. Docs document the asymmetry;
PYPOST-872 deferred changing `lint` as out of title scope. PYPOST-905
made auto-ensure cheap, so the deferred optional remains the open gap.

### Business need

Remove the install-first footgun for the lint quality entry point, now
that ensuring `[dev]` via the existing `venv-test` safety net is cheap
when already current. Prefer ensuring tooling present over merely
documenting the gap.

### In Scope

- Decide and deliver the Jira acceptance: `make lint` ensures test/dev
  tooling present (**preferred**), or docs state why not (fallback).
- Update Makefile contract / smoke expectations that currently lock
  “`lint` excludes `venv-test`”.
- Align `doc/dev` testing/setup wording about marker-only `lint`.
- Preserve cheap ensure behavior when `[dev]` is already current
  (PYPOST-905 stamp contract remains in force; this task does not undo
  idempotency).

### Out of Scope

- Changing `run` to depend on `venv-test` (runtime app path; not this
  ticket’s acceptance).
- Redesigning `make install`, stamp/caching mechanics, or extras packaging
  (owned by PYPOST-872 / PYPOST-905).
- Broader flake8 rule / baseline cleanup or CI workflow redesign.
- Product/application feature changes.
- Creating Jira Debt tickets in this run (list follow-ups in
  `60-tech-debt.md` only).

## Functional Requirements

- FR1: After this task, a contributor invoking `make lint` on a venv that
  lacks `[dev]` tooling either gets that tooling ensured before lint runs
  (**preferred**), or encounters documented install-first guidance that
  explicitly explains why auto-ensure was not applied (**fallback**).
- FR2: Preferred outcome: `make lint` shares the “ensure `[dev]` present”
  business promise already used by `typecheck` and pytest Make targets.
- FR3: When `[dev]` is already current, ensuring it for lint must not
  impose a redundant install tax (idempotent ensure from PYPOST-905).
- FR4: Automated checks encode the chosen lint ↔ `[dev]` ensure contract
  (replace today’s “lint must not depend on `venv-test`” assertions if
  preferred outcome ships).
- FR5: Developer documentation matches the chosen outcome and no longer
  contradicts Make behavior for `lint`.
- FR6: `make check` (which includes lint) inherits the same contributor
  experience as FR1 for the lint portion of the gate.

## Non-Functional Requirements

- NFR1: Prefer the Makefile as the primary interface (workspace makefile
  rules).
- NFR2: Preferred ensure path must remain acceptably fast when extras are
  already current (no return to pre-PYPOST-905 reinstall-on-every-visit
  cost for lint alone).
- NFR3: Bare-venv first `make lint` may take normal install time once;
  subsequent visits stay cheap.
- NFR4: Docs stay in English; line length ≤ 100 where practical.
- NFR5: Existing makefile smoke / dependency-chain tests that still apply
  remain green after contract updates.

## Constraints and Assumptions

- Root `Makefile` is the source of truth for targets.
- `venv-test` is the established business means of ensuring the **dev**
  extra (pytest, flake8, etc.); this task does not invent a new extras
  model.
- PYPOST-905 stamp/cache for `venv-test` is landed (or assumed available)
  so depending lint on that ensure path is cheap when current.
- Jira acceptance allows either ensure-tooling **or** docs-why-not;
  product preference for this run is ensure-tooling.
- `run` remaining marker-only is intentional and out of scope unless a
  later ticket says otherwise.
- Parent: PYPOST-872 deferred optional lint ensure; PYPOST-905 deferred
  it again as out of stamp scope → this ticket.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Lint entry (`lint`) | Static analysis quality entry point (flake8 on product code) |
| Dev extra ensure (`venv-test`) | Ensures pytest / flake8 / related `[dev]` tooling in `.venv` |
| Quality gate (`check`) | Convenience gate that includes lint + tests |
| Typecheck entry (`typecheck`) | Already ensures `[dev]`; peer pattern for lint |
| Install-once path (`install`) | Preferred combined setup after clone; still valid |
| Contributor / agent | Invokes Make quality targets without manual extras steps |
| Contract / smoke tests | Encode lint ↔ tooling-ensure promises |

## Q&A

| Q | A |
| --- | --- |
| Why change lint now? | PYPOST-905 made `venv-test` cheap when current; the cost argument for leaving lint marker-only no longer holds. |
| Why not only update docs? | Acceptance allows docs-why-not, but preferred business outcome is ensuring tooling so contributors do not need a separate install step. |
| Relation to PYPOST-872 / 905? | 872 deferred lint as title-scope; 905 stamped `venv-test` and left lint ensure to this ticket. |
| Does this change `run`? | No — out of scope; runtime path stays install-first / marker-only unless a later ticket. |
| Why not ask “why?” further? | Jira + parent debt already state the business reason: optional lint ensure of `[dev]`, preferred now that stamps make it cheap. |
