# PYPOST-864: Inventory drift guard (code vs seed doc)

## Goals

Maintainers and agent authors rely on a single documented seed inventory
(`doc/dev/agent_e2e_seed.md`) that mirrors the fixed seeded-workspace contents
in code. Today those two views can diverge silently when someone updates
constants or the inventory page without the other. This task adds an automated
guard so code↔doc skew is caught in CI before scenarios and docs disagree.

## Programming Language

Python 3.10+

## User Stories

- As a **maintainer**, I want an automated check that seed inventory constants
  in code still appear in the published seed inventory doc, so documentation
  does not silently drift from the fixture pack.
- As a **contributor**, I want that check to fail clearly when I change an id,
  display name, URL template, or env variable without updating the inventory
  page (or vice versa), so the fix path is obvious.
- As a **desktop user** (indirect), I want this debt work not to change seeding
  or product UX — only to lock the documented inventory against the code source
  of truth.

## Definition of Done

- An automated check asserts that the documented seed inventory stays aligned
  with the seed fixture inventory constants (ids, display names, env key/value,
  and request URL templates called out in the inventory table).
- The check declares an explicit pytest timeout marker (module, class, or
  function scope).
- The check is discoverable with other seed / agent-e2e related coverage and
  runnable without a live network or full GUI session when possible.
- Steps 1–8 task artifacts exist for PYPOST-864.
- No intentional change to successful seed write behavior or user-visible
  product UX beyond locking code↔doc sync (doc wording may be tightened to
  match constants if needed).

## Task Description

**Problem:** PYPOST-857 delivered builders + inventory constants and a mirrored
inventory page. Architecture deferred drift detection (Option C) until churn
hurt. Source: [PYPOST-864](https://pypost.atlassian.net/browse/PYPOST-864),
from [PYPOST-857](https://pypost.atlassian.net/browse/PYPOST-857)
`ai-tasks/PYPOST-857/60-tech-debt.md` — Inventory drift guard (code ↔ doc).

**Business need:** Close this low-priority testing/docs debt so seed inventory
docs remain trustworthy for humans and agents without requiring a committed
golden JSON dump.

### In Scope

- Adding a focused automated guard for code inventory constants vs
  `doc/dev/agent_e2e_seed.md`.
- Completing Steps 1–8 workflow artifacts.
- Minor inventory doc clarifications if the guard requires exact tokens that
  are already implied but not spelled out.

### Out of Scope

- Changing seed inventory contents for product reasons (new requests/envs).
- Committed golden JSON fixtures as a second source of truth (full Option C
  dump) unless architecture chooses that path.
- Caplog failure coverage (PYPOST-862), drive-then-snapshot (PYPOST-863),
  session packaging (PYPOST-858), HTTP determinism (PYPOST-859), failure
  artifacts (PYPOST-860), or make/CI pack entry (PYPOST-861).
- New product features or UI changes.

## Functional Requirements

- FR1: When a seed inventory constant (id, display name, env key/value, or
  documented URL template) is missing from the inventory doc, the automated
  check fails.
- FR2: When the inventory doc still lists the current fixture constants, the
  automated check passes.
- FR3: The check isolates against local files only — no live network and no
  full GUI session required.
- FR4: The check is discoverable near other seed coverage so maintainers can
  find it with agent e2e / seed tests.

## Non-Functional Requirements

- NFR1: Explicit pytest timeout marker on the new check (or inherited module
  marker).
- NFR2: Fast, deterministic unit style (read local markdown + import
  constants).
- NFR3: Failure messages name the missing token so maintainers know which
  constant/doc row to fix.
- NFR4: No secrets or live host dependency.

## Constraints and Assumptions

- Fixture constants in `pypost/fixtures/agent_e2e_seed.py` remain the code
  source of truth; the markdown page mirrors them for humans/agents.
- A lightweight presence/assert approach is preferred over generating a
  committed golden JSON unless architecture decides otherwise.
- Autonomous batch run: user approval gates are pre-approved for Steps 1–8;
  Jira updates and git commit are out of band for this execution.

## Main Entities (business)

| Entity | Role |
| --- | --- |
| Seed inventory (code) | Fixed ids/names/URLs/vars in the seed fixture pack |
| Seed inventory (doc) | Human/agent-facing mirror under `doc/dev/` |
| Drift | Mismatch between code constants and documented inventory |
| Drift guard | Automated check that fails when drift is present |

## Q&A

- Q: Why not commit golden JSON (full Option C)?
  A: Debt item allows a lightweight constants↔doc assert; golden JSON is
  heavier than needed for the current fixed four-row catalog.
- Q: Is a GUI session required?
  A: No. Business need is doc/code sync; file-level check is preferred.
- Q: Source of the debt item?
  A: [PYPOST-857 tech debt](../PYPOST-857/60-tech-debt.md) — Inventory drift
  guard (code ↔ doc) → [PYPOST-864](https://pypost.atlassian.net/browse/PYPOST-864).
