# PYPOST-879: Optional shared worker timeout detail helper

## Goals

Maintainers of the automated storage/async suite need a clear, honest decision
on whether a shared worker-only timeout-detail helper is warranted. After
richer timeout diagnostics landed (PYPOST-828), a small local helper remained
in one collection-worker test module. Extracting it into the shared wait
helpers only pays off when more than one worker-only consumer needs the same
shape; otherwise the extraction is premature consistency work.

The business outcome is either (a) a shared helper used by multiple worker-only
consumers, or (b) an explicit deferral with inventory evidence so this Lowest
priority debt can close without a forced refactor.

## Programming Language

Python 3.10+

## User Stories

- As a **maintainer**, I want shared test helpers only when duplication is
  real, so the suite does not grow unused abstractions for a single call site.
- As a **contributor**, I want clear guidance on where to put worker-only
  timeout detail (local vs shared), so I do not invent a second pattern or
  force an unnecessary move.
- As a **desktop user** (indirect), I want this debt work not to change product
  behavior—only how maintainers organize optional test diagnostics.

## Definition of Done

- An inventory of worker-only timeout-detail consumers is recorded.
- Decision is explicit: **extract** if two or more worker-only consumers exist;
  **defer** (YAGNI) if still a single consumer module.
- If defer: task artifacts document evidence and SAFE TO CLOSE rationale; no
  forced shared-helper extraction.
- If extract: shared helper lives next to existing wait/timeout helpers and
  consumers use it with equivalent diagnostic intent.
- No intentional change to product desktop UX, encryption, or on-disk formats.
- Steps 1–8 task artifacts exist for PYPOST-879.

## Task Description

**Problem:** PYPOST-828 left a local `_worker_timeout_detail` in the collection
storage worker test module and ticketed optional extraction
([PYPOST-879](https://pypost.atlassian.net/browse/PYPOST-879) /
`ai-tasks/PYPOST-828/60-tech-debt.md` TD-2) only if a second worker-only
consumer appears. Priority is Lowest; the ticket is explicitly YAGNI-optional.

**Business need:** Close or resolve this optional consistency debt without
forcing a refactor that adds no second consumer. Prefer documenting deferral
with evidence over extracting “just in case.”

### In Scope

- Inventory of worker-only timeout-detail call sites / helpers.
- Decision: extract vs defer.
- If defer: workflow artifacts + brief maintainer guidance.
- If extract: move helper next to shared wait helpers and update consumers.
- Completing Steps 1–8 workflow artifacts.

### Out of Scope

- Product changes to workers, gateways, or UI.
- Reworking gateway timeout detail (already shared).
- Wiring `worker_operation` (covered by PYPOST-878).
- Full-suite quality-gate campaigns (PYPOST-880).

## Functional Requirements

- Maintainers must be able to see whether more than one worker-only consumer
  needs the same timeout-detail shape.
- Closing this task must not require inventing a second consumer.
- Product behavior must remain unchanged.

## Non-functional Requirements

- **YAGNI:** Do not extract a shared helper for a single consumer module.
- **Clarity:** Decision and inventory must be recorded in task artifacts.
- **Maintainability:** Guidance should prevent premature shared helpers and
  still allow extraction when a second consumer appears later.
- **Quality:** No intentional drop of existing timeout diagnostic coverage.

## Constraints and Assumptions

- Programming language: Python 3.10+.
- Source: [PYPOST-828](https://pypost.atlassian.net/browse/PYPOST-828) TD-2;
  artifact `ai-tasks/PYPOST-828/60-tech-debt.md`.
- Issue type: Debt; priority: Lowest; story points: 1.
- Two call sites inside one module count as **one** consumer, not two.
- Approval for step artifacts is treated as granted under fully autonomous
  batch execution (no per-step user gates; no Jira calls; no git commit in this
  run).

## Main Entities and Interactions

| Entity | Attributes (business) | Role |
| --- | --- | --- |
| Maintainer / contributor | Needs clear helper placement | Authors worker-only waits |
| Worker-only timeout detail | Optional running-state text on wait failure | Triage aid in CI output |
| Shared wait helpers | Existing gateway timeout detail | Shared only when reused |
| Collection worker checks | Current single consumer | May keep a local helper |
| Product desktop surfaces | Unchanged | Out of product-change scope |

Interaction overview:

1. Maintainer inventories worker-only timeout-detail consumers.
2. If two or more distinct consumers exist → extract shared helper.
3. If still one consumer → document deferral and close as YAGNI.
4. Task artifacts record the decision for future readers.

## Q&A

- Q: Why was this ticketed if extraction is optional?
  A: PYPOST-828 recorded Lowest follow-ups so optional polish is trackable
  without blocking the richer-diagnostics story.
- Q: Does “two call sites in one file” mean extract?
  A: No. The trigger is a **second consumer module/surface**, not a second
  wait in the same module.
- Q: Does this change product desktop behavior?
  A: No. Harness organization / documentation only.
- Q: Is forcing extraction acceptable to “complete” the ticket?
  A: No. Prefer honest YAGNI close with inventory evidence.
