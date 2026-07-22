# PYPOST-866: Keep agent_e2e.md harness table synced with markers

## Goals

Maintainers and agent authors use the harness module table in
`doc/dev/agent_e2e.md` to know which test modules the agent UI e2e suite
covers. Default make selection is by the `agent_e2e` marker, so the table can
drift when new modules are marked without updating the umbrella doc. This debt
keeps that table aligned with marked modules and records how maintainers keep
it aligned going forward.

## Programming Language

Python 3.10+ (any automated sync guard). Markdown for developer docs under
`doc/dev/`.

## User Stories

- As a **maintainer**, I want the documented harness module table to match the
  modules marked `agent_e2e`, so the umbrella doc stays a trustworthy map of
  what the suite includes.
- As a **contributor**, I want a clear maintenance process when I add or remove
  an `agent_e2e` module, so I know to update the table (or rely on an enforced
  sync) instead of leaving docs stale.
- As a **desktop user** (indirect), I want this debt work not to change product
  UX — only documentation accuracy and maintainability for the agent e2e suite.

## Definition of Done

- The harness module table in `doc/dev/agent_e2e.md` matches the set of modules
  marked `@pytest.mark.agent_e2e`.
- Developer-facing docs note the maintenance process for keeping that table in
  sync when marked modules change.
- Steps 1–8 task artifacts exist for PYPOST-866.
- No intentional change to product UX.

## Task Description

**Problem:** Default make selection is `-m agent_e2e`; the documented module
table can lag when authors mark new modules without updating
`doc/dev/agent_e2e.md`. Source:
[PYPOST-866](https://pypost.atlassian.net/browse/PYPOST-866), from
[PYPOST-858](https://pypost.atlassian.net/browse/PYPOST-858)
`ai-tasks/PYPOST-858/60-tech-debt.md` — Keep `agent_e2e.md` harness table
synced with marked modules.

**Business need:** Close this low-priority docs/testing hygiene debt so the
umbrella agent e2e entry stays accurate for humans and agents, and so future
module adds do not silently desync docs from marker selection.

### In Scope

- Aligning the harness module table with modules that carry the `agent_e2e`
  mark.
- Recording a maintenance process so future mark/table changes stay intentional.
- Completing Steps 1–8 workflow artifacts.
- Any focused check or process note needed to keep table and marks aligned.

### Out of Scope

- Changing product features or GUI behavior.
- Sibling agent-e2e hygiene (strict markers, optional packaging caplog, seed
  inventory contents, HTTP stubs, failure artifacts, make/CI pack entry).
- Redesigning the agent e2e suite layout or renaming the `agent_e2e` marker.

## Functional Requirements

- FR1: The harness module table in `doc/dev/agent_e2e.md` lists the same
  modules that are marked `agent_e2e` (no missing marked modules; no stale
  rows for unmarked modules that are no longer in the suite).
- FR2: Each table row remains useful for readers (module identity plus a short
  coverage note consistent with existing table style).
- FR3: Developer docs describe how maintainers keep the table synced when
  modules gain or lose the `agent_e2e` mark.
- FR4: After this work, drift between marked modules and the documented table
  is either prevented by process/enforcement or quickly detectable.

## Non-Functional Requirements

- NFR1: No meaningful slowdown of default `make test` / `make test-agent-e2e`.
- NFR2: If an automated check is used, failure messages must name the mismatch
  clearly enough for maintainers to fix the table or the mark.
- NFR3: Documentation stays in English under `doc/dev/`.
- NFR4: No change to successful product behavior or user-visible UX.

## Constraints and Assumptions

- The registered `agent_e2e` marker and `make test-agent-e2e` selection from
  PYPOST-858 remain the suite entry; this task does not redefine selection.
- The umbrella page `doc/dev/agent_e2e.md` remains the human/agent-facing
  harness module list.
- Acceptance requires both table↔mark alignment and a noted maintenance
  process (checklist, doc note, and/or automated guard — chosen in architecture).
- Autonomous Step 1 run: user approval gate for this step is waived per task
  instructions; later steps follow the usual workflow.

## Main Entities

| Entity | Role |
| --- | --- |
| Agent e2e marker | Suite label selecting harness modules for make/CI |
| Harness module | Test module that participates in agent UI e2e |
| Harness module table | Documented list of those modules on the umbrella page |
| Drift | Mismatch between marked modules and the documented table |
| Maintenance process | How authors keep marks and the table aligned |

## Q&A

| Q | A |
| --- | --- |
| Why sync the table at all? | Make selects by marker; the table is how authors discover coverage. Drift misleads. |
| Product impact? | None — docs / test-hygiene only. |
| Source of the debt item? | [PYPOST-858 tech debt](../PYPOST-858/60-tech-debt.md) → [PYPOST-866](https://pypost.atlassian.net/browse/PYPOST-866). |
| Must architecture pick a test vs checklist? | Either (or both) is fine if acceptance is met; choice is Step 2. |
