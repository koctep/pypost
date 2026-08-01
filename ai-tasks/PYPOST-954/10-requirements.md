# PYPOST-954: Harden UI-action MCP packaging doc locks

## Goals

[PYPOST-918](https://pypost.atlassian.net/browse/PYPOST-918) closed with
873-style substring doc locks in `tests/test_ui_actions_mcp_packaging_doc.py`.
Follow-up item 3 asked whether those locks should be **hardened** beyond raw
substrings if token churn becomes noisy.

Business value: keep UI-action MCP packaging doc guards **resilient without
false failures** — either by hardening when DRY/churn pressure is real, or by
explicitly recording strategy with criteria for future semantic hardening.

**Source:** [PYPOST-918/60-tech-debt.md](../PYPOST-918/60-tech-debt.md) follow-up 3.

## Programming Language

Python pytest contract helpers; English Markdown in `doc/dev/testing.md`.

## User Stories

- As a **maintainer**, I want an evidence-backed hardening decision on UI-action
  MCP packaging doc locks, not speculative semantic refactors.
- As a **contributor**, I want shared lock helpers and clear revisit triggers
  so doc edits fail with consistent messages.
- As a **reviewer**, I want the PYPOST-918 packaging contract suite to stay green
  after this debt closes.

## Definition of Done

- Churn on locked tokens / surfaces assessed honestly (git history).
- Explicit **HARDEN** (shared helper) or **KEEP** with rationale.
- If **HARDEN**: more resilient lock strategy without false failures.
- PYPOST-918 packaging contract tests green.
- Unticketed follow-ups listed in `60-tech-debt.md` only.

Acceptance (from Jira): **More resilient lock strategy; existing packaging doc
tests stay green.**

## Task Description

### Problem

Substring doc locks (PYPOST-873 / 918 / 922 pattern) are brittle if prose is
rephrased without locked tokens. PYPOST-918 follow-up 3 deferred hardening
unless churn is noisy. A second packaging doc-lock module (922) now exists —
938 trigger #3 applies.

### In Scope

- Inspect `tests/test_ui_actions_mcp_packaging_doc.py` and sibling 922 module.
- Measure token churn since PYPOST-918 landed.
- HARDEN via shared helper or KEEP with documented criteria.
- Dev docs for future lock authors.

### Out of Scope

- Semantic / schema-based doc asserts (unless future triggers fire).
- Runtime product MCP catalog guards (PYPOST-953).
- Live agent-UI MCP bridge (PYPOST-952).
- Git commit; Jira transitions (orchestrator).

## Functional Requirements

- FR1: Churn assessment with evidence (commits, test maintenance burden).
- FR2: HARDEN-or-KEEP decision tied to assessment.
- FR3: Developer docs state lock strategy and revisit triggers for UI-action MCP.
- FR4: Existing 918 packaging contract tests remain green.

## Non-Functional Requirements

- NFR1: Do not semantic-harden without demonstrated noisy churn.
- NFR2: Shared helper must stay fast (disk read only; `@pytest.mark.timeout(10)`).
- NFR3: Import contract prevents reintroducing local `_read` copies.

## Constraints and Assumptions

- Parent locks: PYPOST-918 doc + `test_ui_actions_mcp_packaging_doc.py`.
- Sibling: PYPOST-922 / 938 broader packaging locks.
- PYPOST-928 pattern: shared helper + import contract test.

## Main Entities

| Entity | Role |
| --- | --- |
| UI-action packaging lock module | `tests/test_ui_actions_mcp_packaging_doc.py` |
| Broader packaging lock module | `tests/test_agent_e2e_broader_packaging_doc.py` |
| Shared helper | `tests/helpers/packaging_doc_lock.py` |
| Locked docs | `ui_actions.md`, `mcp_integration.md`, `mcp_trust_model.md` |
| Strategy doc | `doc/dev/testing.md` § packaging doc locks |

## Q&A

| Q | A |
| --- | --- |
| Must we semantic-harden because this is a “harden” ticket? | No. Shared helper DRY satisfies acceptance when churn is low but two modules exist. |
| Change lock tokens? | No — preserve 918 tokens; refactor assert plumbing only. |
| Refactor 922 module too? | Yes — 938 trigger #3; single helper for both modules. |
