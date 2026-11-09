# PYPOST-1542: Remove unused selector match helpers

## Goals

Response masking decides whether a field is hidden through the live match
behavior that redaction and the response viewer already use. Two extra match
helpers sit beside that behavior and have no production caller.

A helper nobody calls is a second way to answer the same question. A later
change can follow the unused helper and drift from the fields that are
actually masked. This debt item, recorded in
[PYPOST-1388 technical debt](ai-tasks/PYPOST-1388/60-tech-debt.md), exists so
maintainers have one masking outcome: the live one. Removing the unused
helpers must not change which fields that live outcome hides.

**Implementation language:** Python

## User Stories

- As a **maintainer of response masking**, I want match helpers that
  production never calls to be gone, so the only mask decision I can follow
  is the one redaction and the response viewer already use.
- As a **security reviewer**, I want the same selectors and document
  locations to stay masked or visible exactly as they are today, so cleanup
  does not weaken hidden fields.
- As a **quality engineer**, I want the older checks that still call the
  unused compiled-selector matcher to judge the live masking outcome, so
  those cases stay locked without keeping a production method that only a
  test calls.

## Definition of Done

This task is done when all of the following are true:

1. Production masking has no match helper left that production never calls.
   The sequence-oriented trie helper and the compiled-selector matcher are
   both gone.
2. For the same hidden-field rules and the same document location, the live
   mask decision is unchanged, including shorthand matching when the
   document path uses a wildcard.
3. The older unit checks that call the compiled-selector matcher now judge
   that live mask decision for the same rules and the same expected masked
   or not results. Checks that the compiler still turns a hierarchical rule
   into the segments production compile uses remain.
4. The developer guide for the selector engine does not present either
   removed helper as available.
5. Hierarchical rules still compile, and redaction and the response viewer
   still ask the live mask decision.

## Task Description

### Problem

Production masking asks whether a field at a document location matches a
hidden-field rule. That question is answered by the live path-and-key match
and, when the document path contains a wildcard, by the live shorthand
match. Callers are response redaction and the response-viewer mask path.

The sequence-oriented trie helper answers the same kind of question from a
combined token list. Nothing in production or in tests calls it. The
developer guide still describes it as available for future callers.

The compiled-selector matcher answers a token-sequence question on one
compiled rule. Production compile still builds those rules and still uses
their segments. Production masking does not call the matcher. The only
caller is the older tokenization-and-matching check in the PYPOST-1394
selector tests: a full wildcard path that matches, a same-length path whose
field does not, and a path that is too short, for both a single wildcard
and a repeated wildcard.

Leaving either helper in place keeps an unused production match path.
Wiring the sequence-oriented helper into live masking would add a second
production entry for a question the live walks already answer.

### Scope

- The sequence-oriented trie match helper is removed. It is not connected
  to live masking.
- The compiled-selector matcher is removed.
- The older checks that call that matcher move to the live mask decision,
  with the same expected masked or not results. Segment checks that
  production compile still depends on stay in that test.
- The developer guide stops describing the removed helpers as available.
- Live mask results for current rules and locations stay the same.

### Out of Scope

- Replacing the compiled-rule list or the scaling probe that watches it
  ([PYPOST-1543](https://pypost.atlassian.net/browse/PYPOST-1543)).
- Remembering whether a document path contains a wildcard without scanning
  it ([PYPOST-1544](https://pypost.atlassian.net/browse/PYPOST-1544)).
- A new isolated trie catalog, equivalence table, or wildcard fan-out
  stress suite
  ([PYPOST-1545](https://pypost.atlassian.net/browse/PYPOST-1545)).
- A broader rewrite of the PYPOST-1394 selector tests beyond the checks
  that call the compiled-selector matcher.
- Any other follow-up in the PYPOST-1388 debt list.

### Functional Requirements

- **FR-1 — One live mask decision**: Production masking continues to decide
  a field from the live path-and-key match and the live shorthand match.
  No unused match helper remains beside that decision.
- **FR-2 — Same mask results**: For the same hidden-field rules and the
  same document location, a field that is masked today stays masked, and a
  field that is visible today stays visible.
- **FR-3 — Older matcher checks follow the live outcome**: The cases the
  compiled-selector matcher still locks (matching wildcard path, wrong
  field, path too short, including a repeated wildcard) are judged by the
  live mask decision. Segment checks for rules production still compiles
  stay.
- **FR-4 — Guide matches what remains**: A maintainer reading the selector
  engine guide does not find either removed helper offered as a way to
  match.

### Non-Functional Requirements

- **NFR-1 — No behavior change for callers**: Redaction and the response
  viewer keep the mask results they have today. This cleanup does not
  require a faster or slower match.
- **NFR-2 — No second production match path**: The work does not add a new
  production caller for a combined-token match.
- **NFR-3 — Existing selector checks stay meaningful**: Selector tests that
  already lock live mask results continue to lock those results, with
  explicit timeouts left as they are.

### Constraints and Assumptions

- Language for the change is Python.
- The source note is
  [PYPOST-1388 technical debt](ai-tasks/PYPOST-1388/60-tech-debt.md). The
  ticket is Debt, 2 points, parent context PYPOST-1388, and is a
  non-blocker.
- Inspection: the sequence-oriented trie helper has no production caller
  and no test caller. The compiled-selector matcher has no production
  caller; its only caller is the PYPOST-1394 tokenization-and-matching
  test. Live masking uses the path-and-key and shorthand matches.
- Compilation of hierarchical rules stays, because production still
  compiles those rules into segments before the live decision. This ticket
  removes unused match helpers only.
- Sibling debts stay on their own tickets even if they touch the same
  engine.

## Main Entities and Interactions

- **Hidden-field rule**: A configured name or path whose matching values
  must be hidden. Attributes that matter here: whether it is a body rule,
  and whether it is hierarchical.
- **Document location**: Where a field sits while a payload is walked
  (ancestor segments plus the field name). A wildcard segment means the
  field is inside an array.
- **Live mask decision**: The yes-or-no answer production redaction and the
  response viewer already use for that rule set and location, including
  shorthand when the location contains a wildcard.
- **Unused match helper**: A match question with no production caller. It
  is not part of the live decision and is removed.
- **Compiler segments**: The segments a hierarchical rule is reduced to so
  the live decision can be prepared. Those segments stay in use.

Redaction and the response viewer ask the live mask decision. They do not
ask the unused helpers. The older test that still asks the compiled-selector
matcher asks the live mask decision instead. Maintainers reading the guide
see only the live decision.

## Q&A

- **Q:** What is the decided outcome for the remove-or-wire choice?
  **A:** Remove both unused match helpers. Do not wire the sequence-oriented
  trie helper into live masking. Move the older checks that still call the
  compiled-selector matcher onto the live mask decision so that matcher can
  go, and keep the segment checks production compile still needs. Live mask
  results stay the same.
- **Q:** Why remove the helpers instead of keeping them for a future caller?
  **A:** No production caller uses them. A second match path can drift from
  the fields redaction and the response viewer actually hide. The business
  need is one masking outcome, not a spare API.
- **Q:** Why move only those older checks, and not the rest of the PYPOST-1394
  suite or the PYPOST-1545 trie catalog?
  **A:** Those checks are the only reason the compiled-selector matcher still
  has a caller. Pointing them at the live mask decision is enough to drop
  the unused production method. A wider migration is a different ticket.
