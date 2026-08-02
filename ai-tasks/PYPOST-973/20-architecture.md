# PYPOST-973: Adopt qt_item_view teardown in collections_tree

## Research

### Jira / parent debt

- Issue: [PYPOST-973](https://pypost.atlassian.net/browse/PYPOST-973) —
  Adopt `qt_item_view` teardown helper in `collections_tree.py` fixtures if
  isolated item views grow. Acceptance: Shared teardown used where applicable;
  no Qt teardown warnings.
- Source: [PYPOST-940](https://pypost.atlassian.net/browse/PYPOST-940) TD-1 —
  “Adopt qt_item_view teardown in collections_tree if isolated views grow.”
- Labels: `tech-debt`, `testing`, `ui`. Priority: Low. Type: Debt.
- Requirements: [10-requirements.md](10-requirements.md) (FR-1–FR-6, AC-1–AC-6).

### Qt model/view teardown baseline

Qt model/view programming attaches an external model to
`QAbstractItemView` subclasses such as `QTreeView`. Destroying a view while a
model remains attached can produce destructor noise in PySide6 offscreen test
runs. The established project pattern (PYPOST-940) is to call
`view.setModel(None)` via `detach_item_view_model` before closing the view
([Qt Model/View Programming](https://doc.qt.io/qtforpython-6/overviews/qtwidgets-model-view-programming.html)).

### Current helpers

| Piece | Role |
| --- | --- |
| `tests/helpers/qt_item_view.py` | `detach_item_view_model`, `close_item_view_fixture` |
| `tests/helpers/collections_tree.py` | `build_isolated_tree_actions` → `IsolatedTreeActions` with `QTreeView` + model |
| Consumers | `test_collection_tree_actions.py`, `*_delete_confirmation.py`, `*_rename_context_menu.py`, `*_rename_delegate_e2e.py` (~27 build sites) |

Gap: harnesses set `view.setModel(model)` but never detach on close. There is
no `close_isolated_tree_actions` and no context manager.

### Decision

| Option | Verdict |
| --- | --- |
| Add `close_isolated_tree_actions` using `detach_item_view_model` + context manager; migrate callers | **Chosen** — reuses shared helper, covers all harness owners |
| Inline `setModel(None)` in each test | Rejected — duplicates helper, violates NFR-3 |
| Only document “call detach yourself” | Rejected — acceptance requires shared teardown used |
| Migrate to `close_item_view_fixture` (widget_id) | Rejected — harnesses are not widget-id roots; detach primitive is enough |

## Implementation Plan

1. **Step 3 — red proof** — add a test that closing an isolated tree harness
   leaves `view.model() is None`, written against current helpers so it fails
   until close exists (or fails by asserting a missing close API).
2. **Step 4 — development** — implement close helper + context manager; migrate
   `build_isolated_tree_actions` call sites; make red test green; run focused
   suite.
3. **Steps 5–8** — cleanup, observability N/A or minimal, tech-debt review,
   update `doc/dev/testing.md`.

**Mandatory — Failing Repro (next Step 3):**

Add `tests/test_qt_item_view_teardown.py` case (or sibling) that:

1. Builds an isolated tree harness via `build_isolated_tree_actions`.
2. Calls `close_isolated_tree_actions(harness)` from `collections_tree`.
3. Asserts `harness.view.model() is None`.

Expected red failure today: `ImportError` / `AttributeError` because
`close_isolated_tree_actions` does not exist yet. That is the intended missing
behavior signal — do not implement the close helper in Step 3.

## Architecture

```text
tests/helpers/qt_item_view.py
  detach_item_view_model(view)     ← shared primitive (unchanged)

tests/helpers/collections_tree.py
  build_isolated_tree_actions(...)  ← unchanged build
  close_isolated_tree_actions(h)    ← NEW: detach + close + processEvents
  isolated_tree_actions(...)        ← NEW: contextmanager build/yield/close

tests (consumers)
  with isolated_tree_actions(...) as harness:
      ...
```

### Module responsibilities

| Module | Responsibility |
| --- | --- |
| `qt_item_view` | Own detach semantics for all item views |
| `collections_tree` | Own IsolatedTreeActions lifecycle; call shared detach on close |
| Consumer tests | Prefer `isolated_tree_actions` context manager |
| Teardown unit test | Prove harness close detaches model |

### Patterns

- **Reuse over copy** — call `detach_item_view_model`, do not reimplement.
- **Context manager** — guarantee teardown even on assertion failure.
- **Keep build()** — for rare cases needing manual lifecycle; document that
  callers must close.

## Q&A

- **Q: Why not only add close without migrating callers?**
  **A:** AC-2 requires call sites that own harnesses to use the close path;
  unused helpers do not meet acceptance.
- **Q: Why context manager instead of unittest addCleanup only?**
  **A:** Context manager works for both unittest and pytest styles and makes
  teardown visible at the call site.
