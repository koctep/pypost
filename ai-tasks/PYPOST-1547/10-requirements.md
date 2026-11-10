# PYPOST-1547: One toggle keeps later click targets correct

## Goals

A person inspecting a masked response can click a hidden value to see the
real text, and click that value again to put the mask back. Either click
changes how much text that value occupies. Every masked value that comes
later in the same response must still be the click target at its new
place, so the next click lands on the value that is actually there.

Today, keeping those later click targets correct means visiting each later
masked value. In a large response that visit grows with the number of
masked values, even though the person toggled only one. Finding which
value is under a click already stays ordered. This ticket is the remaining
cost of a toggle: that work must not grow by visiting every later masked
value, including when many values follow the one that was toggled.

Reveal still shows the real value. Hide still shows the mask. Which fields
are masked stays the same. Click targets stay in document order so ordered
click lookup still finds the value under the pointer.

How later click targets are kept correct is deferred to architecture. These
requirements state the outcome only.

This item is follow-up debt from
[PYPOST-1390](https://pypost.atlassian.net/browse/PYPOST-1390). It is Debt,
Low, 5 story points, and a non-blocker.

**Implementation language:** Python

## User Stories

- As a **person inspecting a large masked response**, I want one reveal or
  one hide to leave every later click target on the value now shown at
  that place, so the next click does not land on a neighbor.
- As a **person revealing many values in a dense response**, I want each
  toggle to stay acceptable as the number of masked values grows, so the
  viewer does not do that work by walking every later masked value.
- As a **person clicking in the response**, I want click targets to stay
  in document order, so the value under the pointer is still the one that
  is revealed or hidden.
- As a **security reviewer**, I want reveal to show the real value and
  hide to show the mask, and I want the same fields masked as today.
- As a **product maintainer**, I want pointer-motion throttling to stay on
  [PYPOST-1548](https://pypost.atlassian.net/browse/PYPOST-1548), so this
  ticket stays limited to later click targets after a toggle.

## Definition of Done

This task is done when all of the following are true:

1. After one reveal or one hide, every later click target still matches
   the masked or revealed value that occupies that place in the response.
2. The work of that toggle does not grow by visiting every later masked
   value when many masked values follow the toggled one.
3. Click targets stay in document order before and after the toggle, so a
   click still finds the value under the pointer.
4. Reveal still shows the real value. Hide still shows the mask.
5. Which fields are masked stays the same.
6. A series of toggles keeps later click targets correct after each one,
   and each toggle obeys the same limit on visiting later values.
7. Pointer-motion throttling stays on PYPOST-1548.

## Task Description

### Problem

Interactive masking shows sensitive values as masks until the person
reveals them. A click on a masked value shows the real text. A click on a
revealed value shows the mask again. Because those two texts differ in
length, every later masked value in the same response moves.

The person still needs each of those later values to be the click target
at its new place. A click on ordinary response text still targets no
masked value. A click on the edge of a shown value still targets that
value, the same way it does today.

The cost that remains is the update itself. With a handful of masked
values the update is invisible. With many masked values, updating later
click targets by visiting each of them grows with that count. A toggle
near the start of a dense response affects every later value and is the
case that must stay acceptable. A toggle with nothing after it still
reveals or hides that one value correctly.

Ordered click lookup, already acceptable under high counts of masked
values, continues to depend on click targets remaining in document order.
This ticket keeps that order. It does not reopen how a click finds the
value under the pointer, except to keep that lookup ordered and its
answers correct after each toggle.

### User Scenario

A dense response shows many masked values. The person reveals one near
the start and sees its real value. A later click reveals the value now
shown at that later place, and shows that value's real text. Hiding the
first value puts its mask back. Later clicks still land on the values now
shown, in the order they appear in the response.

### Scope

- Later click targets after one reveal or one hide stay on the values now
  shown at those places.
- The work of one toggle does not grow by visiting every later masked
  value.
- Click targets stay in document order so ordered click lookup still finds
  the value under the pointer.
- Reveal still shows the real value. Hide still shows the mask.
- A series of toggles keeps those results after each toggle.

### Out of Scope

- Pointer-motion throttling stays on
  [PYPOST-1548](https://pypost.atlassian.net/browse/PYPOST-1548).
- Which fields are masked stays as it is today.
- The words of the real value and the words of the mask stay as they are
  today.
- Hover cursor and tooltip copy stay as they are today. After a toggle,
  a click still targets the value now shown at that place.
- Stored response data stays unchanged. The viewer changes what is shown
  and where later clicks land.
- The choice of structure that keeps later click targets correct. That
  choice belongs to architecture.

### Functional Requirements

- **FR-1 — Later click targets**: After a toggle changes how much text one
  masked value occupies, every later click target refers to the masked or
  revealed value now shown at that place. A click on ordinary response
  text still targets no masked value. A click on the edge of a shown value
  still targets that value.
- **FR-2 — Toggle work**: The work of one toggle does not grow by visiting
  every later masked value. This holds when many values follow the toggled
  one, and when none do.
- **FR-3 — Ordered click lookup**: Click targets remain in document order
  before and after each toggle. A click finds the value under the pointer
  by that order.
- **FR-4 — Reveal and hide**: Reveal shows the real value. Hide shows the
  mask. The toggled value and every other shown value keep those results.
- **FR-5 — Same masked fields**: The set of fields that are masked does
  not change.
- **FR-6 — Repeated toggles**: Each toggle in a series leaves later click
  targets correct for the next click, and each toggle obeys FR-2.

### Non-Functional Requirements

- **NFR-1 — Acceptable in a dense response**: When many masked values are
  present, toggling one of them stays acceptable. The work does not grow
  by visiting each later masked value. A toggle near the start, which
  moves every later click target, is included.
- **NFR-2 — Click targets stay correct**: A lighter toggle is acceptable
  only while a later click still lands on the value now shown at that
  place, including at the edges of that value.
- **NFR-3 — Reveal and hide stay correct**: A lighter toggle is acceptable
  only while reveal shows the real value and hide shows the mask.
- **NFR-4 — Order stays usable**: Ordered click lookup remains usable after
  every toggle because click targets stay in document order.
- **NFR-5 — Non-blocker**: The item is Low priority. Typical responses with
  few masked values may already feel immediate. The outcome still applies
  when many masked values are present.

### Constraints and Assumptions

- Language for the change is Python.
- The ticket is
  [PYPOST-1547](https://pypost.atlassian.net/browse/PYPOST-1547): Debt,
  Low, 5 story points, non-blocker, parent
  [PYPOST-1390](https://pypost.atlassian.net/browse/PYPOST-1390).
- PYPOST-1390 left this cost for a later ticket. Click lookup there
  already stays ordered. This ticket keeps that order and keeps click
  answers correct after each toggle.
- The structure that keeps later click targets correct is deferred to
  architecture. These requirements do not select one.
- Pointer-motion throttling is a separate concern and stays on
  PYPOST-1548.
- Masked values in one displayed response do not overlap, and they appear
  in document order. A toggle preserves that order.
- The stored response stays the stored response. Reveal and hide change
  only what the viewer shows and where later clicks land.
- Which fields are masked is decided by existing masking rules. This
  ticket does not add, remove, or retarget those rules.

## Main Entities and Interactions

- **Masked value**: One sensitive field in the shown response. Attributes:
  its place in the response, whether it is revealed, the real value, and
  the mask. Reveal shows the real value. Hide shows the mask.
- **Click target**: The place the person clicks to reveal or hide that
  value. After a toggle, each later click target follows the value that
  moved.
- **Toggle**: One click that reveals a masked value or hides a revealed
  value. It changes how much text that value occupies, so later click
  targets move. Its work does not grow by visiting every later masked
  value.
- **Document order**: The order masked values appear in the response.
  Click targets stay in that order so click lookup can find the value
  under the pointer.
- **Response viewer**: The surface where the person reads the response and
  clicks masked values. It shows the real value or the mask and keeps
  later clicks on the values now shown.
- **Masked-field rules**: The existing choice of which fields are masked.
  They stay as they are.

The person clicks a masked value in the response viewer. The viewer
reveals the real value or restores the mask. Later click targets move
with the values that follow, and they stay in document order. The next
click uses that order and lands on the value now shown at that place.

## Q&A

- **Q:** The source describes several ways to keep later click targets
  correct. Which way is required?
  **A:** None is required here. The structure choice is deferred to
  architecture. Click targets stay correct, click lookup stays ordered,
  and reveal and hide results stay correct.
- **Q:** May a toggle still visit every later masked value when that is
  simpler?
  **A:** No. The work of one toggle must not grow by visiting every later
  masked value. Later click targets must still be correct, including
  after a series of toggles.
- **Q:** What must stay true for the person clicking?
  **A:** A later click lands on the value now shown at that place. Reveal
  shows the real value. Hide shows the mask. Click targets stay in
  document order. Which fields are masked stays the same.
- **Q:** Is pointer-motion throttling part of this work?
  **A:** No. It stays on
  [PYPOST-1548](https://pypost.atlassian.net/browse/PYPOST-1548).
- **Q:** What language is this change in?
  **A:** Python.
