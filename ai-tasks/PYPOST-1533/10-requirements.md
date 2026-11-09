# PYPOST-1533: Selector duplication policy for hidden response fields

## Goals

Users keep an ordered list of response fields that must stay confidential. They
edit that list in the request editor, save it with the request, and reload it
later. The rule is to keep repeats. Loading the list (`set_data`) and editing
it trim surrounding whitespace, drop blank selectors, preserve order, and do
not collapse duplicate selector text. The single unsaved trailing blank stays.
Saved lists are not uniquified. Letter case remains significant.

A repeated selector does not hide any extra response data. Naming the same field
twice hides that field once. The repeat is still part of the list the user
saved. The editor restores that list as saved.

PYPOST-1386 says uniquify only if the product wants it. No such want is
recorded. PYPOST-1377 requires the ordered saved list to be restored as saved.
The model already keeps repeats. Changing that would alter saved collections.

## Programming Language

- **Implementation language**: Python.

## User Stories

- As a user, I want repeated selectors kept. Loading the list (`set_data`) and
  editing it trim surrounding whitespace, drop blank selectors, preserve order,
  and do not collapse duplicate selector text. The single unsaved trailing
  blank stays. Saved lists are not uniquified. Letter case remains significant.
- As a user, I want the hidden-field list I save to come back in the same
  order, with the same entries I left in it, including repeated selector text.
- As a user, I want one blank row at the end of the list so I can type the next
  selector, and I want that blank row left unsaved.
- As a maintainer, I want this written rule: keep repeats, and do not uniquify
  saved lists. `set_data` and edits trim whitespace, drop blank selectors,
  preserve order, and do not collapse duplicate selector text. Case remains
  significant. The single unsaved trailing blank stays.

## Definition of Done

The policy is decided: keep repeats. This task is done when that rule holds
for loading, editing, and saving.

- FR1: `set_data` and edits trim whitespace, drop blank selectors, preserve
  order, and do not collapse duplicate selector text. Repeated selector text
  stays as separate entries.
- FR2: Saving returns every non-blank selector in that order, including
  repeats. Saved lists are not uniquified.
- FR3: The single unsaved trailing blank stays. It is the row for the next
  entry, and it is not saved. A repeat typed into that blank is added, and a
  new trailing blank remains.
- FR4: Letter case remains significant. `Token` and `token` are different
  selectors.
- FR5: An already saved list is restored as saved, repeats included. The editor
  does not rewrite a saved collection to drop later copies.
- NFR1: Adding, editing, and removing selectors stays responsive for ordinary
  lists and for the large lists the editor already supports.
- NFR2: Confidentiality holds. Each distinct selector still masks the same
  response fields. Keeping repeats leaves every distinct selector in place.
- NFR3: Syntax guidance, change notifications, and the rest of hidden-field
  editing stay as they are under the keep-repeats rule.

## Task Description

### Problem

The hidden-field editor stores an ordered list of selectors on each request.
Blank and whitespace-only entries are not kept. Every other entry is kept, even
when the same text appears more than once. The last row is always a single
blank entry used to type the next selector. That blank row is not saved.

This behavior comes from the original hidden-field editor (PYPOST-1377) and was
left unchanged when the table was rebuilt (PYPOST-1386). PYPOST-1386 says
uniquify only if the product wants it. No such want is recorded. PYPOST-1377
requires the ordered saved list to be restored as saved. The model already
keeps repeats. Changing that would alter saved collections.

Repeats do not add confidentiality. They are part of the saved document.
Unsaved-change detection compares that ordered list, repeats included.

### Scope

- In scope: keep repeats when a list is loaded (`set_data`) and when a row is
  edited or added. `set_data` and edits trim whitespace, drop blank selectors,
  preserve order, and do not collapse duplicate selector text. The single
  unsaved trailing blank stays. Saved lists are not uniquified. Case remains
  significant.
- Out of scope: selector syntax validation, checkbox or enable state, keyboard
  and context-menu coverage, large-list timing, and case-insensitive matching.
  `Token` and `token` stay different selectors.

