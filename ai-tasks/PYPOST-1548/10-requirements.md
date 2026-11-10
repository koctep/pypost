# PYPOST-1548: Optional limit on mask hover feedback

## Goals

A person moving the pointer across a masked response should see hover
feedback for the same value a click at that place would reveal or hide.
Finding that value was already made cheaper. Pointer motion can still ask
for cursor and tooltip updates on every small move. On a slower machine
that stream can keep the viewer busy even when the value under the pointer
has the same meaning it has for a click.

This ticket allows an optional limit on how often that hover feedback
runs. The limit must leave hit results unchanged. The hovered value stays
the value a click at that place would use. Extra pointer-move updates must
not change which value is hovered or which value is revealed or hidden.
With the limit unused, today's hover and click results remain.

How often feedback is limited, and how pointer motion is reduced, belong
to architecture. These requirements state the outcome only.

This item is follow-up debt from
[PYPOST-1390](https://pypost.atlassian.net/browse/PYPOST-1390). It is Debt,
Low, 2 story points, and a non-blocker. Later click targets after a toggle
stay as delivered by
[PYPOST-1547](https://pypost.atlassian.net/browse/PYPOST-1547).

**Implementation language:** Python

## User Stories

- As a **person moving the pointer across a masked response**, I want the
  hovered value to be the same value a click at that place would use, so
  cursor and tooltip agree with reveal and hide.
- As a **person on a slower machine**, I want hover feedback to be allowed
  to run less often while I move the pointer, so cursor and tooltip work
  need not follow every tiny move.
- As a **person clicking a masked value**, I want the click to reveal or
  hide the value under the pointer, the same as today, whether or not
  hover feedback skipped some pointer moves.
- As a **security reviewer**, I want the same fields masked as today, and
  I want reveal to show the real value and hide to show the mask.
- As a **product maintainer**, I want the limit to stay optional, and I
  want later click targets after a toggle to stay the work of
  [PYPOST-1547](https://pypost.atlassian.net/browse/PYPOST-1547).

## Definition of Done

This task is done when all of the following are true:

1. Moving the pointer across a masked response hovers the same value a
   click at that place would use.
2. A limit on how often hover feedback runs is optional. With that limit
   unused, hover and click results stay as they are today.
3. With the limit in use, the hovered value is still the value a click at
   that place would use. Click results stay the same.
4. Extra pointer-move updates do not change which value is hovered or
   which value is revealed or hidden.
5. Which fields are masked stays the same.
6. Reveal still shows the real value. Hide still shows the mask.
7. A click on ordinary response text still targets no masked value. A
   click on the edge of a shown value still targets that value.
8. Later click targets after a toggle stay as delivered by PYPOST-1547.

## Task Description

### Problem

Interactive masking hides sensitive values until the person reveals them.
While the pointer moves over the response, the viewer answers which value
is under the pointer. That answer drives hover feedback (cursor and
tooltip) and the click that reveals or hides the value.

Finding the value under the pointer no longer has to visit every masked
value on each move. Pointer motion itself still arrives for every small
movement, and each arrival can still refresh cursor and tooltip feedback.
That volume was left out of the earlier lookup work on purpose. When the
viewer still feels busy from that feedback on a slower machine, the
product needs an optional way to run hover feedback less often.

The value under the pointer stays the value a click would use. A flood of
pointer moves must leave that value unchanged. A click still lands on the
value at the click. Skipped pointer-move updates must leave that click
result unchanged.

### User Scenario

A dense response shows many masked values. The person moves the pointer
across them. Hover feedback names the value a click at that place would
reveal. The person clicks and sees that value's real text. Moving on and
clicking again hides or reveals the value now under the pointer. If hover
feedback runs less often, the click still uses the value under the
pointer, and hover feedback still names that same value for the place it
describes.

### Scope

- An optional limit on how often mask hover feedback runs while the
  pointer moves.
- The hovered value stays the value a click at that place would use.
- Click reveal and hide results stay the same with the limit used and
  with the limit unused.
- Extra pointer-move updates leave the hovered value and the revealed
  value unchanged.

### Out of Scope

- Any wait, repeat interval, or filter on pointer motion. That choice
  belongs to architecture.
- Later click targets after a toggle. They stay as delivered by
  [PYPOST-1547](https://pypost.atlassian.net/browse/PYPOST-1547).
- Which fields are masked. They stay as they are today.
- The words of the real value and the words of the mask. They stay as
  they are today.
- Hover cursor meaning and tooltip wording. They still refer to the value
  under the pointer.
- How the viewer finds the value under the pointer, beyond keeping that
  answer the same one a click would use. The cheaper lookup from
  [PYPOST-1390](https://pypost.atlassian.net/browse/PYPOST-1390) stays as
  it is.
- Stored response data. It stays unchanged. Reveal and hide change only
  what the viewer shows.

### Functional Requirements

- **FR-1 — Same hover and click target**: For a place in the shown
  response, the hovered value is the value a click at that place would
  use. Ordinary text targets no masked value. The edge of a shown value
  targets that value.
- **FR-2 — Optional limit**: The product may limit how often hover
  feedback runs during pointer motion. The limit is optional. With the
  limit unused, hover and click results stay as they are today.
- **FR-3 — Hits stay the same**: With the limit in use, the value hovered
  at a place and the value a click reveals or hides at that place stay
  the same as they are today.
- **FR-4 — Extra moves**: Further pointer-move updates leave the hovered
  value and the revealed or hidden value unchanged. The value follows the
  place under the pointer.
- **FR-5 — Reveal and hide**: Reveal shows the real value. Hide shows the
  mask. A click still does that for the value under the pointer.
- **FR-6 — Same masked fields**: The set of fields that are masked stays
  the same.
- **FR-7 — Later click targets**: After a reveal or a hide, later click
  targets stay correct under the behavior already delivered. This ticket
  leaves that behavior in place.

### Non-Functional Requirements

- **NFR-1 — Optional and non-blocking**: The item is Low priority. Correct
  hover and click results stand without a limit on pointer motion.
  Ordinary responses may keep updating hover feedback as pointer motion
  arrives.
- **NFR-2 — Limit preserves hits**: A limit is acceptable only while the
  hovered value and the click result for a place stay the same as they
  are today.
- **NFR-3 — Feedback names the click target**: Hover feedback reports the
  value a click would use at the place that feedback describes. Further
  pointer moves do not make that report name a different value.
- **NFR-4 — Clicks follow the pointer**: A click uses the value under the
  pointer at the click. Skipped pointer-move updates leave that result
  unchanged.
- **NFR-5 — Room for slower machines**: The limit exists so cursor and
  tooltip work can run less often when pointer motion still pressures the
  viewer. No machine class, interval, or measurement method is fixed
  here.

### Constraints and Assumptions

- The language for the change is Python.
- The ticket is
  [PYPOST-1548](https://pypost.atlassian.net/browse/PYPOST-1548): Debt,
  Low, 2 story points, non-blocker, parent
  [PYPOST-1390](https://pypost.atlassian.net/browse/PYPOST-1390).
- PYPOST-1390 made finding the value under the pointer cheaper and left
  any limit on hover feedback for a later ticket. This is that ticket.
- PYPOST-1547 keeps later click targets correct after a toggle. This
  ticket leaves that delivery in place.
- The limit is optional. Hit results stay the same whether the limit is
  used or unused.
- No wait, interval, or pointer-motion filter is chosen here. Architecture
  chooses how the optional limit is applied.
- Masked values in one displayed response do not overlap. They appear in
  document order. A click on the edge of a shown value targets that value,
  as it does today.
- The stored response stays the stored response. Reveal and hide change
  only what the viewer shows.
- Which fields are masked follows existing masking rules. This ticket
  does not add, remove, or retarget those rules.

## Main Entities and Interactions

- **Masked value**: One sensitive field in the shown response. Attributes:
  its place in the response, whether it is revealed, the real value, and
  the mask. Reveal shows the real value. Hide shows the mask.
- **Hover target**: The masked value under the pointer, or none when the
  pointer is on ordinary text. It is the same value a click at that place
  would use.
- **Hover feedback**: Cursor and tooltip for the hover target. How often
  this feedback runs may be limited. The limit is optional.
- **Pointer motion**: Movement of the pointer across the response. Further
  motion leaves the hovered value and the revealed value unchanged.
- **Click**: Reveals or hides the value under the pointer. Its result
  stays the same when some pointer-move updates are skipped.
- **Optional hover limit**: A cap on how often hover feedback runs. Used
  or unused, the hover target and the click result for a place stay the
  same.
- **Response viewer**: The surface where the person reads the response,
  moves the pointer, and clicks masked values.
- **Masked-field rules**: The existing choice of which fields are masked.
  They stay as they are.
- **Later click targets**: Where clicks land after a toggle changes how
  much text a value occupies. They stay as delivered by PYPOST-1547.

The person moves the pointer over the response viewer. Hover feedback
names the hover target: the value a click would use at that place. The
person clicks. The viewer reveals the real value or restores the mask.
Extra pointer moves, and the optional limit on hover feedback, leave that
value unchanged.

## Q&A

- **Q:** The source asks for optional throttling or debouncing of pointer
  motion. Which interval or filter is required?
  **A:** None. Those names are the suggested approach. The requirement is
  an optional limit on how often hover feedback runs. Hit results stay the
  same with the limit used and with it unused. The wait, interval, or
  filter belongs to architecture.
- **Q:** May extra pointer moves change which value is hovered or
  revealed?
  **A:** No. The value is the one under the pointer, the same one a click
  at that place would use. More moves leave that value unchanged.
- **Q:** Does the limit change click results?
  **A:** No. A click still reveals or hides the value under the pointer.
  Ordinary text still targets no masked value. The edge of a shown value
  still targets that value. Results match today whether the limit is used
  or unused.
- **Q:** Does this redo how later click targets stay correct after a
  toggle?
  **A:** No. That stays as delivered by
  [PYPOST-1547](https://pypost.atlassian.net/browse/PYPOST-1547).
- **Q:** Do masked fields change?
  **A:** No. Which fields are masked stays the same. Reveal shows the
  real value. Hide shows the mask.
- **Q:** Why does this matter to the person using the viewer?
  **A:** Hover and click must keep naming the same value. Pointer motion
  can still ask for cursor and tooltip updates very often. An optional
  limit lets that feedback run less often on a slower machine while the
  hovered value and the click result stay the same.
- **Q:** What language is this change in?
  **A:** Python.
