# PYPOST-388: Architecture — tree state test coverage

## Research

Tree state flows through two layers:

1. **StateManager** (`pypost/core/state_manager.py`) — reads/writes `expanded_collections` in
   `AppSettings` via `ConfigManager`.
2. **CollectionsPresenter** (`pypost/ui/presenters/collections_presenter.py`) — connects
   `QTreeView` expand/collapse signals to StateManager and applies saved ids in
   `restore_tree_state()` after model rebuild.

Existing tests:

| Module | Tests |
|--------|-------|
| `tests/test_settings_persistence.py` | `test_set_expanded_collections_persists`, noop save |
| `tests/test_collections_presenter.py` | expand/collapse handlers, restore, round-trip reload |

## Implementation Plan

1. Confirm presenter tests exercise `_on_tree_expanded`, `_on_tree_collapsed`,
   `restore_tree_state`, and QWidget `expand` → signal → state path.
2. Document covered scenarios in `doc/dev/collection_tree_actions.md`.
3. Add PYPOST-388 references to primary round-trip test docstring.
4. Mark PYPOST-8 tech-debt item resolved.

No production code changes required — coverage already landed via PYPOST-92; this task
formalizes PYPOST-8 closure.

## Q&A

- **Q:** Fake vs real StateManager in presenter tests? **A:** `FakeStateManager` in presenter
  tests is sufficient for UI/state integration; real persistence stays in
  `test_settings_persistence.py`.