### Required behavior

Keep repeats.

- Loading `token`, `password`, `token` shows three selector rows in that order,
  then one blank row. Saving returns `token`, `password`, `token`.
- Loading `token`, ` token `, and a blank entry shows two `token` rows and one
  trailing blank. Surrounding spaces are removed, and the blank entry is
  dropped. The two `token` rows stay. Duplicate selector text is not collapsed.
- Editing an existing row to text that another row already has leaves both
  rows.
- Typing a selector that already exists into the trailing blank adds that
  selector again and keeps a new blank row at the end.
- Clearing the trailing blank without typing does not add a row.
- The saved list omits the trailing blank and keeps repeats in entered order.
  Saved lists are not uniquified. Letter case remains significant.

### Policy

Keep repeats. `set_data` and edits trim whitespace, drop blank selectors,
preserve order, and do not collapse duplicate selector text. The single unsaved
trailing blank stays. Do not uniquify saved lists. Case remains significant.

PYPOST-1386 says uniquify only if the product wants it. No such want is
recorded. PYPOST-1377 requires the ordered saved list to be restored as saved.
The model already keeps repeats. Changing that would alter saved collections.

## Constraints and Assumptions

- Keep repeats. `set_data` and edits trim whitespace, drop blank selectors,
  preserve order, and do not collapse duplicate selector text. The single
  unsaved trailing blank stays. Do not uniquify saved lists. Case remains
  significant.
- PYPOST-1377 requires the ordered saved list to be restored as saved. That
  restoration includes repeats and order.
- PYPOST-1386 says uniquify only if the product wants it. No such want is
  recorded. The model already keeps repeats. Changing that would alter saved
  collections.
- The same selector means the same text after trim. Letter case remains
  significant. Field names that differ only by case stay different rules for
  masking.

## Main Entities

- **Selector**: Text that names a response field or path to keep confidential.
  Letter case is part of the name and remains significant. Surrounding
  whitespace is not part of the name. Duplicate selector text is kept.
- **Selector list**: The ordered selectors on one request. Repeats are kept.
  `set_data` and edits trim whitespace, drop blank selectors, preserve order,
  and do not collapse duplicate selector text. Saved lists are not uniquified.
  The single unsaved trailing blank stays outside the saved list.
- **Trailing blank entry**: The single empty row at the end of the editor. It
  is how the user adds the next selector. It is not saved. A repeat typed there
  is kept as another selector, and one new trailing blank remains.
- **Saved request configuration**: The selector list stored with the request.
  It is restored as saved, in order, including repeats. It is not uniquified.
  Unsaved-change detection compares that ordered list. Case remains
  significant.

## Q&A

- **Q: What is the decision?**
  - **A:** Keep repeats. `set_data` and edits trim whitespace, drop blank
    selectors, preserve order, and do not collapse duplicate selector text.
    The single unsaved trailing blank stays. Do not uniquify saved lists. Case
    remains significant.

- **Q: Why keep repeats?**
  - **A:** PYPOST-1386 says uniquify only if the product wants it. No such want
    is recorded. PYPOST-1377 requires the ordered saved list to be restored as
    saved. The model already keeps repeats. Changing that would alter saved
    collections.

- **Q: What happens to order, blanks, and case?**
  - **A:** Order is preserved, including repeats. `set_data` and edits trim
    whitespace and drop blank selectors. They do not collapse duplicate
    selector text. The single unsaved trailing blank stays. A repeat typed into
    that blank is added. Saved lists are not uniquified. `Token` and `token`
    stay different selectors because case remains significant.

- **Q: Where is this recorded?**
  - **A:** [PYPOST-1386 tech debt](../PYPOST-1386/60-tech-debt.md) says uniquify
    only if the product wants it. No such want is recorded. The original note
    is in [PYPOST-1377 tech debt](../PYPOST-1377/60-tech-debt.md). PYPOST-1377
    requires the ordered saved list to be restored as saved. The model already
    keeps repeats.
