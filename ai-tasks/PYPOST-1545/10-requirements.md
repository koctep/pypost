# PYPOST-1545: Isolated confidence for hierarchical path matching

## Goals

Response masking hides configured fields while a document is walked.
Hierarchical rules are prepared once into an index of distinct paths.
Today a developer sees that preparation mostly through end-to-end masking
locks: the same fields stay hidden, and a large set of exact paths stays
cheap to consider. Those locks can stay green while insert counting, an
empty index, a shorthand-only hit, or a wildcard-heavy catalog is never
stated on its own.

This debt item, recorded in
[PYPOST-1388 technical debt](ai-tasks/PYPOST-1388/60-tech-debt.md), is a
non-blocker coverage gap. The business need is that a developer can trust
four facts from one isolated catalog:

- Preparing the same hierarchical path more than once counts once, and the
  indexed count is the number of distinct complete paths.
- An empty hierarchical index misses every document location. An empty
  selector set leaves every field visible. Bare-name rules still hide
  fields when the hierarchical index is empty.
- A shorthand-only walk is visible on its own: the direct look leaves the
  field visible, and the shorthand look hides it.
- A wildcard-heavy catalog hides a field those rules hide and leaves
  visible a field those rules leave visible.

The catalog complements the existing PYPOST-1388 semantic and efficiency
locks. It does not replace them. Which fields are masked stays the same.

**Implementation language:** Python

## User Stories

- As a **maintainer of response masking**, I want one isolated catalog for
  insert dedupe, indexed size, an empty index, and shorthand-only walks, so
  I can trust those facts without reading only the end-to-end masking locks.
- As a **quality engineer**, I want the direct path-and-key decision and the
  public mask check to agree wherever that public check is the path-and-key
  decision, so a removed combined-token helper is not required to see the
  agreement.
- As a **quality engineer**, I want a wildcard-heavy rule set to hide a
  field those rules hide and leave visible a field those rules leave
  visible.
- As a **security reviewer**, I want today's mask results to stay the same,
  and I want removed match helpers to stay removed, so this catalog does not
  add a second way to decide a hidden field.

## Definition of Done

This task is done when all of the following are true:

1. An isolated catalog shows that preparing the same hierarchical path more
   than once counts as one path, that a different complete path counts
   again even when the two paths share a prefix, and that the indexed count
   is zero when no hierarchical path has been prepared.
2. The same catalog shows that an empty index answers no for every document
   location.
3. The same catalog shows a shorthand-only walk: the direct path-and-key
   decision leaves the field visible, the shorthand decision hides it, and
   the public mask check hides it because the location contains a wildcard.
4. The same catalog shows that the path-and-key decision and the public
   mask check give the same yes or no for hierarchical rules on locations
   where that public check is the path-and-key decision.
5. The same catalog shows a wildcard-heavy rule set. A location those
   rules hide stays hidden. A location those rules leave visible stays
   visible.
6. The removed combined-token trie helper and the removed compiled-selector
   matcher stay absent. No new public match question is added.
7. For the same hidden-field rules and the same document location, a field
   that is masked today stays masked, and a field that is visible today
   stays visible.
8. The existing PYPOST-1388 semantic locks and the efficiency lock over
   many distinct exact paths still guard the outcomes they guard today.

## Task Description

### Problem

A developer must be able to trust an isolated catalog of hidden-field
outcomes. Hierarchical rules are prepared into an index of distinct
complete paths. The catalog states, on their own, the indexed count, an
empty hierarchical index, a shorthand-only case, agreement of the
path-and-key decision with the public mask check, and the yes-or-no of a
wildcard-heavy catalog.

Callers of the public mask check are response redaction and the response
viewer. End-to-end locks already freeze their results, including shorthand
and a large catalog of distinct exact paths. They do not isolate the index:

- A repeated hierarchical path must not inflate the indexed count. A shared
  prefix of two different complete paths must still count as two paths.
  The count is zero before any hierarchical path is prepared.
