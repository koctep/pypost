# PYPOST-881: Optional shared finish-teardown helper for storage gateways

## Goals

Maintainers of the storage-gateway lifecycle need a clear, honest decision on
whether a shared finish-teardown helper is warranted. After the H3 finish-path
fix (PYPOST-829), both environment and collection gateways use the same
capture → deleteLater → short wait → WARNING → pending-restart pattern and the
same short wait bound. Extracting a private shared helper only pays off when a
third consumer appears or the two copies start to drift; otherwise the
extraction is premature consistency work.

The business outcome is either (a) a shared helper used where duplication is
real and risky, or (b) an explicit deferral with inventory evidence so this
Lowest priority debt can close without a forced refactor.

## Programming Language

Python 3.10+

## User Stories

- As a **maintainer**, I want shared private helpers only when duplication is
  real or drift is imminent, so the product does not grow unused abstractions
  for two stable call sites.
- As a **contributor**, I want clear guidance on whether finish teardown stays
  inline in each gateway, so I do not invent a third pattern or force an
  unnecessary move.
- As a **desktop user** (indirect), I want this debt work not to change product
  behavior—only how maintainers organize optional lifecycle hygiene.

## Definition of Done

- An inventory of finish-teardown consumers is recorded.
- Decision is explicit: **extract** if a third consumer appears or drift is
  already visible / clearly likely; **defer** (YAGNI) if still only the two
  gateways and sequences remain aligned.
- If defer: task artifacts document evidence and SAFE TO CLOSE rationale; no
  forced shared-helper extraction.
- If extract: shared private helper is used by consumers with equivalent
  lifecycle semantics (pending restart preserved).
- No intentional change to product desktop UX, encryption, or on-disk formats.
- Steps 1–8 task artifacts exist for PYPOST-881.

## Task Description

**Problem:** PYPOST-829 left the finish-teardown pattern inline in both storage
gateways and ticketed optional extraction
([PYPOST-881](https://pypost.atlassian.net/browse/PYPOST-881) /
`ai-tasks/PYPOST-829/60-tech-debt.md` TD-1) only if a third consumer appears or
drift becomes likely. Priority is Lowest; the ticket is explicitly
YAGNI-optional and not required for DoD of PYPOST-829.

**Business need:** Close or resolve this optional consistency debt without
forcing a refactor that adds no third consumer and no current drift. Prefer
documenting deferral with evidence over extracting “just in case.”

### In Scope

- Inventory of finish-teardown call sites / constants.
- Decision: extract vs defer.
- If defer: workflow artifacts + brief maintainer guidance.
- If extract: shared private helper and updated consumers.
- Completing Steps 1–8 workflow artifacts.

### Out of Scope

- Changing finish-path semantics (wait bound, pending restart order).
- Full-suite quality-gate campaigns (PYPOST-882).
- Shared `qapp` / suite affinity (PYPOST-830).
- User-facing product docs (`doc/user/`).
- Creating Jira Debt tickets from this task’s Step 7 (this run does not call
  Jira MCP).

## Functional Requirements

- Maintainers must be able to see how many modules implement the finish
  teardown pattern and whether they have drifted.
- Closing this task must not require inventing a third consumer.
- Product finish-path behavior must remain unchanged under the defer path.

## Non-functional Requirements

- **YAGNI:** Do not extract a shared helper while only two aligned consumers
  exist and drift is not visible.
- **Clarity:** Decision and inventory must be recorded in task artifacts.
- **Maintainability:** Guidance should allow extraction when a third consumer
  or real drift appears later.
- **Quality:** No intentional drop of H3 finish-path hygiene or stress canary
  coverage.

## Constraints and Assumptions

- Programming language: Python 3.10+.
- Source: [PYPOST-829](https://pypost.atlassian.net/browse/PYPOST-829) TD-1;
  artifact `ai-tasks/PYPOST-829/60-tech-debt.md`.
- Issue type: Debt; priority: Lowest; story points: 2.
- Two gateway modules are the known consumers; a third distinct consumer (or
  visible drift) is the extract trigger — not “two copies exist.”
- Approval for step artifacts is treated as granted under fully autonomous
  batch execution (no per-step user gates; no Jira calls; no git commit in this
  run).

## Main Entities and Interactions

| Entity | Attributes (business) | Role |
| --- | --- | --- |
| Maintainer / contributor | Needs clear helper placement | Owns gateway lifecycle |
| Finish teardown pattern | Capture, deleteLater, short wait, WARNING, pending restart | H3 hygiene |
| Environment storage gateway | Load/save + pending drain | One consumer |
| Collection storage gateway | Load + pending drain | One consumer |
| Product desktop surfaces | Unchanged under defer | Out of product-change scope |

Interaction overview:

1. Maintainer inventories finish-teardown consumers and compares sequences.
2. If a third consumer exists or drift is visible → extract shared helper.
3. If still only two aligned gateways → document deferral and close as YAGNI.
4. Task artifacts record the decision for future readers.

## Q&A

- Q: Why was this ticketed if extraction is optional?
  A: PYPOST-829 recorded Lowest follow-ups so optional polish is trackable
  without blocking the H3 fix.
- Q: Do two gateways already force extract?
  A: No. TD-1’s trigger is a **third** consumer or likely drift, not the
  existence of the original symmetric pair.
- Q: Does this change product desktop behavior under defer?
  A: No. Decision / documentation only.
- Q: Is forcing extraction acceptable to “complete” the ticket?
  A: No. Prefer honest YAGNI close with inventory evidence unless drift is
  already visible.
