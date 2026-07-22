# PYPOST-872: Make test targets depend on venv-test / install-first

## Goals

Developers and CI must be able to run the project’s primary test make
targets without hitting a confusing “pytest not installed” failure after a
fresh virtualenv. Today `make test` and `make test-agent-e2e` ensure the
OTel extra is present but do not ensure the **dev** tooling (pytest and
friends) that those recipes invoke. Contributors should either get those
tools installed automatically by the test targets, or have one clear
**install-first** contract so the expected setup is unambiguous.

This debt comes from [PYPOST-861](https://pypost.atlassian.net/browse/PYPOST-861)
tech-debt follow-up: close the gap between “targets that run pytest” and
“targets that install pytest.”

## Programming Language

Makefile (root build interface) with Python pytest contract tests
(`.cursor/lsr/do-python.md`, `.cursor/lsr/do-testing.md`). Developer
documentation in English Markdown (`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **new contributor**, I want `make test` / `make test-agent-e2e` to
  either install the needed test tools or tell me clearly to run
  `make install` first, so I am not blocked by a missing pytest module.
- As a **CI maintainer**, I want the local make contract to match how we
  already install before testing, so local and CI failure modes stay
  aligned.
- As a **developer running coverage**, I want the fast/e2e test targets to
  follow the same “dev tools available” expectation as `make test-cov`,
  which already pulls in the dev extra.

## Definition of Done

- An explicit decision is recorded: **ENABLE** makefile prerequisites
  (`venv-test` on pytest-running targets) **or** **document-only**
  install-first — with rationale.
- Acceptance behavior of the chosen approach is verified by automated
  tests and/or updated developer docs as appropriate.
- `make test` and `make test-agent-e2e` no longer leave contributors
  guessing whether pytest must be installed separately (either they
  install it via prerequisites, or docs state the contract in one place).
- Related makefile smoke / dependency-chain tests remain green and
  reflect the chosen contract.
- Unticketed follow-ups (if any) live only in this task’s
  `60-tech-debt.md` (no Jira ticket creation in this run).

## Task Description

**Problem:** `make test` and `make test-agent-e2e` depend on the venv
marker and `venv-otel`, but not on `venv-test`. Pytest comes from the
`[dev]` optional extra. CI runs `make install` (or equivalent
`pip install -e ".[dev,otel]"`) before tests, so the gap is hidden in CI
and bites mainly on clean local checkouts that skip install.

**Business need:** Reliable, self-explanatory test entry points for
humans and agents using the Makefile as the primary interface.

### In Scope

- Decide ENABLE vs document-only with written rationale.
- Update Makefile prerequisites and/or canonical developer docs
  accordingly.
- Update makefile contract tests to lock the chosen behavior.
- Align related mentions in `doc/dev` (testing / setup) with the
  decision.

### Out of Scope

- Stamp/caching redesign for `venv-test` / `venv-otel` (optional
  follow-up if ENABLE causes painful reinstall cost).
- Changing `lint` / `run` install behavior beyond documenting them if
  they remain install-first.
- Creating Jira Debt tickets (orchestrator Phase D lists unticketed
  items only; this run does not call Jira for follow-ups).
- Commit or status transitions (orchestrator owns those).

## Functional Requirements

- FR1: Record ENABLE vs document-only decision with rationale in
  architecture.
- FR2: After delivery, contributors can follow one documented path to a
  working `make test` / `make test-agent-e2e` on a clean checkout.
- FR3: Automated checks encode the chosen Makefile dependency contract
  for `test` and `test-agent-e2e`.
- FR4: Existing makefile smoke that still applies remains green.

## Non-Functional Requirements

- NFR1: Prefer the Makefile as the primary interface (workspace makefile
  rules).
- NFR2: Avoid surprising multi-minute regress on every `make test` when
  avoidable; if ENABLE is chosen, accept current non-stamped
  `venv-test`/`venv-otel` pip cost already present for otel, or note a
  follow-up for stamps.
- NFR3: Docs stay in English; line length ≤ 100 where practical.

## Constraints and Assumptions

- Root `Makefile` is the source of truth for targets.
- `make install` installs `[dev,otel]` in one shot; `venv-test` /
  `venv-otel` install extras separately.
- Parent debt: PYPOST-861 `60-tech-debt.md` item 1 → this ticket.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Test make targets | Entry points that run pytest |
| Dev tooling install | Ensures pytest (and related) exist in `.venv` |
| Install-first contract | Explicit “run install before test” expectation |
| Contract tests | Encode Makefile dependency promises |

## Q&A

| Q | A |
| --- | --- |
| Why not always document-only? | CI already installs first; the pain is local DX and asymmetry with `venv-otel` on `test`. Architecture must choose. |
| Why mention `test-cov`? | It already depends on `venv-test`; a consistency argument for ENABLE. |
| Jira / commit in this run? | No — user directed; worklog block only for parent. |