- With nothing prepared, the index matches no location.
- A shorthand-only case is easy to miss inside a full mask fixture. The
  direct look says no. Ignoring wildcard segments in the location says
  yes. The public mask check follows that yes when a wildcard is present.
- The efficiency lock uses many distinct exact paths. It does not lock a
  wildcard-heavy catalog on its own. That catalog must hide a field those
  rules hide and leave visible a field those rules leave visible.

The source note also asked for equivalence between a combined-token walk
and the path-and-key walk. That combined-token helper, and the compiled
selector matcher beside it, were removed by PYPOST-1542. Nothing in
production calls them. The agreement a developer still needs is the
remaining walk: the path-and-key decision, and the public mask check on
locations where that check is the path-and-key decision.

### Scope

- One isolated catalog a developer can read for the index facts below.
- Insert dedupe and indexed size for hierarchical paths.
- An empty index, including a count of zero and no hierarchical match.
- A shorthand-only walk, including agreement of the public mask check when
  the location contains a wildcard.
- Agreement between the path-and-key decision and the public mask check
  where the public check is that path-and-key decision.
- A wildcard-heavy catalog, with one location the rules hide and one
  location they leave visible.
- Today's mask results, and the absence of the removed match helpers.

### Out of Scope

- Restoring `PathSelectorTrie.matches_tokens` or
  `CompiledPathSelector.matches`.
- Adding a new public way to ask whether a field is hidden.
- Changing which fields are masked, which locations use shorthand, or how
  bare names and header rules are treated.
- A new shape for the index. The wildcard-heavy catalog locks today's
  yes-or-no.
- Replacing or weakening the PYPOST-1388 semantic locks or the efficiency
  lock over many distinct exact paths.
- Any other follow-up in the PYPOST-1388 debt list.

### Functional Requirements

- **FR-1 — Distinct indexed count**: Preparing one hierarchical path twice
  leaves the indexed count at one. Preparing two complete paths that share
  a prefix leaves the indexed count at two. Before any hierarchical path
  is prepared, the indexed count is zero.
- **FR-2 — Empty index**: When no hierarchical path is prepared, every
  document location is a hierarchical miss. When the selector set itself
  is empty, the public mask check leaves every field visible.
- **FR-3 — Shorthand-only walk**: The catalog includes this case. The rule
  is `items.secret`. The location is `items`, then an array wildcard, then
  the field `secret`. The direct path-and-key decision leaves the field
  visible. The shorthand decision hides it. The public mask check hides
  it. When the only hierarchical rule is `items.secret`, the field
  `secret` at `other` stays visible. A rule the direct decision already
  hides, such as `items.*.secret` at that wildcard location, is a direct
  hit and is not this shorthand-only case.
- **FR-4 — Path-and-key agrees with the public check**: Where the public
  mask check is decided by the path-and-key walk, the isolated path-and-key
  answer and the public mask check are the same yes or no. Covered
  examples: rule `user.apiKey` at location `user` / `apiKey` is yes for
  both; the same rule at `user` / `name` is no for both. A bare-name rule
  and a hierarchical rule are separate catalog cases. A shorthand-only hit
  is outside this agreement and is covered by FR-3.
- **FR-5 — Wildcard-heavy catalog**: The catalog includes a rule set whose
  segments are mostly wildcards. A location those rules hide is hidden. A
  location those rules leave visible stays visible. The answer is the
  yes-or-no those rules already require.
- **FR-6 — Same live decision**: Production masking still decides a field
  through the public mask check. The removed combined-token helper and the
  removed compiled-selector matcher stay absent. No new public match
  question is added. Mask results stay the results of today.

### Non-Functional Requirements

- **NFR-1 — No behavior change for callers**: Redaction and the response
  viewer keep the mask results they have today. This catalog does not
  require a faster or slower match.
