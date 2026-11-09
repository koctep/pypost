# PYPOST-1530: Keep hidden field selectors consistent

## Goals

Keep response masking configuration understandable and reliable by removing unsupported
per-selector activation state. Every saved selector must remain an active masking rule;
maintainers should not have to reason about a dormant feature that users cannot control.

## User Stories

- As a user, I can add, edit, remove, save, and reload response masking selectors with the
  same results as before.
- As a maintainer, I can understand which selector properties affect masking without
  encountering unused activation state.

## Definition of Done

- FR1: Selectors have no separate enabled or disabled state in the hidden field table.
- FR2: Every configured non-empty selector remains included when configuration is saved
  and restored; selector order and existing whitespace handling remain unchanged.
- FR3: Adding, editing, deleting, and the trailing blank entry retain their current behavior.
- FR4: Advisory syntax feedback and existing configuration change notifications remain intact.
- FR5: No per-selector activation controls or new saved configuration format are introduced.
- NFR1: The table retains its virtualized behavior and existing large-list responsiveness.
- NFR2: Masking coverage and protection of configured response fields do not regress.
- Documentation describes the resulting selector-only behavior and verification confirms
  the preserved user workflows.

## Task Description

Implementation language: Python.

The hidden response field table allows users to maintain an ordered list of masking
selectors. A selector identifies a response field or path and has advisory syntax feedback.
The saved masking configuration contains these selectors and applies them to response data.
An empty trailing entry supports adding another selector.

Earlier work retained an activation concept that is neither exposed to users nor saved.
This task resolves that maintenance debt by retaining only the delivered selector workflow.
The scope covers the hidden field table's unused activation concept and its documentation.
Selector deduplication, event-path coverage, performance-budget changes, and new masking
features belong to other issues.

Assumption: There is no current product requirement for temporarily disabling individual
selectors. The source ticket explicitly permits removing the dormant concept.

## Q&A

- Why is this needed? Unsupported activation state makes configuration behavior harder to
  maintain while providing no usable capability, as recorded in
  [the source debt analysis](../PYPOST-1386/60-tech-debt.md).
- Which policy is selected? Remove the dormant activation concept and preserve the existing
  selector-only user workflow.
- Is user review required here? This task is part of the authorized autonomous sprint run;
  an independent review provides the acceptance gate before the next step.
