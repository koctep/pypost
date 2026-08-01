# PYPOST-936: Shared modal settle helper for product dialog proofs

## Goals

[PYPOST-919](https://pypost.atlassian.net/browse/PYPOST-919) delivered product dialog
settle under `agent_e2e` with a modal-safe `QTimer.singleShot` + `wait_until` +
fail-closed dismiss pattern. [PYPOST-934](https://pypost.atlassian.net/browse/PYPOST-934)
added a forced-timeout companion in the same module, duplicating the timer skeleton
and `UiWaitTimeoutError` rewrap block. PYPOST-919 TD-3 deferred helper extraction until
a second proof appeared — that trigger is now met.

Without a shared helper, each new product-dialog settle proof copies ~30 lines of
timer/rewrap/dismiss logic, increasing drift risk between happy-path and failure-path
diagnostics.

**Business why:** Keep dialog-settle proofs DRY and consistent under `agent_e2e` now
that two proofs exist, without changing production APIs.

Source: [PYPOST-919](https://pypost.atlassian.net/browse/PYPOST-919) `60-tech-debt.md`
TD-3 (Low). Parent debt item. Browse:
[PYPOST-936](https://pypost.atlassian.net/browse/PYPOST-936).

## Programming Language

Python (`.cursor/lsr/do-python.md`). Test-only refactor under `tests/helpers/`.
Task artifacts in English Markdown (`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **maintainer**, I want one shared modal-settle helper used by both dialog-settle
  proofs, so timer/rewrap/dismiss behavior stays consistent when editing either test.
- As an **AI agent / harness author**, I want a documented helper for product-dialog
  settle, so new dialog proofs compose the same modal-safe pattern without copy-paste.
- As a **CI runner**, I want the existing `agent_e2e` dialog-settle module to stay green
  under `make test-agent-e2e` after the refactor.

## Definition of Done

- Shared helper in `tests/helpers/` encapsulates `QTimer` + `wait_until` +
  fail-closed dismiss + timeout rewrap with `step` and modal scalars.
- Both proofs in `tests/test_agent_dialog_settle_e2e.py` use the helper.
- Convention test locks the shared-helper import (Step 3 red → Step 4 green).
- No production API changes unless justified (not expected).
- `make test-agent-e2e` green for the dialog-settle module.
- Unticketed follow-ups recorded only in `60-tech-debt.md`.

Acceptance (from Jira): **Shared helper used by at least two product-dialog settle
proofs; no production API change unless justified.**

## Task Description

**Problem:** Two dialog-settle proofs duplicate timer-before-click orchestration and
timeout rewrap logic inline.

**Business need:** Extract the shared pattern now that the second proof exists, matching
the precedent set by `tests/helpers/agent_e2e_send_settle.py` (PYPOST-948).

### In Scope

- `tests/helpers/agent_e2e_dialog_settle.py` (new).
- Refactor happy-path and timeout companion tests to use the helper.
- Convention test proving helper adoption (Step 3 red).
- Dev doc update for helper location and usage.

### Out of Scope

- Production dialog-settle or wait API changes.
- New product-dialog scenarios beyond the existing two proofs.
- `SETTINGS_DIALOG` widget identity ([PYPOST-935](https://pypost.atlassian.net/browse/PYPOST-935)).
- Migrating Settings from `exec()` to `open()`.
- Golden Send settle helper changes ([PYPOST-948](https://pypost.atlassian.net/browse/PYPOST-948)).
- Commit or Jira transitions (orchestrator).

## Functional Requirements

- FR1: Shared helper exists under `tests/helpers/` for modal-safe dialog settle.
- FR2: Happy-path proof (`test_agent_dialog_settle_after_settings_open`) uses the helper.
- FR3: Timeout companion proof uses the same helper.
- FR4: Helper preserves `step` + modal scalar diagnostics on timeout rewrap.
- FR5: Helper preserves fail-closed `reject()` in `finally`.
- FR6: Convention test fails before helper lands; passes after refactor.
- FR7: Full dialog-settle module green under `make test-agent-e2e`.

## Non-Functional Requirements

- **Test-only:** No imports from `tests/` into production code.
- **Boundedness:** Module `pytest.mark.timeout(60)` unchanged.
- **Minimalism:** Extract only what both proofs share; Settings predicate stays local.
- **English docs;** line length ≤ 100 where practical.

## Constraints and Assumptions

- Trigger: two proofs in `tests/test_agent_dialog_settle_e2e.py` (PYPOST-919 + 934).
- Reference helper: `tests/helpers/agent_e2e_send_settle.py`.
- Modal constraint: `QTimer.singleShot` before `ui_click` because `exec()` blocks.
- Sprint-task-runner autonomy: no approval gates in this run.

## Main Entities

| Entity | Role |
| --- | --- |
| `agent_e2e_dialog_settle` helper | Shared timer + wait + rewrap + dismiss |
| Happy-path proof | Settings open → dialog present → dismiss |
| Timeout companion | Forced near-zero budget → diagnostics asserts |
| Convention test | Structural lock on helper import/usage |
| `SETTLE_STEP` | Stable `diagnostics["step"]` contract |

## Q&A

- Q: Why extract now?
  A: PYPOST-919 TD-3 explicitly deferred until a second proof; PYPOST-934 added it.

- Q: Production changes?
  A: No — test-only refactor unless a shared production need emerges (not expected).

- Q: What stays test-local?
  A: Settings-specific predicate, timeout constants, and test assertions.