- **NFR-2 — Catalog beside the end-to-end locks**: The isolated catalog is
  additional confidence. The PYPOST-1388 semantic locks and the efficiency
  lock over many distinct exact paths keep their current meaning.
- **NFR-3 — Wildcard-heavy catalog is a correctness lock**: The
  wildcard-heavy case exists so a developer can trust the yes-or-no those
  rules already require. It sets no new speed or memory target.
- **NFR-4 — Bounded checks**: Each new check carries an explicit time bound,
  consistent with existing selector checks.

### Constraints and Assumptions

- Language for the change is Python.
- The source note is
  [PYPOST-1388 technical debt](ai-tasks/PYPOST-1388/60-tech-debt.md). The
  ticket is Debt, Low, 3 points, parent context PYPOST-1388, and is a
  non-blocker. It complements the PYPOST-1388 semantic and efficiency
  locks.
- Current code, after PYPOST-1542: `PathSelectorTrie.matches_tokens` and
  `CompiledPathSelector.matches` are gone. They have no production callers
  and stay gone. This ticket does not add a public match question and does
  not change mask results.
- This ticket locks the existing shorthand-only case in the isolated
  catalog. It does not change when a shorthand decision applies.
- Sibling debts stay on their own tickets even if they touch the same
  engine.

## Main Entities and Interactions

- **Hidden-field rule**: A configured name or path whose matching values
  must be hidden. Attributes that matter here: whether it is hierarchical,
  whether its segments are exact or wildcards, and whether a repeated
  preparation is the same complete path.
- **Hierarchical path index**: The prepared set of distinct complete
  hierarchical paths. Its indexed count is how many of those paths are
  present. An empty index has a count of zero and matches no location.
- **Document location**: Where a field sits while a payload is considered
  (ancestor segments plus the field name). A wildcard segment means the
  field is inside an array.
- **Path-and-key decision**: The direct yes-or-no for that location against
  the index.
- **Shorthand decision**: The yes-or-no after wildcard segments in the
  location are ignored. It matters for a shorthand-only walk, where the
  direct decision said no.
- **Public mask check**: The yes-or-no redaction and the response viewer
  already use. On a hierarchical path-and-key decision it agrees with the
  path-and-key answer. On a shorthand-only walk it agrees with the
  shorthand answer when a wildcard is present.
- **Wildcard-heavy catalog**: Many hierarchical rules whose segments are
  mostly wildcards. For a document location, the catalog locks the
  yes-or-no those rules already require.
- **Removed match helper**: A match question production does not call. The
  combined-token trie helper and the compiled-selector matcher are already
  removed and stay removed.

A developer reads the isolated catalog and sees indexed count, empty-index
misses, shorthand-only walks, path-and-key agreement with the public mask
check, and the wildcard-heavy yes-or-no. Redaction and the response viewer
keep asking the public mask check. They do not gain a new question, and
the removed helpers do not return.

## Q&A

- **Q:** The source note asks for equivalence with the removed
  combined-token helper. Should that helper be restored so two walks can
  be compared?
  **A:** No. PYPOST-1542 removed `PathSelectorTrie.matches_tokens` and
  `CompiledPathSelector.matches`. They have no production callers and must
  not be restored. The agreement a developer still needs is the
  path-and-key decision and the public mask check, on locations where that
  check is the path-and-key decision. Shorthand-only walks stay a separate
  catalog case, because there the public check follows the shorthand
  decision. Do not add a new public match question. Do not change mask
  results.
- **Q:** Does a wildcard-heavy catalog mean a faster match or a new index
  shape?
  **A:** No. It means a developer can trust the yes-or-no those rules
  already require. A field they hide stays hidden, and a field they leave
  visible stays visible. Mask results stay as they are. A different index
  shape is out of scope.
- **Q:** Do the existing end-to-end masking locks go away once the isolated
  catalog exists?
  **A:** No. They stay, including the efficiency lock over many distinct
  exact paths. The catalog adds the index facts those locks do not state
  on their own.
