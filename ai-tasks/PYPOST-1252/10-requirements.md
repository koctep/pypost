# PYPOST-1252: Synchronize dialog-audit inventory to the current source

## Goals

The dialog-audit quality check fails because its frozen inventory and aggregate no longer match
the current source-authoritative dialog inventory. The stale record creates a false positive: a
valid current state appears to be an audit failure.

The business goal is to keep the audit expectation, consistency checks, and human-readable report
coherent with the current dialog inventory. Maintainers should be able to distinguish genuine
dialog-audit drift from an obsolete snapshot, while the audit remains a trustworthy record of the
current state.

The corrected scope is `settings_dialog.py`, which is currently 263 lines of code (LOC), while
the frozen expectation and report record say 260 LOC. The source-authoritative aggregate is 1790
LOC, while the frozen aggregate says 1787 LOC. `mcp_servers_dialog.py` is 486 LOC and already
matches its recorded value; it is not part of this correction.

For this document:

- **Source-authoritative inventory** means the dialog identity and size information observed from
  the current source when the audit is reviewed.
- **Corrected dialog** means `settings_dialog.py`, whose current source-authoritative count is
  263 LOC.
- **Coherent aggregate** means the displayed total agrees with the individual inventory entries
  represented in the audit, including the corrected 1790 LOC total.
- **Snapshot drift** means a difference between the source-authoritative inventory and the frozen
  expectation or report record.

## Programming Language

Python 3.11+ (the PyPost project language and runtime baseline).

## User Stories

- As a **PyPost maintainer**, I want the audit record to reflect the current settings dialog, so
  that I can tell whether a reported issue is real audit drift or an obsolete snapshot.
- As a **developer**, I want the dialog inventory, aggregate, consistency checks, and report to
  agree, so that a failure points to a genuine inconsistency.
- As a **reviewer**, I want the corrected report expectation to be clear and internally
  consistent, so that I can assess the audit without reconstructing stale historical values.
- As a **CI or release owner**, I want the existing dialog-audit quality gate to accept a coherent
  current record, so that stale expectations do not block reliable maintenance work.
- As an **application user**, I want this maintenance work to leave dialog behavior and visible
  interactions unchanged.

## Definition of Done

The task is complete when all of the following acceptance criteria are met:

- [ ] The audit expectation and corresponding report record identify `settings_dialog.py` with
  its current source-authoritative count of 263 LOC.
- [ ] The full dialog inventory and its aggregate reflect the source-authoritative total of
  1790 LOC.
- [ ] `mcp_servers_dialog.py` remains represented at its correct recorded value of 486 LOC and
  is not changed as part of this correction.
- [ ] The existing dialog-audit consistency checks and report record express the same current
  inventory and aggregate, without retaining contradictory frozen values of 260 or 1787 LOC.
- [ ] The existing dialog-audit quality gate accepts the synchronized expectation, checks, and
  report record.
- [ ] The result makes snapshot drift distinguishable from real audit drift: a valid current
  state must not fail solely because its frozen expectation is obsolete.
- [ ] No production dialog behavior, user interaction, or public application capability changes
  as a result of this task.
- [ ] The change remains limited to the dialog-audit artifacts, consistency checks, and report
  record; unrelated dialogs, production code, and unrelated audit records remain unchanged.

## Task Description

### Problem statement

The dialog audit contains a frozen inventory and LOC expectation that no longer matches the
current source-authoritative state for `settings_dialog.py`. The current file is 263 LOC, but the
frozen expectation and report record say 260 LOC. As a result, the aggregate is 1790 LOC in the
current inventory but 1787 LOC in the audit record. The pre-existing quality check reports a
failure even though the current state is valid; that outcome is a **false positive**.

The audit expectation, consistency checks, and report record must represent the current settings
dialog and aggregate consistently. An incomplete or incorrect audit that receives a passing
result would be a **false negative**, because it would conceal a real audit problem. The intended
outcome is a quality signal that accurately reflects the current inventory.

### In scope

- Correcting the stale inventory and LOC expectation for `settings_dialog.py` from 260 to the
  source-authoritative 263 LOC.
- Correcting the full dialog-audit aggregate from 1787 to the source-authoritative 1790 LOC.
- Updating the corresponding dialog-audit consistency checks and report statements that directly
  depend on the corrected settings count or aggregate.
- Preserving the recorded 486 LOC value for `mcp_servers_dialog.py`, which is already accurate.
- Keeping the audit quality gate a meaningful signal for the synchronized record.

### Out of scope

- Changing production dialog code, layout, validation, persistence, or lifecycle behavior.
- Redesigning audit policy, audit methodology, or the quality-gate policy.
- Revalidating or changing MCP role semantics.
- Updating unrelated dialogs, inventory entries, or audit records.
- Creating future drift automation or expanding the audit beyond the stale settings expectation,
  its aggregate, and directly affected audit records.
- Making changes outside the dialog-audit artifacts, consistency checks, and report record.

## Functional Requirements

1. **Current inventory representation:** The audit shall represent `settings_dialog.py` at its
   current source-authoritative count of 263 LOC.
2. **Correct aggregate:** The full dialog inventory shall represent the source-authoritative
   aggregate of 1790 LOC.
3. **Unaffected dialog preservation:** The audit shall continue to represent
   `mcp_servers_dialog.py` at 486 LOC, because that recorded value already matches the source.
4. **Coherent audit record:** The corresponding expectation, consistency checks, and report
   record shall use the same settings identity, 263 LOC count, and 1790 LOC aggregate wherever
   those facts are presented.
5. **Meaningful quality signal:** The existing quality gate shall accept the synchronized current
   expectation, checks, and report record. A failure caused only by an obsolete frozen value
   shall be recognized as a false positive, while an incomplete or incorrect audit that passes
   shall be recognized as a false negative.
