# PYPOST-1549: Clear forgets a reveal; hide-again survives indent

## Goals

A person inspecting a masked response can reveal one sensitive value and
leave the others hidden. That choice is part of the inspection. Two
follow-on actions must keep their meaning.

Clearing the response body is a deliberate end to that inspection. The
revealed value is forgotten. The next body shown in that view starts
masked, including when the content matches the body that was cleared.

Changing indent only refreshes how the same response is shown. If the
person revealed a value and then masked that same value again, the
refresh leaves it hidden. A value they left revealed stays visible. A
value they never revealed stays masked.

Those outcomes were already promised for interactive masking. Indent
persistence for a value left revealed, and a full reset when a different
response is shown, are already demonstrated. The clear, and the
hide-again choice across an indent refresh, still need their own
demonstration. A regression there can uncover a secret the person already
covered, or restore a secret they dismissed by clearing the body.

This ticket is that demonstration. The product rules stay the ones
already promised. The behavior may already hold.

This item is follow-up debt from
[PYPOST-1392](https://pypost.atlassian.net/browse/PYPOST-1392),
recorded there as TD-1. It is Debt, Low, 3 story points, and a
non-blocker. The parent clear outcome is parent FR-5. The parent
hide-again outcome is parent FR-7.

**Implementation language:** Python

## User Stories

- As a **person inspecting a masked response**, I want clearing the
  response body to forget a value I revealed, so the next body starts
  masked.
- As a **person who revealed a value and then masked it again**, I want
  an indent change on the same response to leave that value hidden, so
  the secret stays covered.
- As a **person who left another value revealed**, I want that value to
  stay visible across the same indent change, so the inspection I kept
  open is still open.
- As a **security-conscious user**, I want a clear to dismiss a revealed
  secret, and I want a hide-again choice to survive an indent refresh of
  the same response.
- As a **product maintainer**, I want these two outcomes demonstrated on
  their own, beside the indent and new-response outcomes already shown.
  Background reformat of a longer response stays on
  [PYPOST-1550](https://pypost.atlassian.net/browse/PYPOST-1550).
  Cleanup of leftover reveal choices stays on
  [PYPOST-1551](https://pypost.atlassian.net/browse/PYPOST-1551).

## Definition of Done

This task is done when all of the following are true:

1. After a person reveals a masked value, clearing the response body
   forgets that reveal. The next body in that view starts masked,
   including when the content matches the body that was cleared.
2. After a person reveals a value and then masks that same value again,
   an indent change on the same response leaves that value hidden. The
   real value stays covered.
3. Across that same indent change, a value left revealed stays visible,
   and a value never revealed stays masked.
4. Which fields start masked stays the same. Reveal shows the real
   value. Masking again shows the mask.
5. A different response still starts masked. An indent change still
   keeps a reveal the person left in place.
6. Hover feedback stays as it is. How the viewer finds the value under
   the pointer stays as it is. Later click targets after a toggle stay
   as they are.
7. Background reformat of a longer response stays on PYPOST-1550.
   Cleanup of leftover reveal choices stays on PYPOST-1551.
8. Automated checks demonstrate the clear outcome and the hide-again
   outcome. The checks pass.

## Task Description

### Problem

Interactive masking hides sensitive values until the person reveals
them. A later click on a revealed value shows the mask again. Those
choices belong to the response on screen.

Clearing the response body ends that view of the body. The reveal must
end with it. Showing a body again after the clear starts masked. The
secret the person had uncovered stays covered.

An indent change rebuilds the visible text of the same response. It is
a presentation refresh, and the underlying response stays the same.
Choices survive that refresh. A value masked again before the refresh
stays hidden afterward. A value left revealed stays visible. A value
never revealed stays masked.

Indent persistence for a single reveal, with its siblings still masked,
is already demonstrated. Reset on a different response is already
demonstrated. The dedicated gaps are the clear, and the hide-again
choice before an indent refresh.

### User Scenario

The response shows two hidden values. The person reveals the first. They
clear the response body. The revealed value is gone. They show a body
again, including the same content. Both hidden values start masked.

On a later look, the person reveals the first value, then masks it
again, and leaves the second value revealed. They change the indent.
The first value stays hidden. The second value stays visible. Any
further hidden value they never touched stays masked.

### Scope

- Clearing the response body forgets reveal choices for that view.
- The next body shown after a clear starts masked.
- Masking a revealed value again, then changing indent on the same
  response, leaves that value hidden.
- A value left revealed stays visible across that indent change. A
  value never revealed stays masked.
- Automated demonstration of the clear outcome and the hide-again
  outcome.
- Which fields start masked stays the same.

### Out of Scope

- Background reformat of a longer response. That stays on
  [PYPOST-1550](https://pypost.atlassian.net/browse/PYPOST-1550).
- Cleanup of leftover reveal choices for values no longer shown. That
  stays on
  [PYPOST-1551](https://pypost.atlassian.net/browse/PYPOST-1551).
- Hover feedback, including any optional limit on how often it runs.
  It stays as it is.
- How the viewer finds the value under the pointer, and how later click
  targets stay correct after a toggle. They stay as they are.
- Which fields are masked. The set stays as it is today.
- The words of the real value and the words of the mask. They stay as
  they are today.
- Irreversible masking for automated tool access. It stays as it is.
- Reveal choices across application restart, or across save and load.
- Folding, search text, and scroll position.
- A new control for clearing or for indent. The existing clear and the
  existing indent change are the actions.

### Functional Requirements

- **FR-1 — Clear forgets the reveal**: After the person reveals a masked
  value, clearing the response body forgets that reveal for that view.
  The next body shown in the view starts masked. This includes a body
  whose content matches the body that was cleared. This is the parent
  clear outcome (parent FR-5).
- **FR-2 — Hide again survives indent**: After the person reveals a
  value and then masks that same value again, changing indent on the
  same response leaves that value hidden. The real value stays covered.
  This is the parent hide-again outcome (parent FR-7).
- **FR-3 — Other choices survive that refresh**: Across the same indent
  change, a value the person left revealed stays visible. A value the
  person never revealed stays masked. Each value keeps its own choice.
- **FR-4 — Same masked fields**: Which fields start masked stays the
  same. Reveal shows the real value. Masking again shows the mask.

### Non-Functional Requirements

- **NFR-1 — Secret stays covered**: A clear leaves the next body masked.
  A hide-again choice leaves that value hidden after the indent refresh.
  A value the person left masked stays masked.
- **NFR-2 — Clear and refresh differ**: A clear forgets reveal choices.
  An indent change of the same response keeps each value's last choice,
  including a choice to mask a value again.
- **NFR-3 — Same masking rules**: The set of fields that start masked
  stays the same.
- **NFR-4 — Coverage of promised behavior**: The item is Debt, Low, and
  3 story points. The outcomes were already required. This ticket
  demonstrates them. The existing clear and the existing indent change
  remain the actions.
- **NFR-5 — One view's choices**: Reveal choices belong to the response
  view that recorded them. A clear on that view forgets that view's
  choices.

### Constraints and Assumptions

- The language for the change is Python.
- The ticket is
  [PYPOST-1549](https://pypost.atlassian.net/browse/PYPOST-1549): Debt,
  Low, 3 story points, non-blocker, parent
  [PYPOST-1392](https://pypost.atlassian.net/browse/PYPOST-1392), source
  TD-1.
- Parent clear outcome: clearing the response body discards reveal
  choices for that view. Parent hide-again outcome: a value the person
  revealed and then masked again stays masked after an indent refresh
  of the same response.
- Indent persistence for a value left revealed, and reset when a
  different response is shown, are already demonstrated. This ticket
  complements them.
- The outcomes may already hold. The gap is a dedicated demonstration
  of the clear and of the hide-again choice.
- PYPOST-1550 owns background reformat of a longer response.
  PYPOST-1551 owns cleanup of leftover reveal choices. This ticket
  leaves both where they are.
- Hover feedback stays as it is. Finding the value under the pointer
  stays as it is. Later click targets after a toggle stay as they are.
- Each response view keeps its own reveal choices.
- The stored response stays the stored response. Reveal and hide change
  only what the viewer shows. A clear removes that showing of the body.

## Main Entities and Interactions

- **Response view**: The surface for one response body. It shows hidden
  values as masks until the person reveals them. It owns the reveal
  choices for the body on screen.
- **Masked value**: One sensitive field in the shown response.
  Attributes: whether it is revealed, the real value, and the mask.
  Reveal shows the real value. Masking again shows the mask.
- **Reveal choice**: The person's last preference for a masked value in
  the current body: revealed or masked.
- **Clear**: The person clears the response body. Reveal choices for
  that view are forgotten. The next body starts masked.
- **Indent refresh**: A change of indentation that rebuilds the visible
  text of the same response. Each value keeps its last reveal choice,
  including a choice to mask a value again.
- **Starting masks**: The fields that appear masked when a body is first
  shown. That set stays as it is today.
- **Different response**: Another body shown in the view. It starts
  masked. That outcome is already demonstrated and stays in place.

The person reveals a masked value. Clearing the body forgets that
reveal, and the next body starts masked. On the same response, masking
a revealed value again and then changing indent leaves that value
hidden, while a value left revealed stays visible.

## Q&A

- **Q:** The task note says reformatting the same response and masking
  it again keeps the revealed value visible. Does masking a value again
  leave it visible after indent?
  **A:** Masking that same value again leaves it hidden. The value that
  stays visible is a different one: a value the person revealed and left
  revealed. An indent refresh of the same response keeps each choice.
  The hidden-again value stays hidden. The still-revealed value stays
  visible.
- **Q:** After a clear, does showing the same content restore the
  reveal?
  **A:** The next body starts masked when its content matches the
  cleared body. The reveal stays forgotten.
- **Q:** Is a different response the same outcome as a clear?
  **A:** A different response already starts masked, and that outcome
  is already demonstrated. A clear is the explicit emptying of the
  response body. This ticket demonstrates that the clear forgets the
  reveal and that the next body starts masked.
- **Q:** Does this change which fields start masked?
  **A:** The set stays the same. Reveal shows the real value. Masking
  again shows the mask.
- **Q:** Does this include background reformat of a longer response?
  **A:** That stays on
  [PYPOST-1550](https://pypost.atlassian.net/browse/PYPOST-1550).
- **Q:** Does this remove leftover reveal choices for values that are
  no longer shown?
  **A:** That stays on
  [PYPOST-1551](https://pypost.atlassian.net/browse/PYPOST-1551).
  This ticket demonstrates the clear and the hide-again choice.
- **Q:** Does this change hover feedback or how a click finds its
  value?
  **A:** Hover feedback stays as it is. How the viewer finds the value
  under the pointer stays as it is. Later click targets after a toggle
  stay as they are.
- **Q:** What language is this change in?
  **A:** Python.
