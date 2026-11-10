# PYPOST-1543: Drop the unused compiled-rule list

## Goals

Response masking already decides hidden fields from indexed hierarchical
paths. A second stored copy of every compiled hierarchical rule is kept
beside that index. Steady-state matching never reads the copy. It exists so
a compile debug log can count compiled rules, and so the hierarchical
efficiency check can watch that private list.

That second copy costs a retained rule for every hierarchical hidden field
and invites the efficiency check to depend on a private list production
matching does not use. This debt item, recorded in
[PYPOST-1388 technical debt](ai-tasks/PYPOST-1388/60-tech-debt.md), exists so
maintainers keep one prepared form for hierarchical rules: the indexed
paths. The indexed-path count is already available as trie size. Duplicate
raw rules that collapse to one indexed path do not change which fields are
masked, so a second list length is not needed. Removing the copy must not
change which fields are masked.

**Implementation language:** Python

## User Stories

- As a **maintainer of response masking**, I want one prepared form for
  hierarchical hidden-field rules, so I am not keeping a second copy that
  matching never reads.
- As a **quality engineer**, I want the hierarchical efficiency check to
  use the indexed-path count and to stop touching the private compiled-rule
  list, so the lock survives without that list.
- As a **security reviewer**, I want the same selectors and document
  locations to stay masked or visible exactly as they are today, so this
  cleanup does not weaken hidden fields.
- As an **operator reading compile diagnostics**, I want the indexed-path
  count alone, so sizing does not depend on a list matching does not use.

## Definition of Done

This task is done when all of the following are true:

1. The duplicate stored list of compiled hierarchical rules is gone.
   Hierarchical rules are still prepared once into indexed paths.
2. The efficiency check that guards hierarchical lookup uses the
   indexed-path count (trie size) and does not expose the private
   compiled-rule list.
3. Compile diagnostics report that indexed-path count and do not depend on
   the length of a retained compiled-rule list.
4. For the same hidden-field rules and the same document location, live
   mask results are unchanged, including bare keys, dotted paths, array
   wildcards, shorthand matching, header rules ignored for body masking,
   and empty selector sets.
5. Redaction and the response viewer still hide the same fields.
6. The selector-engine developer guide does not describe a retained
   compiled-rule list as required for matching or for the efficiency check.

## Task Description

### Problem

A hidden-field catalog is prepared once. Bare names stay a fast membership
check. Hierarchical rules are indexed as paths, and steady-state matching
walks that index. It does not scan a stored list of compiled rules.

The product still retains that list. Inspection of production callers shows
two reads only: the compile debug log counts the list, and the hierarchical
efficiency check wraps the private list to see whether matching scans it.
No production mask, redact, or response-viewer path reads the stored rule
objects. The raw text kept on each compiled rule is unread. After a rule's
segments are indexed, the stored object is not needed for a later match.

The indexed-path count (trie size) already reports how many distinct
hierarchical paths were prepared. It can be smaller than the list length
when two raw rules index the same path. Those duplicates do not change
mask results. Debug sizing can use trie size only.

### Scope

- Remove the duplicate stored list of compiled hierarchical rules.
- Point the hierarchical efficiency check at the indexed-path count, and
  stop it from reading the private compiled-rule list.
- Compile diagnostics use that indexed-path count and no longer report a
  second length taken from the stored list.
- The developer guide stops treating the retained list as part of matching
  or of the efficiency check.
- Live mask results for current rules and locations stay the same.

### Out of Scope

- Remembering whether a document path contains a wildcard without scanning
  it ([PYPOST-1544](https://pypost.atlassian.net/browse/PYPOST-1544)).
- A new isolated trie catalog or wildcard fan-out stress suite
  ([PYPOST-1545](https://pypost.atlassian.net/browse/PYPOST-1545)).
- Removal of unused match helpers
  ([PYPOST-1542](https://pypost.atlassian.net/browse/PYPOST-1542)), which is
  already done.
- Changing how a single hierarchical rule is reduced to segments for
  indexing, or the existing checks that lock those segments.
- Any other follow-up in the PYPOST-1388 debt list.

### Functional Requirements

- **FR-1 — One prepared form for hierarchical rules**: Hierarchical
  hidden-field rules are prepared once into indexed paths. A second stored
  list of the compiled rule objects is not retained.
- **FR-2 — Efficiency check without the private list**: The check that
  hierarchical lookup stays bounded uses the indexed-path count (trie size).
  It does not expose or wrap the private compiled-rule list.
- **FR-3 — Diagnostics follow the index**: Compile diagnostics report the
  indexed-path count. They do not depend on the length of a retained
  compiled-rule list.
- **FR-4 — Same mask results**: For the same hidden-field rules and the
  same document location, a field that is masked today stays masked, and a
  field that is visible today stays visible.
- **FR-5 — Guide matches what remains**: A maintainer reading the selector
  engine guide does not find a retained compiled-rule list described as
  required for matching or for the efficiency check.

### Non-Functional Requirements

- **NFR-1 — No behavior change for callers**: Redaction and the response
  viewer keep the mask results they have today.
- **NFR-2 — No extra retained copy**: The work does not replace the stored
  list with another retained copy of each compiled rule.
- **NFR-3 — Existing live mask locks stay meaningful**: Checks that already
  lock live mask results continue to lock those results.

### Constraints and Assumptions

- Language for the change is Python.
- The source note is
  [PYPOST-1388 technical debt](ai-tasks/PYPOST-1388/60-tech-debt.md). The
  ticket is Debt, 2 points, parent context PYPOST-1388, and is a
  non-blocker.
- Inspection: production matching, redaction, and the response viewer do
  not read the stored compiled-rule list. The list is appended at compile
  and then used for a debug count and for the efficiency check. The
  indexed-path count is already reported as trie size.
- Segment compilation for the index stays. This ticket removes the
  duplicate retained list, not the ability to index a hierarchical rule.
- Sibling debts stay on their own tickets even if they touch the same
  engine.

## Main Entities and Interactions

- **Hidden-field rule**: A configured name or path whose matching values
  must be hidden. Attributes that matter here: whether it is a body rule,
  and whether it is hierarchical.
- **Indexed hierarchical path**: The prepared form matching already uses
  for a hierarchical rule. Its count is the trie size.
- **Compiled-rule list**: The extra stored copy of each compiled
  hierarchical rule. Matching does not read it. It is removed.
- **Live mask decision**: The yes-or-no answer production redaction and the
  response viewer already use. It stays the same.
- **Efficiency check**: The lock that hierarchical lookup does not grow
  with a scan of every compiled rule. It uses the indexed-path count and
  does not touch the private list.

Redaction and the response viewer ask the live mask decision. Maintainers
see the indexed-path count at compile time. They do not keep a second list
of compiled rules for that count or for the efficiency check.

## Q&A

- **Q:** Does production still need each stored compiled rule, or does that
  list exist only so a check or a debug log can count compiled rules?
  **A:** The stored list exists only for that efficiency check and that
  compile debug count. Production matching does not read the stored rule
  objects. The check uses trie size, the duplicate list is gone, and live
  mask results stay the same.
