# PYPOST-971: Technical Debt Analysis

**Verdict:** SAFE TO CLOSE

Acceptance met: one shared DisplayRole exact-match policy
(`display_role_equals`) and one flat sibling scan
(`find_child_index_by_display_text`) live in `pypost/agent/tree_index.py`;
flat `_select_item_view` and recursive tree lookup both consume that policy;
public errors, logging, and dispatch are unchanged. Focused ownership,
`ui_actions`, and tree-walk suites are green. Step 8 still needs the normal
developer-doc ownership wording update before the overall task can close.

**Do not create Jira issues in this step** (Phase D / tech-debt sync later).

## Review Scope

Reviewed task artifacts and the task-owned diff:

- `pypost/agent/tree_index.py`
- `pypost/agent/ui_actions.py`
- `tests/test_display_role_scan_ownership.py`
- `ai-tasks/PYPOST-971/` (`10-requirements`, `20-architecture`,
  `40-code-cleanup`, `50-observability`, `00-roadmap`)

Also checked `doc/dev/ui_actions.md` for Step 8 readiness (ownership wording
still describes flat scan without naming the shared helpers).

## Requirements and Architecture Review

| Requirement | Evidence | Verdict |
| --- | --- | --- |
| FR-1 / AC-1 shared ownership | Match + flat scan in `tree_index`; AST marker | Met |
| FR-2 flat root-only | `find_child_index_by_display_text` walks direct children only | Met |
| FR-3 tree DFS | DFS retained; compares via `display_role_equals` | Met |
| FR-4 selection / expand | Side effects stay in `_select_item_view` / `_select_tree` | Met |
| FR-5–FR-8 errors / dispatch | Boundaries and integer paths unchanged | Met |
| FR-9 suites green | 37 focused tests passed (Step 7) | Met |
| FR-10 docs | Deferred to Step 8 (planned, not debt) | Pending Step 8 |
| NFR-2 maintainability | One predicate implementation | Met |
| NFR-3 performance | Same O(root rows) / DFS shape | Met |
| NFR-5/6 observability/privacy | No new logs; helpers have no logger | Met |

No architecture deviation. Flat views do not recurse; tree DFS does not switch
to siblings-first via `find_child_index_by_display_text`; combo / `QListWidget`
/ integer paths were left alone.

## Shortcuts Taken

None that are temporary crutches. Intentional, accepted design choices:

- **Helpers live in `tree_index.py`** — Reuses the PYPOST-941 DisplayRole lookup
  home rather than adding a new `model_index` module (architecture Option
  selected).
- **Tree DFS does not call the flat finder** — Calling
  `find_child_index_by_display_text` then recurse would change duplicate-label
  first-match order. Tree shares only `display_role_equals`.
- **AST convention marker instead of a broken runtime select** — Runtime
  selection was already correct; ownership is locked structurally (same pattern
  as PYPOST-970).
- **Dev docs deferred to Step 8** — Planned workflow step; not Step 7 debt.

## Code Quality Issues

None material.

- Shared match policy has a single implementation (`display_role_equals`).
- Flat text branch in `_select_item_view` delegates without inline
  `DisplayRole`.
- Module name `tree_index` for flat callers is a discoverability trade-off
  already accepted in architecture; Step 8 docs should name the helpers
  explicitly.
- Sibling-loop structure remains duplicated between the flat finder and tree
  `_walk` by design (traversal strategy must stay distinct).
- No new hardcoded timeouts, magic strings, or debug prints.

## Missing Tests

No blocker. Explicit timeout markers are present.

| Contract | Coverage |
| --- | --- |
| Shared match + flat scan ownership | `test_display_role_scan_ownership.py` (AST) |
| Flat QListView text / index | `tests/test_ui_actions.py` |
| Tree text / nested / index / errors | `test_ui_actions.py`, `test_tree_index_walk.py` |
| Combo / `QListWidget` regression | `test_ui_actions.py` |
| Caplog scalar `ui_action_applied` | Existing fill/select caplog tests |
| Timeout markers | Ownership module `timeout(10)`; existing suites retain theirs |
| Flat finder itself calls `display_role_equals` | Not asserted by AST marker (TD-1) |
| Dedicated item-view no-model test | Already tracked as PYPOST-972 |

