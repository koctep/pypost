# PYPOST-1537: Live warning and advisory accept for hidden-field selectors

## Goals

A person editing hidden-field selectors must be warned while typing, and an invalid
draft must still be accepted when they finish editing.

Those selectors decide which response fields are masked.
[PYPOST-1387](https://pypost.atlassian.net/browse/PYPOST-1387) already promised a
warning during editing and an advisory finish that keeps the typed text.
Feedback on a row after the value is stored is already checked. The open edit
still lacks proof that invalid text warns, that valid text stays neutral, and
that finishing keeps an invalid draft. This task supplies that proof so a later
change cannot drop the live warning or discard a draft the person meant to keep.

The definition of done is one focused automated check of that live warning and of the
advisory accept.

**Implementation language:** Python

## User Stories

- As a **person editing hidden fields**, I want a warning while I am still typing an
  unsupported selector, so I can see the problem before I finish the edit.
- As a **person editing hidden fields**, I want neutral feedback while I am still
  typing a supported selector, so a correct draft is presented as healthy.
- As a **person finishing an edit**, I want the text I typed kept when it is
  unsupported, so the draft stays in the field for a later correction.
- As a **maintainer of masking configuration**, I want one automated check of the live
  warning and of the advisory accept, so that promise stays locked.

## Definition of Done

This task is done when one focused automated check shows all of the following:

1. While a hidden-field selector edit is still open and the text is the unsupported
   selector `$.secret`, the editor shows a warning.
2. While a hidden-field selector edit is still open and the text is the supported
   selector `token`, the editor shows neutral feedback, with the warning absent.
3. When the person finishes the edit on `$.secret`, the selector kept for that field
   is exactly `$.secret`.
4. The check observes the open edit. Feedback after the value is already stored stays
   outside this check.

## Task Description

### Problem

People configure response masking by typing field selectors. During an open edit, an
unsupported selector must carry a warning, and a supported selector must carry neutral
feedback. When the person finishes, the typed text is kept even if it is unsupported.
The finish is advisory: the warning informs the person and the draft remains.

The stored-row presentation of a selector that is already saved is already covered.
The gap is the open edit: warning versus neutral feedback while the person is still
typing, and keeping the typed text when an invalid draft is finished. The gap is
recorded in [PYPOST-1387 technical debt](ai-tasks/PYPOST-1387/60-tech-debt.md) and
tracked by [PYPOST-1537](https://pypost.atlassian.net/browse/PYPOST-1537).

### Scope

- One automated check of live warning versus neutral feedback while the person is
  still typing a hidden-field selector.
- The same check proves advisory accept: finishing the edit keeps the typed text when
  that text is unsupported.
- The unsupported text in the check is `$.secret`.
- The supported text in the check is `token`.
- A warning is the open-edit caution that the current text is not an accepted
  selector. Neutral feedback is that same open edit with the caution absent.

### Out of Scope

- Feedback on a row after the selector value is already stored.
- Sharing of the `header:` prefix across components
  ([PYPOST-1538](https://pypost.atlassian.net/browse/PYPOST-1538)).
- Rejecting a literal `..` draft
  ([PYPOST-1539](https://pypost.atlassian.net/browse/PYPOST-1539)).
- Specialized explanations for particular unsupported forms
  ([PYPOST-1540](https://pypost.atlassian.net/browse/PYPOST-1540)).
- Autocomplete, selector deduplication, and per-row enable controls.
- Changing which selector forms masking honors.
- Blocking save, or clearing a field, because a selector is unsupported.

### Functional Requirements

- **FR1: Live warning.** While the edit is open, `$.secret` produces a warning.
- **FR2: Live neutral feedback.** While the edit is open, `token` produces neutral
  feedback, with the warning absent.
- **FR3: Advisory accept.** Finishing the edit stores the typed characters as the
  selector. Finishing on `$.secret` keeps `$.secret`.
- **FR4: Single check.** FR1, FR2, and FR3 are proven together by one focused
  automated check of the open edit.

### Non-Functional Requirements

- **NFR1: Distinguishable feedback.** During an open edit, warning and neutral
  feedback are visibly different for `$.secret` and `token`.
- **NFR2: Draft fidelity.** Advisory accept stores the characters the person typed.
  The stored selector for a finish on `$.secret` is `$.secret`.

### Constraints and Assumptions

- The supported vocabulary stays the one already used for hidden-field masking. A
  simple key such as `token` is accepted. A `$`-prefixed path such as `$.secret` is
  unsupported.
- This task proves the open-edit promise from PYPOST-1387. It uses the warning the
  person already receives while typing. It does not add a second kind of caution or
  a phrase catalog for individual dialects.
- Empty rows and stored-row presentation stay outside this task.

## Entities

- **Field selector**: The text a person types to name a response field to mask.
- **Open edit**: The period while the person is still changing a selector and has
  not finished.
- **Warning**: The caution on an open edit when the current text is not an accepted
  selector.
- **Neutral feedback**: The open-edit presentation of an accepted selector, with the
  warning absent.
- **Advisory accept**: Finishing an edit stores the typed text, including when that
  text is unsupported.
- **Stored selector**: The selector text kept for the field after the edit finishes.

## Q&A

### Q1: Why is this needed?

**A**: A person editing hidden-field selectors must be warned while typing, and an
invalid draft must still be accepted when they finish. Stored-row feedback is already
checked. The open edit is not.

### Q2: When is the task done?

**A**: When one focused automated check proves the live warning for `$.secret`, the
neutral feedback for `token`, and the advisory accept that keeps `$.secret`.

### Q3: Why these two strings?

**A**: `token` is a simple supported key. `$.secret` is an unsupported `$`-prefixed
path. Both belong to the vocabulary PYPOST-1387 already defined. The check stays
clear of the gaps owned by PYPOST-1538, PYPOST-1539, and PYPOST-1540.

### Q4: What must the warning look like?

**A**: The check requires a warning on `$.secret` that is distinguishable from the
neutral feedback on `token`. Dialect-specific phrasing stays with PYPOST-1540.

### Q5: What is stored when the person finishes on an unsupported selector?

**A**: The stored selector is exactly `$.secret`. The accept is advisory.

### Q6: What programming language is used?

**A**: Python.
