# PYPOST-865: Enable pytest --strict-markers (or document deferral)

## Goals

Maintainers and contributors need unknown pytest markers to fail loudly in
local runs and CI, so typos and unregistered suite marks cannot silently warn
and weaken marker-based selection. This debt closes the optional hygiene gap
left after registering `agent_e2e` in PYPOST-858: either turn on strict marker
enforcement project-wide, or document an explicit deferral with rationale.

## Programming Language

Python 3.11+ (pytest configuration and automated config guard).

## User Stories

- As a **maintainer**, I want unknown pytest markers to fail the suite (or a
  clear documented reason why that is deferred), so marker typos cannot hide
  in warning noise.
- As a **contributor**, I want local `make test` / pytest defaults to match CI
  regarding marker strictness, so I discover unregistered marks before push.
- As a **desktop user** (indirect), I want this debt work not to change product
  UX — only test-tooling hygiene for reliable suite selection.

## Definition of Done

- CI and local pytest either use `--strict-markers`, **or** developer docs
  explain why that mode is intentionally deferred.
- If enabled: registered custom markers continue to work; unknown custom
  markers fail collection/usage loudly.
- An automated check (or equivalent verified proof) locks the chosen policy.
- Steps 1–8 task artifacts exist for PYPOST-865.
- No intentional change to product UX.

## Task Description

**Problem:** PYPOST-858 registered `agent_e2e` but left `--strict-markers` off.
Registration stops warnings for that mark; typos of other marks still warn
only. Source: [PYPOST-865](https://pypost.atlassian.net/browse/PYPOST-865),
from [PYPOST-858](https://pypost.atlassian.net/browse/PYPOST-858)
`ai-tasks/PYPOST-858/60-tech-debt.md`.

**Business need:** Close low-priority testing hygiene debt so marker-based
selection and suite policy remain trustworthy.

### In Scope

- Choosing enable vs explicit deferral (with documented rationale if deferred).
- Pytest config / CI / docs updates needed for the chosen policy.
- Completing Steps 1–8 workflow artifacts.
- A focused automated guard or documented proof of the policy.

### Out of Scope

- Changing product features or GUI behavior.
- Sibling agent-e2e stories (HTTP determinism, failure artifacts, make/CI
  pack entry, harness table sync, optional caplog proofs).
- Introducing new suite markers beyond what already exists (unless required
  for a clean enable).

## Functional Requirements

- FR1: The project has an explicit policy: either `--strict-markers` is on for
  default local/CI pytest, or docs state deferral and why.
- FR2: When the policy is “enable”, an unregistered custom marker fails
  loudly under that configuration.
- FR3: When the policy is “enable”, existing registered custom markers
  (`timeout`, `slow`, `agent_e2e`) remain valid.
- FR4: Local defaults and CI inherit the same policy (no silent local-only
  strictness divergence).
- FR5: The chosen policy is locked by an automated check and/or clear
  developer documentation so future changes are intentional.

## Non-Functional Requirements

- NFR1: No meaningful slowdown of default `make test` collection.
- NFR2: Failure messages for unknown markers must be actionable for authors.
- NFR3: Documentation stays in English under `doc/dev/`.

## Constraints and Assumptions

- Pytest config lives under `[tool.pytest.ini_options]` in `pyproject.toml`.
- Acceptance allows either enable **or** documented deferral.
- Prefer enable when a one-time audit shows the suite is already clean.

## Main Entities

| Entity | Role |
| --- | --- |
| Pytest marker policy | Project rule for unknown vs registered marks |
| Registered custom markers | Named marks allowed under strict mode |
| Contributor / CI runner | Consumers of the policy via local make and CI |

## Q&A

| Q | A |
| --- | --- |
| Why not defer only? | Only registered marks used; enable is cheaper than documenting a gap. |
| Product impact? | None — test configuration only. |
