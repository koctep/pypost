# PYPOST-876: Narrow dump helper exception types

## Goals

When an agent e2e failure dump cannot complete (disk full, broken session,
serialization issue), triage still needs the **original test failure** as the
primary outcome. The dump path must stay best-effort for those expected
problems.

Today the dump helper treats almost any failure the same way: catch everything,
log a warning, return no dump. That also swallows surprising programming
mistakes inside the dump path, which makes real bugs harder to notice during
harness maintenance.

This debt comes from [PYPOST-860](https://pypost.atlassian.net/browse/PYPOST-860)
tech-debt (“Narrow dump helper exception types”) and remains after
[PYPOST-875](https://pypost.atlassian.net/browse/PYPOST-875) direct-session
auto-dump work.

## Programming Language

Python (pytest agent e2e harness dump helpers). Guides:
`.cursor/lsr/do-python.md`, `.cursor/lsr/do-testing.md`. Developer
documentation in English Markdown (`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **test author**, I want dump I/O and capture problems to stay
  best-effort so a failed dump never replaces my assert failure.
- As a **harness maintainer**, I want unexpected mistakes inside the dump
  path to surface clearly instead of looking like a normal “dump failed”
  warning, so regressions in the helper are easier to find.
- As a **future maintainer**, I want docs and automated checks that state
  which failure kinds are intentionally swallowed, so the contract does not
  silently widen again.

## Definition of Done

- Dump-helper paths that today catch every exception instead catch only the
  catalogued, expected failure kinds for capture / write / half-torn session
  reads.
- Expected dump failures still log a warning and leave the original test
  failure as the primary outcome (no dump directory returned).
- Unexpected exceptions in the dump path are no longer swallowed as normal
  dump failures.
- Docs describe the intentional catch set (or point to the helper contract).
- Automated checks lock best-effort for expected kinds and propagation for an
  unexpected kind (red then green in Steps 3–4).
- Unticketed follow-ups (if any) live only in this task’s `60-tech-debt.md`
  (no Jira ticket creation in this run).

## Task Description

**Problem:** The agent e2e failure dump helper uses a broad catch-all for
errors during artifact write. That preserves triage priority (original test
failure wins) but also hides unexpected helper bugs behind the same warning.

**Business need:** Keep reliable failure triage for expected dump problems,
while making unintended dump-path defects visible to maintainers.

### In Scope

- Research dump helpers in the agent e2e failure fixture module and related
  PYPOST-860 / PYPOST-875 behavior.
- Narrow intentional catch-all(s) in that dump helper to documented expected
  failure kinds.
- Keep best-effort semantics for those expected kinds.
- Align `doc/dev` failure-artifact guidance with the narrowed contract.
- Lock behavior with automated tests.

### Out of Scope

- Changing snapshot masking, artifact layout, or CI upload (PYPOST-874).
- Changing fixture vs direct-session dump wiring (PYPOST-875) beyond what
  narrowing the helper’s catch set requires.
- Narrowing broad catches in the agent session lifecycle dump-hook wrapper
  (noted as possible later follow-up in PYPOST-875).
- Creating Jira Debt tickets (unticketed items only in `60-tech-debt.md`).
- Commit or Jira status transitions (orchestrator owns those).

## Functional Requirements

- FR1: Expected dump failures (I/O, capture/runtime, type/value issues during
  write or snapshot) still produce a warning and no dump directory, without
  replacing the original test failure.
- FR2: An unexpected exception type raised inside the dump path must
  propagate (not be converted into a normal dump-failed warning).
- FR3: Existing successful dump behavior (snapshot + diagnostics written)
  remains intact.
- FR4: Docs state which failure kinds the helper intentionally swallows.
- FR5: Automated checks prove FR1 and FR2.

## Non-Functional Requirements

- NFR1: Do not duplicate snapshot or masking logic.
- NFR2: Success paths stay unchanged (no dump on pass).
- NFR3: Docs stay in English; line length ≤ 100 where practical.
- NFR4: Per-test timeouts remain mandatory on new/changed tests.

## Constraints and Assumptions

- Parent debt: PYPOST-860 `60-tech-debt.md` — “Narrow dump helper exception
  types” → this ticket; suggested kinds included OS/runtime/type/value class
  failures once catalogued.
- Related: PYPOST-875 keeps BLE001 on the helper until this ticket lands.
- Default artifact root and env override stay as in PYPOST-860 / 875.
- No commit / no Jira writes in this execution run.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Failure artifact dump | Masked UI snapshot + diagnostics on disk |
| Expected dump failure | Capture/I/O/serialization problem that must not mask the test |
| Unexpected dump failure | Programming mistake in the dump path that should surface |
| Contributor triage | Reads dumps after red local/CI agent e2e |
| Harness maintainer | Owns dump helper correctness |

## Q&A

| Q | A |
| --- | --- |
| Why not keep catching everything? | Parent debt: broad catch hides helper bugs behind triage warnings. |
| Why keep any swallow at all? | Dump must stay best-effort so assert failures remain primary. |
| Lifecycle hook BLE001 too? | Out of scope here; PYPOST-875 deferred that to a later follow-up. |
| Jira / commit in this run? | No — user directed; worklog block only for parent. |
