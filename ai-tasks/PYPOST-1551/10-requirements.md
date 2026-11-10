# PYPOST-1551: Forget reveal choices for fields that have left

## Goals

A person inspecting a masked response can reveal one sensitive value and
leave the others hidden. That choice belongs to a field that is among
the masked fields of the response on screen.

The person can keep the same view for a long session while the masked
fields of the current response change. After those fields are applied, a
reveal choice for a field that is no longer among them is forgotten. The
view does not retain a choice for a field that has left.

A reveal choice for a field that is still present stays. That includes an
indent refresh of the same response. The field the person left revealed
stays visible. The field the person left hidden stays hidden.

Clearing the body still forgets every choice. A different response still
starts masked.

Which fields start masked stays as it is. Hover stays as it is. Pointer
lookup stays as it is.

[PYPOST-1549](https://pypost.atlassian.net/browse/PYPOST-1549) and
[PYPOST-1550](https://pypost.atlassian.net/browse/PYPOST-1550) stay as
already promised. This ticket does not expand into those tests.

The parent called this outcome nice-to-have. It was not required for the
parent definition of done. The ticket is in this sprint, so the outcome
is now in scope here.

This item is follow-up debt from
[PYPOST-1392](https://pypost.atlassian.net/browse/PYPOST-1392),
recorded there as TD-3. It is Debt, Low, 2 story points, labeled
tech-debt.

**Implementation language:** Python

## User Stories

- As a **person keeping one response view open for a long session**, I
  want a reveal choice for a field that is no longer among the current
  masked fields to be forgotten once those fields are applied, so the
  view does not retain a choice for a field that has left.
- As a **person whose field is still among those masked fields**, I want
  that reveal choice to stay, including across an indent refresh of the
  same response, so the inspection I kept open is still open.
- As a **security-conscious user**, I want clearing the body to still
  forget every choice, and I want a different response to still start
  masked.
- As a **product maintainer**, I want this leftover-choice outcome in
  scope for this ticket. PYPOST-1549 and PYPOST-1550 stay as already
  promised, and this ticket does not expand into those tests.

## Definition of Done

This task is done when all of the following are true:

1. After the masked fields of the current response are applied, a reveal
   choice for a field that is no longer among those fields is forgotten.
2. A reveal choice for a field that is still present stays, including
   across an indent refresh of the same response.
3. Clearing the body still forgets every choice. A different response
   still starts masked.
4. Which fields start masked stays the same. Hover stays as it is.
   Pointer lookup stays as it is.
5. PYPOST-1549 and PYPOST-1550 stay as already promised. This ticket
   does not expand into those tests.
6. Automated checks demonstrate the forgotten leftover choice and the
   choice that stays for a field still present. The checks pass.

## Task Description

### Problem

Interactive masking hides sensitive values until the person reveals
them. Each reveal choice belongs to a field among the masked fields of
the response on screen.

The person can keep the same view while the set of masked fields
changes. A choice can remain for a field that is no longer among the
fields just applied. A long session on that view then retains a choice
for a field that has left.

After the masked fields of the current response are applied, that
leftover choice is forgotten. A choice for a field that is still present
stays, including across an indent refresh of the same response.

The parent treated forgetting the leftover choice as nice-to-have, and
did not require it for the parent definition of done. This ticket is in
the sprint, so that outcome is in scope here.

### User Scenario

The view has been open through a long session. The person revealed one
field and left another hidden. The masked fields of the current response
are applied again. The revealed field is no longer among them. That
reveal choice is forgotten. The field they left hidden is still among
the masked fields. That choice stays, and the value stays hidden.

They change the indent of the same response. A field that is still
present keeps its choice. A field that is no longer among the masked
fields has its choice forgotten.

They clear the body. Every choice is forgotten. They show a different
response. It starts masked.

### Scope

- After the masked fields of the current response are applied, a reveal
  choice for a field that is no longer among those fields is forgotten.
- A reveal choice for a field that is still present stays, including
  across an indent refresh of the same response.
- A long session that keeps the same view does not retain a choice for a
  field that has left.
- Automated demonstration of the forgotten leftover choice and of the
  choice that stays for a field still present.

### Out of Scope

- Clearing the body. It still forgets every choice, as already promised
  on
  [PYPOST-1549](https://pypost.atlassian.net/browse/PYPOST-1549).
  This ticket does not expand into that test.
- A different response. It still starts masked, as already promised.
  This ticket does not expand into that test.
- Short-response hide-again across an indent refresh. It stays as
  already promised on PYPOST-1549. This ticket does not expand into
  that test.
- A longer response whose formatting finishes in the background, and a
  stale background result. Both stay as already promised on
  [PYPOST-1550](https://pypost.atlassian.net/browse/PYPOST-1550).
  This ticket does not expand into those tests.
- Which fields start masked. The set stays as it is today.
- Hover. It stays as it is.
- Pointer lookup: how the viewer finds the value under the pointer. It
  stays as it is.
- The words of the real value and the words of the mask. They stay as
  they are today.
- Irreversible masking for automated tool access. It stays as it is.
- Reveal choices across application restart, or across save and load.
- Folding, search text, and scroll position.
- A new control for applying masked fields, for indent, or for clear.
  Applying the current masked fields, the existing indent change, and
  the existing clear stay the actions.

### Functional Requirements

- **FR-1 — Leftover choice is forgotten**: After the masked fields of
  the current response are applied, a reveal choice for a field that is
  no longer among those fields is forgotten. A long session that keeps
  the same view does not retain that choice.
- **FR-2 — Present choice stays**: A reveal choice for a field that is
  still among those fields stays. This includes an indent refresh of the
  same response. A field left revealed stays visible. A field left
  hidden stays hidden.
- **FR-3 — Clear still forgets every choice**: Clearing the body still
  forgets every reveal choice for that view. This stays as already
  promised on PYPOST-1549.
- **FR-4 — Different response still starts masked**: A different
  response still starts masked. This stays as already promised.
- **FR-5 — Same masking surface**: Which fields start masked stays the
  same. Hover stays as it is. Pointer lookup stays as it is.

### Non-Functional Requirements

- **NFR-1 — No retained leftover**: Once the masked fields of the
  current response are applied, a choice for a field that has left is
  forgotten. The same view does not keep that choice through a long
  session.
- **NFR-2 — Open inspection stays open**: A field that is still present
  keeps the choice the person made, including across an indent refresh
  of the same response.
- **NFR-3 — Secret stays covered**: Forgetting a leftover choice does
  not reveal a field the person left hidden. A different response still
  starts masked. A clear still forgets every choice.
- **NFR-4 — Same masking rules**: The set of fields that start masked
  stays the same. Hover stays as it is. Pointer lookup stays as it is.
- **NFR-5 — Sibling promises stay**: PYPOST-1549 and PYPOST-1550 stay
  as already promised. This ticket does not expand into those tests.
- **NFR-6 — In scope for this ticket**: The parent treated the outcome
  as nice-to-have and did not require it for the parent definition of
  done. The item is Debt, Low, and 2 story points. It is in this sprint,
  so the outcome is required here.

### Constraints and Assumptions

- The language for the change is Python.
- The ticket is
  [PYPOST-1551](https://pypost.atlassian.net/browse/PYPOST-1551): Debt,
  Low, 2 story points, label tech-debt, parent
  [PYPOST-1392](https://pypost.atlassian.net/browse/PYPOST-1392), source
  TD-3.
- Parent wording called the outcome optional and not required for the
  parent definition of done. Inclusion in this sprint places the
  outcome in scope for this ticket.
- A field still present keeps its reveal choice, including across an
  indent refresh of the same response.
- Clearing the body still forgets every choice. A different response
  still starts masked. Both stay as already promised. PYPOST-1549 owns
  the clear demonstration and the short-response hide-again
  demonstration. This ticket does not expand into those tests.
- PYPOST-1550 owns the longer-response indent demonstration and the
  stale background result. This ticket does not expand into those
  tests.
- Which fields start masked, hover, and pointer lookup stay as they
  are.
- Each response view keeps the reveal choices for the fields still
  among its current masked fields.
- The stored response stays the stored response. A reveal choice
  changes only what the viewer shows for a field that is still present.

## Main Entities and Interactions

- **Response view**: The surface for one response body. It shows hidden
  values as masks until the person reveals them. It keeps a reveal
  choice only for a field that is still among the current masked fields.
- **Masked field**: One sensitive field among the masked fields of the
  current response. Attributes: whether it is revealed, the real value,
  and the mask. Reveal shows the real value. A field left hidden shows
  the mask.
- **Reveal choice**: The person's last preference for a masked field in
  the current view: revealed or hidden. A choice for a field that has
  left is forgotten when the current masked fields are applied.
- **Field that has left**: A field that is no longer among the masked
  fields just applied. Its reveal choice is forgotten.
- **Field still present**: A field that is among the masked fields just
  applied. Its reveal choice stays.
- **Indent refresh**: A change of indentation that rebuilds the visible
  text of the same response. A field still present keeps its last
  reveal choice.
- **Clear**: The person clears the response body. Every reveal choice
  for that view is forgotten. The next body starts masked.
- **Different response**: Another body shown in the view. It starts
  masked. That outcome stays as already promised.
- **Starting masks**: The fields that appear masked when a body is first
  shown. That set stays as it is today.
- **Hover**: Feedback while the pointer rests on a masked value. It
  stays as it is.
- **Pointer lookup**: How the viewer finds the value under the pointer.
  It stays as it is.

The person keeps one view open. After the masked fields of the current
response are applied, a choice for a field that has left is forgotten,
and a choice for a field that is still present stays. An indent refresh
of the same response keeps the choice for a field still present.
Clearing the body still forgets every choice. A different response still
starts masked.

## Q&A

- **Q:** Why forget a reveal choice for a field that has left?
  **A:** A long session that keeps the same view should not retain a
  choice for a field that is no longer among the masked fields. After
  those fields are applied, that leftover choice is forgotten.
- **Q:** The parent called this nice-to-have. Is it required?
  **A:** It was not required for the parent definition of done. The
  ticket is in this sprint, so the outcome is in scope for this ticket.
- **Q:** Does a field that is still present lose its choice?
  **A:** The choice stays. That includes an indent refresh of the same
  response. A field left revealed stays visible. A field left hidden
  stays hidden.
- **Q:** If a forgotten field is among the masked fields again later,
  does the old choice return?
  **A:** The choice was forgotten. The field starts masked until the
  person reveals it again.
- **Q:** What about clearing the body, or a different response?
  **A:** Clearing the body still forgets every choice. A different
  response still starts masked.
- **Q:** Does this change which fields start masked, hover, or pointer
  lookup?
  **A:** They stay as they are.
- **Q:** Does this include the clear demonstration, the hide-again
  demonstration, or the longer-response indent demonstration?
  **A:** PYPOST-1549 and PYPOST-1550 stay as already promised. This
  ticket does not expand into those tests.
- **Q:** What language is this change in?
  **A:** Python.