Timeout-marker review: **no blocker** under `.cursor/lsr/do-testing.md`.

## Performance Concerns

None.

- Flat selection remains linear in root-row count.
- Tree lookup retains the existing depth-first walk (no extra traversal).
- AST marker has no GUI, socket, or network dependency.

## Observability, Diagnostics, and Privacy

Step 6 decision confirmed: no new production logs or metrics. Successful
`ui_select` still emits scalar-only `ui_action_applied`. Shared helpers do not
log option text or DisplayRole values. Public miss / missing-model reasons are
unchanged.

## Deviations from Architecture

None.

Delivered interfaces match the Step 2 plan:

- `display_role_equals(index, text) -> bool`
- `find_child_index_by_display_text(model, text, parent=None) -> QModelIndex | None`
- Tree DFS wires match only; flat item-view text branch delegates scan
- Dependency direction: `ui_actions` → `tree_index`; no reverse import

## Follow-up Tasks

Concrete Debt candidates for a later sync. **No Jira browse links yet**
(orchestrator tickets in Phase D). Leave links pending unless already tracked.

### Already tracked (do not reticket)

| Area | Owner |
| --- | --- |
| Dedicated `item view has no model` test | [PYPOST-972](https://pypost.atlassian.net/browse/PYPOST-972) (PYPOST-939 TD-2) |
| Flat DisplayRole scan sharing (this ticket) | Resolved by PYPOST-971 (was PYPOST-939 TD-1) |

### TD-1 — Low (optional)

- **Item:** Strengthen
  `tests/test_display_role_scan_ownership.py` so
  `find_child_index_by_display_text` must call `display_role_equals` (and
  optionally assert both helpers appear in `__all__`).
- **Notes:** Today the marker proves tree DFS uses the match helper and flat
  `_select_item_view` uses the flat finder, but the flat finder could re-inline
  `DisplayRole` without failing the marker. Low value; source is currently
  correct.
- **Priority:** Low
- **Jira:** [PYPOST-1041](https://pypost.atlassian.net/browse/PYPOST-1041)

### Accepted / out of scope (do not ticket)

- Multi-column `QTableView` selection semantics.
- Recursing flat item views or flattening tree traversal.
- Changing combo / `QListWidget` / integer selection paths.
- Renaming `tree_index.py` solely for flat-scan discoverability.
- Step 8 `doc/dev/ui_actions.md` ownership wording (planned workflow step).

## Blocker Review

| Check | Result |
| --- | --- |
| Temporary solutions / crutches | None |
| Missing tests with timeout markers | **None** — ownership `timeout(10)` |
| Deviations from architecture | None |
| Acceptance gaps | **None** (docs → Step 8) |
| Merge / release blocker debt | **None** |

**SAFE TO CLOSE** for this story’s core DoD (shared DisplayRole ownership).
Optional TD-1 is non-blocking.

## Validation Evidence

| Check | Result |
| --- | --- |
| Focused suites (Step 7) | 37 passed in 1.54s |
| Ownership AST marker | Passed |
| `tests/test_ui_actions.py` | Passed (incl. list view / tree / combo) |
| `tests/test_tree_index_walk.py` | Passed |
| Step 5 lint / cleanup | Clean (`40-code-cleanup.md`) |
| Step 6 observability | No-new-log decision documented |

## Documentation Review

User documentation is not applicable (harness ownership only). Canonical
developer docs in `doc/dev/ui_actions.md` still describe flat column-0 scan vs
recursive tree without naming `display_role_equals` /
`find_child_index_by_display_text`. That update belongs to **Step 8**, not a
tech-debt ticket.
