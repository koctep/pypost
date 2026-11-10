# PYPOST-1544: Know wildcard presence from the breadcrumb

## Goals

Response masking walks a document and decides which fields stay hidden.
When a hierarchical rule misses, matching scans every segment of the current
location to learn whether a wildcard is present, and only then considers a
shorthand match. A wildcard segment is placed on the location when the walk
pushes the breadcrumb and is removed when that segment is popped. The scan
repeats a fact the walk already established.

This debt item, recorded in
[PYPOST-1388 technical debt](ai-tasks/PYPOST-1388/60-tech-debt.md), is a
non-blocker micro-optimization. Typical document depths make the scan cheap
today. The decided outcome is still that wildcard presence is known from
push and pop of the breadcrumb, so a hierarchical miss does not scan the
location again before the shorthand decision. Which fields are masked stays
the same.

**Implementation language:** Python

## User Stories

- As a **maintainer of response masking**, I want wildcard presence on the
  current location to stay current as the breadcrumb is pushed and popped,
  so a hierarchical miss does not scan that location before the shorthand
  decision.
- As a **security reviewer**, I want the same selectors and document
  locations to stay masked or visible exactly as they are today, so this
  change does not weaken hidden fields.
- As a **quality engineer**, I want existing live mask checks to keep
  locking today's results, including a shorthand hit when a wildcard is
  present and a miss when none is present.

## Definition of Done

This task is done when all of the following are true:

1. During a masking walk, whether the current location contains a wildcard
   is the presence known from breadcrumb push and pop.
2. A hierarchical miss uses that known presence. It does not scan every
   segment of the location to discover a wildcard before the shorthand
   decision.
3. For the same hidden-field rules and the same document location, a field
   that is masked today stays masked, and a field that is visible today
   stays visible.
4. Shorthand matching is still considered only when a wildcard is present,
   and is still not considered when none is present.
5. Redaction and the response viewer still hide the same fields.

## Task Description

### Problem

Hidden-field matching answers a live yes-or-no question for a field at a
document location. Bare names stay a fast membership check. Hierarchical
rules are answered by a first look at the location. When that look misses,
matching may still hide the field by a shorthand match, and only when the
location contains a wildcard.

Inspection of that live decision shows one full pass over the current
location, looking for a wildcard segment, immediately before the shorthand
walk. The pass runs on a hierarchical miss.

The production walks that pay for it are redaction and the response viewer.
Each keeps one breadcrumb for the current location. Descent pushes a
segment. Return pops that segment. Entering a list pushes a wildcard.
Entering an object pushes the field name, and that name can itself be a
wildcard. Either way, the location contains a wildcard, or it does not,
at the moment of the push, and the opposite update happens at the pop.
The full pass rediscovers that fact on every hierarchical miss.

### Scope

- Wildcard presence for the current masking location is known from
  breadcrumb push and pop.
- A hierarchical miss uses that known presence and does not scan the
  location for a wildcard before the shorthand decision.
- Redaction and the response viewer keep the mask results they have today,
  including shorthand hits and shorthand misses.

### Out of Scope

- A new isolated trie catalog or wildcard fan-out stress suite
  ([PYPOST-1545](https://pypost.atlassian.net/browse/PYPOST-1545)).
- Changing when a shorthand match is attempted, or removing that second
  look. It still runs only when a wildcard is present and the first
  hierarchical look missed.
- Leaving the full-location scan in place because typical depths are cheap.
- Any other follow-up in the PYPOST-1388 debt list.

### Functional Requirements

- **FR-1 — Presence from push and pop**: While a masking walk is in
  progress, whether the current location contains a wildcard is the fact
  established when a breadcrumb segment is pushed and updated when that
  segment is popped. A list wildcard and an object key that is a wildcard
  both count.
- **FR-2 — No repeated scan on a hierarchical miss**: A hierarchical miss
  does not scan every segment of the location to learn that fact before
  deciding whether a shorthand match is needed.
- **FR-3 — Same mask results**: For the same hidden-field rules and the
  same document location, a field that is masked today stays masked, and a
  field that is visible today stays visible. That includes bare keys,
  dotted paths, array wildcards, shorthand matching, header rules ignored
  for body masking, and empty selector sets.
- **FR-4 — Same shorthand condition**: A shorthand match is still considered
  only when the current location contains a wildcard, and is still not
  considered when it does not.

### Non-Functional Requirements

- **NFR-1 — No behavior change for callers**: Redaction and the response
  viewer keep the mask results they have today.
- **NFR-2 — In scope despite low cost**: The scan is cheap at typical
  depths and the item is a non-blocker. The outcome is still known
  presence from push and pop, not a decision to skip the work.
- **NFR-3 — Existing live mask locks stay meaningful**: Checks that already
  lock live mask results continue to lock those results.

### Constraints and Assumptions

- Language for the change is Python.
- The source note is
  [PYPOST-1388 technical debt](ai-tasks/PYPOST-1388/60-tech-debt.md). The
  ticket is Debt, 1 point, parent context PYPOST-1388, and is a
  non-blocker.
- Inspection: the wildcard scan sits in the live mask decision, after the
  first hierarchical look misses and before the shorthand walk. Redaction
  and the response viewer are the production walks that push and pop the
  breadcrumb those decisions use.
- A one-shot question about a location that already contains a wildcard, or
  that does not, keeps today's yes-or-no answer. This ticket does not
  change which locations are masked.
- Sibling debts stay on their own tickets even if they touch the same
  engine.

## Main Entities and Interactions

- **Hidden-field rule**: A configured name or path whose matching values
  must be hidden. Attributes that matter here: whether it is a body rule,
  and whether a shorthand match can hide a field the first hierarchical
  look missed.
- **Masking location**: The breadcrumb of the field currently under
  consideration. Segments are pushed on descent and popped on return.
- **Wildcard presence**: Whether that location currently contains a
  wildcard segment. It is known from those push and pop steps.
- **Hierarchical miss**: The first look did not hide the field. Only then
  is shorthand considered, and only when wildcard presence is known.
- **Live mask decision**: The yes-or-no answer redaction and the response
  viewer already use. It stays the same.

Redaction and the response viewer walk a document, push and pop the
breadcrumb, and ask the live mask decision. A hierarchical miss reads the
presence those steps already know. It does not scan the location again to
learn whether a shorthand match is allowed.

## Q&A

- **Q:** Should this scan stay because typical depths make it cheap, or is
  wildcard presence known from push and pop of the breadcrumb?
  **A:** Wildcard presence is known from push and pop of the breadcrumb,
  and which fields are masked stays the same.
