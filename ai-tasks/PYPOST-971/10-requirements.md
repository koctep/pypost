# PYPOST-971: Share flat DisplayRole scan ownership

## Goals

PYPOST-939 added model-backed flat list selection to the agent `ui_select` capability. Its
column-0 display-text lookup overlaps with the lookup policy already used by tree selection,
leaving more than one place for the same row matching rules to evolve.

The business goal is to reduce maintenance and regression risk by giving the common flat row
scan one source of truth while preserving every existing list-view and tree outcome. Agent and
end-to-end authors should observe no change in how they select controls; maintainers should be
able to update shared DisplayRole matching policy once instead of reconciling duplicate logic.

This is the Low-priority, 2-story-point Debt follow-up recorded as TD-1 in PYPOST-939.

## Programming Language

Python with PySide6. Task artifacts and developer documentation use English Markdown.

## User Stories

- As a **maintainer**, I want flat column-0 DisplayRole scanning to have one ownership point so
  list and tree selection rules cannot drift.
- As an **agent or e2e author**, I want existing text selection to return the same visible row so
  maintenance refactoring does not change scenario behavior.
- As a **CI owner**, I want existing `ui_select` and tree-lookup coverage to remain green so the
  consolidation cannot weaken supported selection paths.
- As a **failure-triage owner**, I want missing-model and missing-option errors to retain their
  established public messages and exception boundaries.

## Task Description

### Problem

The model-backed item-view path introduced by PYPOST-939 performs a flat scan of root rows in
column 0 and compares each row's DisplayRole with the requested text. Tree selection also relies
on the same column-0 DisplayRole matching rule while adding recursive traversal for descendants.
The overlap is small but creates duplicate policy ownership and a future drift point.

### Business Reason

Selection behavior is foundational test-harness infrastructure. A single shared matching policy
reduces repeated maintenance, keeps flat and tree callers consistent where their behavior is
meant to overlap, and makes future changes safer without expanding the user-facing capability.

### In Scope

- Establish one shared ownership point for flat, column-0 DisplayRole row matching used by the
  model-backed item-view and tree-selection paths.
- Preserve flat item-view root-row behavior and recursive tree behavior.
- Preserve existing public selection, failure, and logging outcomes.
- Retain or strengthen automated proof for the existing flat item-view and tree contracts.
- Update canonical developer documentation if ownership details change.

### Exclusions

- Adding a new widget type or new `ui_select` capability.
- Changing combo-box or `QListWidget` selection behavior.
- Changing integer/index selection or its top-level tree semantics.
- Flattening recursive tree traversal or adding recursion to flat item views.
- Changing duplicate-label first-match behavior, case sensitivity, or DisplayRole string
  conversion.
- Adding multi-column `QTableView` selection semantics.
- Replacing viewport click helpers used to open or activate tree rows.
- Changing production UI widgets, widget identities, public agent APIs, logs, or metrics.
- Unrelated cleanup or missing-test debt outside the shared scan contract.

## Functional Requirements

- **FR-1:** Flat model-backed item views and tree text selection must use one shared source of
  truth for matching root-level, column-0 DisplayRole values.
- **FR-2:** Flat item-view text selection must continue to inspect only root rows in column 0 and
  select the first exact display-text match.
- **FR-3:** Tree text selection must continue to find nested rows using its current depth-first
  behavior while applying the shared matching policy at each sibling level.
- **FR-4:** A matched flat item-view or tree row must remain the current selection; a nested tree
  row's parent must retain the existing expansion behavior.
- **FR-5:** Missing text must continue to raise the established
  `UiTargetNotInteractableError` with an `option not found` reason at the `ui_select` boundary.
- **FR-6:** A tree lookup used by the e2e click helper must retain its existing success result and
  caller-specific missing-row error behavior.
- **FR-7:** Missing-model handling must remain distinct for item views and trees, including their
  existing public error reasons.
- **FR-8:** Integer selection, out-of-range errors, widget dispatch order, and unsupported-widget
  errors must remain unchanged.
- **FR-9:** Existing `ui_select` tests and shared tree-lookup tests must pass after the ownership
  consolidation.
- **FR-10:** Developer guidance must continue to describe flat versus recursive selection
  semantics accurately.

## Non-Functional Requirements

- **NFR-1 — Compatibility:** The work must be behavior-preserving for all existing callers and
  public exception types/messages.
- **NFR-2 — Maintainability:** The common flat scan must have one implementation policy rather
  than parallel matching loops.
- **NFR-3 — Performance:** Flat selection must remain linear in root-row count, and recursive
  tree lookup must not add traversal beyond its existing depth-first search.
- **NFR-4 — Stability:** Automated Qt checks must remain deterministic, offscreen, bounded by
  explicit pytest timeouts, and independent of live network services.
- **NFR-5 — Observability:** Successful selection must retain the existing scalar-only
  `ui_action_applied` event; option payloads must not be newly logged.
- **NFR-6 — Security and privacy:** The refactoring must not expand captured or emitted model
  data beyond the existing comparison and error behavior.
- **NFR-7 — Scope control:** No production UI, fixture lifecycle, public API, or unrelated helper
  behavior may change.

## Acceptance Criteria

- **AC-1:** A shared scan capability owns root-level column-0 DisplayRole matching for both the
  flat item-view and tree-selection paths.
