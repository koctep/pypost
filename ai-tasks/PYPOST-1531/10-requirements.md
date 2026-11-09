# PYPOST-1531: Protect selector keyboard and menu workflows

## Goals

Keep response masking configuration reliable when users manage selectors through keyboard
shortcuts and the context menu. Existing checks exercise direct operations but do not protect
these user interaction paths against regressions.

## User Stories

- As a user, I can remove selected masking selectors with Delete or Backspace while retaining
  unselected selectors and a blank entry for adding another selector.
- As a user, I can add a selector or remove selected selectors from the context menu.
- As a user editing a selector, I can use editing keys without accidentally deleting its row.

## Definition of Done

- FR1: Automated verification covers both Delete and Backspace removing selected selector rows.
- FR2: Removal preserves unselected selector order and the trailing blank entry.
- FR3: Context-menu removal applies to the selected rows and is unavailable without a selection.
- FR4: Context-menu addition opens the blank entry for a new selector; the resulting entry can
  be saved with the existing selector list.
- FR5: Verification protects against row removal when a selector is being edited and against
  deleting the trailing blank entry.
- NFR1: Interaction checks are bounded and repeatable without manual input or external services.
- NFR2: Existing selector behavior and saved configuration remain unchanged.

## Task Description

Implementation language: Python.

A masking selector identifies a response field or path. Users manage an ordered list of these
selectors, may select several rows for removal, and use a blank entry to add another rule.
The context menu offers addition and removal; keyboard deletion must respect active editing.

This task adds regression coverage for existing interactions. It does not add new product
behavior, change selector matching or persistence, or alter deduplication and performance
policies, which belong to other issues. No production change is planned unless verification
reveals an in-scope defect requiring review of the task assumptions.

## Q&A

- Why is this needed? The source debt analysis identifies missing coverage of keyboard and
  context-menu interaction paths despite existing direct-operation checks:
  [PYPOST-1386 debt analysis](../PYPOST-1386/60-tech-debt.md).
- Which behavior is authoritative? The delivered selector workflow, including edit protection
  and retention of the blank entry, remains the expected user experience.
- How is acceptance reviewed? Independent review supplies the acceptance gate in this
  authorized autonomous sprint run.
