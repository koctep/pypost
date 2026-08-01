# PYPOST-938: Harden agent-e2e broader packaging doc locks

## Goals

[PYPOST-922](https://pypost.atlassian.net/browse/PYPOST-922) closed broader
agent e2e packaging discoverability with **873-style substring / token doc
locks** in `tests/test_agent_e2e_broader_packaging_doc.py` and Makefile
contract tests. Follow-up 3 asked whether those locks should be **hardened**
beyond raw substrings if token churn becomes noisy.

Business value: keep packaging doc guards **resilient without false failures**
— either by hardening when churn is real, or by explicitly recording **KEEP
CURRENT STRATEGY** with criteria for a future hardening story so maintainers
do not over-engineer stable locks.

**Source:** [PYPOST-922/60-tech-debt.md](../PYPOST-922/60-tech-debt.md) follow-up 3.

## Programming Language

Python pytest contract guards (assessment + optional hardening), English
Markdown in `doc/dev/` for the lock strategy decision.

## User Stories

- As a **maintainer**, I want an evidence-backed decision on whether broader
  packaging doc locks need hardening, not speculative refactors.
- As a **contributor**, I want clear criteria for when to revisit lock
  strategy so doc edits do not surprise me with brittle failures.
- As a **reviewer**, I want the PYPOST-922 contract suite to stay green
  after this debt closes.

## Definition of Done

- Churn on locked tokens / surfaces assessed honestly (git history, false
  failure signals).
- Explicit **HARDEN** or **KEEP CURRENT STRATEGY** with rationale.
- If **KEEP**: document when-to-harden triggers; locks unchanged unless churn
  already noisy.
- If **HARDEN**: more resilient lock strategy without false failures.
- PYPOST-922 packaging contract tests green.
- Unticketed follow-ups listed in `60-tech-debt.md` only.

## Task Description

### Problem

Substring doc locks (PYPOST-873 / 922 pattern) are brittle if prose is
rephrased without locked tokens. PYPOST-922 follow-up 3 deferred hardening
unless churn is noisy.

### In Scope

- Inspect `tests/test_agent_e2e_broader_packaging_doc.py` and sibling 922
  Makefile locks.
- Measure token churn since 922 landed.
- HARDEN or KEEP with documented criteria.
- Dev docs for future lock authors.

### Out of Scope

- Hardening unrelated packaging locks (e.g. `test_ui_actions_mcp_packaging_doc.py`
  — separate PYPOST-954).
- CI topology or runtime packaging selection changes.
- Git commit; Jira ticket creation in this run.

## Functional Requirements

- FR1: Churn assessment with evidence (commits, test maintenance burden).
- FR2: HARDEN-or-KEEP decision tied to assessment.
- FR3: Developer docs state lock strategy and revisit triggers.
- FR4: Existing 922 contract tests remain green.

## Non-Functional Requirements

- NFR1: Do not harden without demonstrated noisy churn (avoid over-engineering).
- NFR2: KEEP decision must still satisfy “more resilient strategy” via explicit
  criteria documentation (not silent deferral).

## Constraints and Assumptions

- Parent locks: PYPOST-922 doc + Makefile contract tests.
- Project practice: 873-style token guards for discoverability debt.
- PYPOST-928 hardened **CI workflow YAML job slicing**, not Markdown doc locks.
- PYPOST-937 shared **Makefile parse helpers**, not doc-token schema.

## Main Entities

| Entity | Role |
| --- | --- |
| Doc-token lock module | `tests/test_agent_e2e_broader_packaging_doc.py` |
| Makefile locks | `TestAgentE2eTargetRecipe`, help cross-check |
| Locked docs | `agent_e2e.md`, `agent_golden_e2e.md`, `testing.md` |
| Lock strategy doc | `doc/dev/testing.md` § packaging doc locks |

## Q&A

| Q | A |
| --- | --- |
| Must we harden because this is a “harden” ticket? | No. Acceptance allows KEEP when churn is low, with explicit future criteria. |
| What counts as noisy churn? | See architecture churn table and testing.md revisit triggers. |
| Change lock tokens on KEEP? | No — document only unless assessment shows HARDEN is required. |