6. **Behavioral preservation:** The task shall not change behavior exposed to application users;
   its result is limited to the truthfulness and coherence of the audit record and quality
   signal.

## User Scenarios

### Scenario 1: Maintainer reviews the corrected audit

1. A maintainer opens the dialog-audit report.
2. The report identifies `settings_dialog.py` and presents its current 263 LOC count.
3. The maintainer can see the source-authoritative 1790 LOC aggregate coherent with the full
   inventory.
4. The report continues to show `mcp_servers_dialog.py` at its accurate 486 LOC count.

### Scenario 2: Developer reviews the quality-gate result

1. A developer reviews the existing dialog-audit quality check.
2. The expectation, consistency checks, and report record describe the same current inventory.
3. The result is accepted because the record is coherent, rather than failing due to the stale
   260 LOC or 1787 LOC snapshot.

### Scenario 3: Reviewer classifies an audit result

1. A reviewer compares the current inventory with the audit expectation, consistency checks, and
   report record.
2. A valid current state failing only because its frozen expectation is obsolete is classified as
   a false positive.
3. An incomplete or incorrect audit accepted as valid is classified as a false negative.

### Scenario 4: Application user continues normal work

1. A user opens and uses dialogs as before.
2. Dialog presentation, configuration, validation, and lifecycle behavior remain unchanged.
3. The user sees no behavior change from this audit-consistency task.

## Main Entities and Interactions

| Entity | Business attributes | Interactions |
| --- | --- | --- |
| Corrected dialog | Identity, source-authoritative LOC, responsibility | Provides audit facts. |
| Dialog inventory | Current entries, aggregate from source | Represents current audit state. |
| Audit expectation | Dialog identity, size, aggregate | Defines facts for checks and report. |
| Consistency checks | Expected, observed, result | Compares audit record with inventory. |
| Audit report record | Scope, facts, aggregate, result | Communicates current state. |
| Quality gate | Accepted or failed consistency result | Signals whether the record is coherent. |
| Maintainer or reviewer | Audit and gate outcomes | Distinguishes snapshot drift from defects. |

The interaction boundary is limited to the stale settings expectation, its aggregate, and the
directly affected audit checks and report record. Dialog runtime behavior and MCP role semantics
are outside this boundary.

## Non-functional Requirements

- **Accuracy:** The settings identity, 263 LOC count, 1790 LOC aggregate, and directly affected
  audit statements must reflect the current source-authoritative inventory.
- **Consistency:** The audit expectation, consistency checks, report record, and quality-gate
  result must express the same current state.
- **Determinism:** An unchanged current state must produce a stable quality-gate interpretation.
- **Clarity:** A maintainer must be able to distinguish snapshot drift from a genuine audit
  inconsistency by reading the expectation, checks, report record, and result.
- **Compatibility:** Production dialog behavior, user interactions, supported capabilities, and
  MCP role semantics must remain unchanged.
- **Maintainability:** A future maintainer must understand why the settings expectation and
  aggregate were synchronized without reconstructing this incident.
- **Scope control:** The outcome must remain limited to PYPOST-1252's stale settings expectation,
  its aggregate, and directly affected audit records.

## Constraints and Assumptions

- Jira issue [PYPOST-1252](https://pypost.atlassian.net/browse/PYPOST-1252) is the governing scope;
  no unrelated cleanup or audit correction is implied.
- The current source inventory is authoritative for `settings_dialog.py`. The frozen values of
  260 LOC and 1787 LOC are historical evidence of snapshot drift, not authority over the current
  state.
- `mcp_servers_dialog.py` is not stale for this task: its source and recorded value are both
  486 LOC.
- The audit record must remain understandable to maintainers and reviewers as a current-state
  expectation, including the distinction between false positives and false negatives.
- This is a quality and maintenance task. It is not permission to alter application behavior,
  revalidate MCP role semantics, redesign audit policy, or introduce future drift automation.
- Step 1 records what must be true from a business and user-observable perspective; architecture,
  implementation choices, and detailed validation belong to later steps.
- The implementation change is limited to audit artifacts, consistency checks, and the report
  record; no production code is changed.

## Q&A

- **Why does a stale audit record matter if users see no UI change?** It creates a false positive
  quality signal, can block reliable maintenance work, and reduces trust in the audit used by
  maintainers and release owners.
- **What is the corrected dialog?** `settings_dialog.py`, whose current source-authoritative
  count is 263 LOC rather than the frozen 260 LOC.
- **What is the corrected aggregate?** The source-authoritative full inventory total is 1790 LOC
  rather than the frozen 1787 LOC.
- **What is the status of `mcp_servers_dialog.py`?** It is 486 LOC and matches its recorded
  value, so it is preserved and excluded from this correction.
- **What is a coherent aggregate?** A displayed total that agrees with all individual inventory
  entries represented in the audit.
- **What is snapshot drift?** A difference between the source-authoritative inventory and the
  frozen expectation or corresponding report record.
- **How are the two failure classes distinguished?** A valid current state failing only because
  its frozen expectation is obsolete is a false positive. An incomplete or incorrect audit
  passing as valid is a false negative.
- **What records are in scope?** The settings inventory expectation, its aggregate, the directly
  affected dialog-audit consistency checks, and the corresponding report record.
- **Are unrelated dialogs or audit records updated?** No. Unrelated dialogs, inventory entries,
  and audit records are explicitly excluded.
- **Are MCP role semantics revalidated or changed?** No. MCP role semantics are explicitly
  outside this task's scope.
- **Does this task require a production dialog change?** No. Dialog behavior, user interactions,
  supported capabilities, and lifecycle behavior remain unchanged.
- **What is the implementation language?** Python 3.11+, with task artifacts written in English
  Markdown.