- **AC-2:** Existing QListView text and index selection tests remain green.
- **AC-3:** Existing tree text, nested lookup, index, and caller-specific error tests remain
  green, and matched-parent expansion behavior remains unchanged.
- **AC-4:** Missing option, missing model, and out-of-range behavior remains unchanged at public
  boundaries.
- **AC-5:** Combo-box and `QListWidget` selection tests remain green.
- **AC-6:** The focused `tests/test_ui_actions.py` selection coverage and
  `tests/test_tree_index_walk.py` pass with explicit timeout protection.
- **AC-7:** No user-visible product behavior, public interface, logging schema, or metric changes.
- **AC-8:** Canonical developer documentation remains accurate about shared matching ownership
  and flat-versus-recursive semantics.

## Constraints and Assumptions

- PYPOST-939's flat model-backed selection and PYPOST-941's shared recursive tree lookup are the
  accepted behavioral baselines.
- Display text is matched exactly after the existing string conversion; duplicate labels select
  the first match in traversal order.
- Flat model-backed views use root rows and column 0. Trees may contain arbitrary depth.
- `QListWidget` remains on its widget-item API and is not part of model scan sharing.
- Tree e2e click helpers and `ui_select` intentionally expose different errors on a miss.
- The work is maintenance debt, not a request for new user-facing capability.
- Step 1 is documentation-only and remains pending review.

## Main Entities and Interactions

| Entity | Business role | Required outcome |
| --- | --- | --- |
| Agent or e2e caller | Requests selection by visible text | Sees unchanged selection |
| Flat model-backed view | Presents root rows | First matching row remains selected |
| Tree view | Presents root and nested rows | Depth-first match remains selected |
| Display text | Human-visible row label | Exact column-0 matching remains stable |
| Shared matching policy | Common maintenance ownership | Prevents list/tree drift |
| Selection boundary | Maps lookup outcome to agent behavior | Preserves public errors and logs |
| CI coverage | Guards supported selection paths | Detects behavioral regression |

Interaction overview:

1. A caller names a supported control and visible option.
2. The selection path inspects column-0 display labels in the path's established order.
3. The first exact match becomes current, with tree parent expansion preserved when applicable.
4. A miss or invalid state remains mapped to the caller's established error contract.
5. CI proves flat item-view, recursive tree, and unaffected selection paths remain compatible.

## Evidence and Traceability

| Evidence | Current observation | Requirement impact |
| --- | --- | --- |
| PYPOST-939 TD-1 | Records Low debt for sharing the flat DisplayRole scan | Goal, FR-1 |
| `ui_actions.py` flat path | Scans root rows, column 0, first exact match | FR-2, FR-5 |
| `pypost/agent/tree_index.py` | Tree lookup is recursive depth-first on column 0 | FR-3, FR-6 |
| `pypost/agent/ui_actions.py::_select_tree` | Expands a matched nested parent | FR-4 |
| `tests/test_ui_actions.py` | Covers list/tree text, index, and errors | FR-7–FR-9 |
| `tests/test_tree_index_walk.py` | Covers deep lookup, miss, error boundaries | FR-3, FR-6 |
| `doc/dev/ui_actions.md` | Documents flat scan and recursive tree behavior | FR-10 |
| Git history | PYPOST-939 added flat view; PYPOST-941 centralized tree lookup | Baseline scope |

## Risks

| Risk | Consequence | Requirement guard |
| --- | --- | --- |
| Flat and recursive semantics merge | List views recurse or trees stop early | FR-2, FR-3 |
| Traversal order changes | Duplicate text selects a different row | FR-2, FR-3 |
| Invalid model indexes are handled differently | Selection or error regression | FR-4, FR-7 |
| Error mapping moves into common policy | Public caller errors drift | FR-5–FR-8 |
| Integer path is swept into the refactor | Out-of-range behavior changes | FR-8 |
| Shared ownership adds more traversal | Slower test harness behavior | NFR-3 |
| New diagnostic data is logged | Fixture values leak into CI output | NFR-5, NFR-6 |

## Definition of Done

- All acceptance criteria are satisfied.
- The common flat DisplayRole scan has one ownership point.
- Existing selection behavior and error contracts remain unchanged.
- Focused selection and tree-lookup suites pass under explicit timeouts.
- Developer documentation reflects the final ownership without implying new capability.
- No unrelated behavior, production UI, public API, logging, or metric change is included.

## Q&A

- **Q: Why consolidate code that already works?**
  **A:** Duplicate matching policy can drift and requires repeated maintenance. The dedicated debt
  ticket resolves that ownership risk while preserving behavior.
- **Q: Should flat item views gain recursive selection?**
  **A:** No. Flat root-row semantics remain distinct from recursive tree traversal.
- **Q: Does this change index selection?**
  **A:** No. The debt concerns display-text scanning only.
- **Q: Should tree click helpers be replaced with `ui_select`?**
  **A:** No. Selection and viewport activation have different business purposes and remain
  separate.
- **Q: Why does the source debt mention tree helpers in `ui_actions.py` when tree lookup is now
  shared elsewhere?**
  **A:** PYPOST-941 subsequently centralized recursive tree lookup. PYPOST-971 follows the
  original debt's ownership goal against the current baseline without undoing PYPOST-941.
- **Q: Does the task add a new supported widget?**
  **A:** No. It consolidates maintenance ownership for existing behavior.
