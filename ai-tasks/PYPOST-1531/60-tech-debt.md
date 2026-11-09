# PYPOST-1531: Technical Debt Analysis

## Shortcuts Taken

1. **Instance-level `QMenu.exec` stand-in.**
   Context-menu tests keep the real `contextMenuEvent` and the actions it
   creates. A class-level patch of `QMenu.exec` does not run under Shiboken:
   the binding resolves `exec` on the instance, the class patch never handles
   the call, and the real modal menu would block the test. `_dispatch_menu`
   patches `QMenu.__init__` and assigns `exec` on that instance. The chooser
   checks the live action titles and enabled state, then returns Add
   Selector, Remove Selected, or cancellation. This is the modal-menu
   substitution the architecture requires. It remains a shortcut because the
   modal loop never runs, and the Shiboken constraint lives only in this
   helper.

2. **Single `processEvents` flush after Return.**
   The add-and-commit test types into the real editor and sends Return.
   Commit and `closeEditor` are queued so the editor is not destroyed while
   the key event is still on the stack. The test then calls
   `QCoreApplication.processEvents()` once. That call processes the current
   queue and returns. It remains a shortcut because the saved-list assertion
   assumes this one flush is enough to apply the committed selector.

No further shortcut was taken. Production modules are unchanged. Tests send
`QTest` key events and a `QContextMenuEvent`. They do not call
`keyPressEvent`, `contextMenuEvent`, or the removal helpers. That is the
accepted architecture. No architecture deviation.

## Code Quality Issues

No code-quality debt beyond the two shortcuts above. The new module is
typed, carries a module timeout, and stays within the 100-character line
limit. The table fixture closes and deletes the widget, and the monkeypatch
fixture restores `QMenu.__init__`.

Hardcoded values were reviewed and are not debt:

- `"Add Selector"` and `"Remove Selected"` are the production action titles.
  Asserting them is the menu contract.
- Fixture selectors (`password`, `user.token`, `secret`, and the typed
  `session.token`) are the sample list used to check order and commit.
- `QPoint(5, 5)` is only the context-menu event position. The widget ignores
  that position and uses the selection model, which the tests set themselves.
- Row indexes `0`, `2`, and `3` follow the three-selector fixture.

## Missing Tests

No missing-test debt. No timeout-marker blocker.

Every collected test in `tests/test_hidden_fields_event_paths.py` is covered
by `pytestmark = pytest.mark.timeout(30)`, including the parametrized
Delete, Backspace, and cancellation cases. No test overrides that mark. The
module does not rely on a `pytest.ini` timeout. Thirty seconds sits in the
GUI widget band. The only in-test event flush is the single `processEvents`
call above, and that call returns after one pass.

Requirements covered by the module:

- Delete and Backspace remove nonadjacent selected rows, keep the remaining
  order and the trailing blank, and forward `data_changed` and `changed`.
- Those keys on the trailing row leave the list unchanged and emit no
  `changed` signal.
- Those keys during editing leave the selector row in place. On this
  offscreen Qt build, `setCurrentIndex` followed by `edit` selects that row,
  so a missing editing guard would remove it.
- The context menu removes the selected rows, disables Remove Selected when
  nothing is selected, cancels with and without a selection, and adds a
  selector by typing into the real editor and committing it.

Reviewed and left without a follow-up:

- The add-and-commit test asserts the saved list and the editor state. It
  does not spy on signals. `setData` is what stores that list, and it already
  emits both signals. The removal tests spy on those same signals.
- Menu removal of a trailing-only selection is not repeated. The keyboard
  tests cover that protection, and the menu uses the same
  `remove_selected_rows` path.
- No new production ERROR path was added, so no `caplog` assertion is
  required.
- Targeted runs for this change passed. Unrelated suite failures are outside
  this analysis.

## Performance Concerns

No performance concern. Each test builds one small table and dispatches a
few key or menu events. The change adds no production work, no large data
set, and no polling loop.

## Follow-up Tasks

Neither item blocks this task. User documentation under `doc/` was not
updated in Step 7. This task has no user-facing behavior change, so the
documentation clause does not apply. Follow-ups were filed after blocker
review.

1. **Centralize the Shiboken `QMenu.exec` instance stand-in.**
   - Priority: Low
   - Jira: [PYPOST-1557](https://pypost.atlassian.net/browse/PYPOST-1557)
   - A class-level patch does not intercept `QMenu.exec` under Shiboken.
     `tests/test_hidden_fields_event_paths.py` assigns `exec` on the menu
     instance from a patched `QMenu.__init__`. The real handler still builds
     the actions. A later menu test that patches the class method instead
     would open a real modal menu and block until the timeout. Put this
     instance stand-in in one shared test helper.
   - Classification: `NON-BLOCKER`

2. **Bound the editor-commit flush after Return.**
   - Priority: Medium
   - Jira: [PYPOST-1558](https://pypost.atlassian.net/browse/PYPOST-1558)
   - `test_context_menu_add_edits_and_commits_trailing_row` depends on one
     `QCoreApplication.processEvents()` call to apply the queued commit.
     The module timeout covers a hang. It does not observe that the editor
     has closed or that the new selector is present before asserting.
     Replace the single flush with a bounded wait that stops when the
     committed selector is in the list, or when the editor leaves editing
     state, and that stops at an iteration cap.
   - Classification: `NON-BLOCKER`

This task's targeted runs passed. No pre-existing suite failure is recorded
from those runs.
