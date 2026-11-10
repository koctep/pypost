# PYPOST-1550: Longer-response indent keeps reveal choices

## Goals

A person inspecting a masked response can reveal one sensitive value and
leave the others hidden. That choice is part of the inspection. Changing
indent only refreshes how the same response is shown. A value they
revealed stays visible. A value they left hidden stays hidden.

A short response finishes formatting before the person continues, and
that refresh already keeps those choices. A longer response can finish
formatting in the background. The formatted text arrives after the
person has already chosen what to reveal. Applying that formatted text
must restore the same choices: a revealed value stays visible, and a
value left hidden stays hidden.

A newer display can appear while an older format is still finishing.
When that older background format finishes late, it is a stale
background result. It must leave the newer display as the person sees
it. The late result does not replace the newer text, and it does not
change which values are revealed there.

Those outcomes were already promised for an indent refresh of the same
response. The short response is already demonstrated. The longer
response, whose formatting finishes in the background, still needs its
own demonstration, including the case where a stale background result
finishes late. A regression there can cover a value the person had
opened, uncover a value they left hidden, or replace a newer display
with an older one.

This ticket is that demonstration. The product rules stay the ones
already promised. The behavior may already hold.

This item is follow-up debt from
[PYPOST-1392](https://pypost.atlassian.net/browse/PYPOST-1392),
recorded there as TD-2. It is Debt, Low, 3 story points, and a
non-blocker. The parent indent outcome is parent FR-2. The parent
partial-reveal outcome is parent FR-6.

**Implementation language:** Python

## User Stories

- As a **person inspecting a longer masked response**, I want a value I
  revealed to stay visible after an indent change, including when the
  formatted text is applied after background work, so the inspection I
  kept open is still open.
- As a **person who left a value hidden** on that longer response, I
  want the indent change to leave that value hidden, including when the
  formatted text is applied after background work, so the secret stays
  covered.
- As a **person looking at a newer display**, I want a stale background
  result that finishes late to leave that display alone, so an older
  format does not replace what I am looking at.
- As a **security-conscious user**, I want a value I left hidden to stay
  hidden after a background indent refresh, and I want a late older
  format to leave the newer display unchanged.
- As a **product maintainer**, I want these outcomes demonstrated for a
  longer response whose formatting finishes in the background. Clearing
  the body and short-response re-mask stay as already promised on
  [PYPOST-1549](https://pypost.atlassian.net/browse/PYPOST-1549).
  Cleanup of leftover reveal choices stays on
  [PYPOST-1551](https://pypost.atlassian.net/browse/PYPOST-1551).

## Definition of Done

This task is done when all of the following are true:

1. On a longer response, a value the person revealed stays visible after
   an indent change, including when the formatted text is applied after
   background work.
2. On that same longer response, a value they left hidden stays hidden
   after the indent change, including when the formatted text is applied
   after background work.
3. A newer display is not overwritten by a stale background result. An
   older background format that finishes late leaves the newer display
   in place.
4. Which fields start masked stays the same. Hover stays as it is.
   Pointer lookup stays as it is.
5. Clearing the body stays as already promised. Short-response re-mask
   stays as already promised. Both remain in force and are unchanged by
   this ticket.
6. Cleanup of leftover reveal choices stays on PYPOST-1551.
7. Automated checks demonstrate the longer-response indent outcome and
   the stale-background-result outcome. The checks pass.

## Task Description

### Problem

Interactive masking hides sensitive values until the person reveals
them. An indent change rebuilds the visible text of the same response.
It is a presentation refresh. The underlying response stays the same.
Choices survive that refresh. A value the person revealed stays
visible. A value they left hidden stays hidden.

On a short response the refresh finishes immediately, and that path is
already demonstrated. On a longer response the formatting finishes in
the background. The person can reveal or leave values hidden before
that formatted text is applied. When the formatted text is applied, the
same choices must still be on screen.

The person can also move on to a newer display before the older format
finishes. That late completion is a stale background result. It must
not overwrite the newer display.

### User Scenario

The longer response shows two hidden values. The person reveals the
first and leaves the second hidden. They change the indent. Formatting
finishes in the background. When the formatted text is applied, the
first value stays visible and the second stays hidden.

While an older format of a longer response is still finishing, a newer
display is shown. The older format then finishes. The screen stays on
the newer display. The stale background result does not replace it.

### Scope

- On a longer response, an indent change keeps a revealed value visible
  and a value left hidden hidden.
- That outcome holds when the formatted text is applied after background
  work.
- A stale background result does not overwrite a newer display.
- Automated demonstration of those two outcomes.
- Which fields start masked stays the same.

### Out of Scope

- Clearing the response body. That stays as already promised on
  [PYPOST-1549](https://pypost.atlassian.net/browse/PYPOST-1549).
- Short-response re-mask. Masking a revealed value again, then changing
  indent on a short response, stays as already promised on
  PYPOST-1549.
- The short response whose formatting finishes immediately. Reveal
  persistence there is already demonstrated and stays in place.
- Cleanup of leftover reveal choices for values no longer shown. That
  stays on
  [PYPOST-1551](https://pypost.atlassian.net/browse/PYPOST-1551).
- Hover feedback. It stays as it is.
- Pointer lookup: how the viewer finds the value under the pointer. It
  stays as it is.
- Which fields start masked. The set stays as it is today.
- The words of the real value and the words of the mask. They stay as
  they are today.
- Irreversible masking for automated tool access. It stays as it is.
- Reveal choices across application restart, or across save and load.
- Folding, search text, and scroll position.
- A new control for indent. The existing indent change is the action.

### Functional Requirements

- **FR-1 — Revealed value stays visible**: On a longer response, a value
  the person revealed stays visible after an indent change. This
  includes the moment the formatted text is applied after background
  work. This is the parent indent outcome for that longer response
  (parent FR-2).
- **FR-2 — Hidden value stays hidden**: On that same longer response, a
  value the person left hidden stays hidden after the indent change,
  including when the formatted text is applied after background work.
  The real value stays covered. This is the parent partial-reveal
  outcome for that longer response (parent FR-6).
- **FR-3 — Stale background result leaves the newer display**: A newer
  display is not overwritten by an older background format that
  finishes late. The newer display stays what the person sees.
- **FR-4 — Same masked fields**: Which fields start masked stays the
  same. Reveal shows the real value. A value left hidden shows the
  mask.

### Non-Functional Requirements

- **NFR-1 — Secret stays covered**: A value the person left hidden stays
  hidden after the background indent refresh. The refresh does not
  uncover a value they did not reveal.
- **NFR-2 — Open inspection stays open**: A value the person revealed
  stays visible when the formatted text of that longer response is
  applied. The refresh does not cover a value they chose to see.
- **NFR-3 — Newer display wins**: A stale background result does not
  replace a newer display, and it does not change the reveal choices
  on that newer display.
- **NFR-4 — Same masking rules**: The set of fields that start masked
  stays the same. Hover stays as it is. Pointer lookup stays as it is.
- **NFR-5 — Coverage of promised behavior**: The item is Debt, Low, and
  3 story points. The outcomes were already required. This ticket
  demonstrates them for a longer response whose formatting finishes in
  the background. The existing indent change remains the action.
- **NFR-6 — One view's choices**: Reveal choices belong to the response
  view that recorded them. A background refresh of that same response
  keeps those choices. A newer display keeps its own.

### Constraints and Assumptions

- The language for the change is Python.
- The ticket is
  [PYPOST-1550](https://pypost.atlassian.net/browse/PYPOST-1550): Debt,
  Low, 3 story points, non-blocker, parent
  [PYPOST-1392](https://pypost.atlassian.net/browse/PYPOST-1392), source
  TD-2. Status at the start of this step is In Progress.
- Parent indent outcome: after the person reveals a value, an indent
  change of the same response leaves that value visible. Parent
  partial-reveal outcome: a value left hidden stays hidden.
- The short response, whose formatting finishes immediately, already
  demonstrates indent persistence. This ticket complements that
  demonstration for a longer response whose formatting finishes in the
  background.
- Clearing the body and short-response re-mask stay as already promised
  on PYPOST-1549. This ticket leaves both where they are.
- PYPOST-1551 owns cleanup of leftover reveal choices. This ticket
  leaves that where it is.
- Hover stays as it is. Pointer lookup stays as it is. Which fields
  start masked stays as it is.
- Each response view keeps its own reveal choices.
- The stored response stays the stored response. Reveal and hide change
  only what the viewer shows. An indent change only refreshes that
  showing.
- The outcomes may already hold. The gap is a dedicated demonstration
  for the longer response and for a stale background result.

## Main Entities and Interactions

- **Response view**: The surface for one response body. It shows hidden
  values as masks until the person reveals them. It owns the reveal
  choices for the body on screen.
- **Masked value**: One sensitive field in the shown response.
  Attributes: whether it is revealed, the real value, and the mask.
  Reveal shows the real value. A value left hidden shows the mask.
- **Reveal choice**: The person's last preference for a masked value in
  the current body: revealed or hidden.
- **Indent refresh**: A change of indentation that rebuilds the visible
  text of the same response. Each value keeps its last reveal choice.
- **Longer response**: A response whose formatting finishes in the
  background. The formatted text is applied when that background work
  finishes. Applying it restores the reveal choices for that display.
- **Stale background result**: An older background format that finishes
  after a newer display is already shown. It leaves the newer display
  in place.
- **Newer display**: The response the person is looking at now. It is
  not replaced by a stale background result.
- **Starting masks**: The fields that appear masked when a body is first
  shown. That set stays as it is today.
- **Short response**: A response whose formatting finishes immediately.
  Indent persistence there is already demonstrated and stays in place.

The person reveals one value on a longer response and leaves another
hidden. They change the indent. When the formatted text is applied
after background work, the revealed value stays visible and the hidden
value stays hidden. If a newer display is already showing when an older
background format finishes, that stale background result leaves the
newer display in place.

## Q&A

- **Q:** Does an indent change on a longer response cover a value the
  person already revealed?
  **A:** The revealed value stays visible. That includes the moment the
  formatted text is applied after background work.
- **Q:** Does that same refresh uncover a value they left hidden?
  **A:** The value they left hidden stays hidden. The real value stays
  covered.
- **Q:** What if an older format finishes after the person is already
  looking at a newer display?
  **A:** That completion is a stale background result. It does not
  overwrite the newer display.
- **Q:** Does this change which fields start masked?
  **A:** The set stays the same. Reveal shows the real value. A value
  left hidden shows the mask.
- **Q:** Does this include clearing the body, or re-mask on a short
  response?
  **A:** Both stay as already promised on
  [PYPOST-1549](https://pypost.atlassian.net/browse/PYPOST-1549). This
  ticket does not reopen them.
- **Q:** Does the short response need another demonstration here?
  **A:** Indent persistence for a short response, whose formatting
  finishes immediately, is already demonstrated. This ticket is the
  longer response whose formatting finishes in the background.
- **Q:** Does this remove leftover reveal choices for values that are
  no longer shown?
  **A:** That stays on
  [PYPOST-1551](https://pypost.atlassian.net/browse/PYPOST-1551).
- **Q:** Does this change hover, or how a click finds its value?
  **A:** Hover stays as it is. Pointer lookup stays as it is.
- **Q:** What language is this change in?
  **A:** Python.
