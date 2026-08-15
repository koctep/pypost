# PYPOST-1001: Import… button wiring lock

## Research

**Where the button and its id live.**

- `pypost/ui/widget_ids.py` defines the stable automation identity:
  `ENV_IMPORT_BUTTON = "pypost_env_import_button"` (line 34). This module's
  docstring states the contract: `objectName` (mirrored to
  `accessibleIdentifier`) is the primary lookup key for automated UI tests —
  not label text.
- `pypost/ui/widgets/environments/environment_list_widget.py`, inside
  `EnvironmentListWidget.__init__` (lines 119–133):
  ```python
  import_btn = QPushButton(BUTTON_IMPORT)
  set_widget_id(import_btn, ENV_IMPORT_BUTTON)
  import_btn.clicked.connect(self.import_environments)
  ...
  buttons_row.addWidget(import_btn)
  ```
  `import_btn` is a **local variable**, not stored as `self.import_btn`. It
  is only reachable after construction via Qt's widget tree (it becomes a
  child of `buttons_row` → the widget's own `QVBoxLayout`), so a test must
  locate it with `findChild(QPushButton, ENV_IMPORT_BUTTON)` rather than by
  attribute access. `EnvironmentListWidget` is itself a `QWidget` (not
  wrapped in a presenter with a separate `.panel`), so the lookup root is
  the widget instance itself: `widget.findChild(QPushButton,
  ENV_IMPORT_BUTTON)`.
- The click is wired directly to `EnvironmentListWidget.import_environments`
  (defined at line 298), which performs file pick → parse → conflict
  resolution → apply → result dialog. That whole method is the "import
  action" referenced by the DoD as `import_environments`.

**Existing button-driven `QTest.mouseClick` precedent in this project.**

Three precedents click a `QPushButton`/tab button and assert on the
resulting side effect, confirming this project's established style for
"real click, not a direct method call":

- `tests/test_response_search_flow_integration.py` (lines 8–56):
  `QTest.mouseClick(rv.search_next_btn, Qt.MouseButton.LeftButton)`, then
  asserts a label updated.
- `tests/test_tabs_presenter.py` (`test_plus_tab_click_adds_request_tab`,
  lines ~304–310) and `tests/test_tab_header.py`
  (`test_plus_tab_click_emits_new_tab_requested`, lines 30–36): both use
  `QTest.mouseClick(plus_btn, Qt.MouseButton.LeftButton)` then assert an
  observable effect (tab count, emitted signal).

A second, more directly relevant precedent shows how this codebase locks a
**named, `objectName`-identified button → presenter/widget method** wiring,
which is the exact shape of PYPOST-1001:

- `tests/test_collection_export_ui.py`,
  `TestExportCollectionEntryPoint.test_panel_exposes_an_identified_export_button_wired_to_the_flow`
  (lines 55–67):
  ```python
  @patch.object(CollectionsPresenter, "export_collection")
  def test_panel_exposes_an_identified_export_button_wired_to_the_flow(
      self, mock_export, qapp
  ):
      presenter, _manager = _make_presenter([make_collection("c1", "Billing")])
      try:
          button = presenter.panel.findChild(QPushButton, COLLECTION_EXPORT_BUTTON)
          assert button is not None
          button.click()
          mock_export.assert_called_once()
      finally:
          presenter.panel.close()
  ```
  This test (a) patches the target method on the class *before*
  construction so the `clicked.connect(self.export_collection)` binding
  captures the mock, (b) finds the button by its `widget_ids` constant via
  `findChild`, (c) clicks it, (d) asserts the method mock was invoked once.
  `tests/test_collection_import_responsiveness.py` (line 57) uses the same
  `findChild(QPushButton, COLLECTION_IMPORT_BUTTON)` lookup style for the
  sibling Import button on the Collections panel.

PYPOST-1001 combines both precedents: the `findChild`-by-`widget_ids`
lookup (collections precedent) with `QTest.mouseClick` instead of
`.click()` (Environments-domain precedent and the literal ask in the Jira
summary: *"QTest.mouseClick Import button wiring test"*). Using
`QTest.mouseClick` rather than `.click()` also matters for the DoD clause
"if the button is missing, **disabled**, ... the test fails": `QTest`
dispatches a real mouse press/release event pair through Qt's event
system, which Qt suppresses for a disabled widget, whereas
`QPushButton.click()` is a direct slot invocation that behaves less like a
real user gesture.

**Existing direct-call Import tests (must remain untouched).**

`tests/test_environment_list_widget.py` (187 lines) holds
`TestImportEnvironments`, whose 9 methods all call
`widget.import_environments()` directly (never via a click) and cover:
happy path, cancelled file picker, invalid file, zero valid candidates,
single/apply-to-all conflict prompts, partial parse failure, no-op when
`read_import_file` is `None`, and a completion log assertion. Its module
header already declares `pytestmark = pytest.mark.timeout(60)`. None of
these are touched by this task; DoD explicitly forbids re-testing
conflict/invalid-file/parse behavior in the new test.

## Implementation Plan

1. Add exactly one new test to `tests/test_environment_list_widget.py`
   (same file that already hosts the Environments-manager Import
   coverage, per DoD "the test lives with the existing ... list-widget
   Import tests"), in a new `TestImportButtonWiring` class alongside the
   existing `TestImportEnvironments` class.
2. New imports needed at the top of the file: `Qt` from
   `PySide6.QtCore` (module already imports from `PySide6` sub-packages
   elsewhere in the suite), `QTest` from `PySide6.QtTest`, `QPushButton`
   from `PySide6.QtWidgets`, and `ENV_IMPORT_BUTTON` from
   `pypost.ui.widget_ids`.
3. The test:
   - `@patch.object(EnvironmentListWidget, "import_environments")` as the
     method decorator, applied **before** `_make_widget(...)` is called
     inside the test body, so the mock is already the class attribute
     when `__init__` runs `import_btn.clicked.connect(self.import_environments)`.
     This stubs the entire import side effect chain (file dialog, parse,
     conflict prompts, list mutation) in one step — satisfying "file-picker
     and import side effects may be stubbed" without needing separate
     patches for `prompt_import_environments_file` etc.
   - Construct the widget via the existing `_make_widget(envs)` helper
     (no `read_import_file` needed, since the method itself is mocked and
     never actually runs).
   - Locate the button: `button = widget.findChild(QPushButton, ENV_IMPORT_BUTTON)`
     and `assert button is not None` (fails loudly if the button is
     missing or renamed — DoD scenario 3).
   - Click it for real: `QTest.mouseClick(button, Qt.MouseButton.LeftButton)`.
   - Assert `mock_import.assert_called_once()` — proves the click reached
     `import_environments` (DoD scenario 1 happy path; DoD scenario 2 —
     a disconnected/repointed handler — fails this assertion).
   - `try/finally: widget.close()`, matching every other test in the file.
4. No production code changes are anticipated. Run the new test against
   current `main`/`dev` code first; if it fails, that is a real wiring
   defect (per requirements' explicit allowance) and gets a minimal fix in
   Step 4 restoring `import_btn.clicked.connect(self.import_environments)`
   — the architecture does not change in that case, only the connection
   line.
5. Timeout: the module already declares
   `pytestmark = pytest.mark.timeout(60)`; the new class inherits it, so no
   additional per-test `@pytest.mark.timeout` is required (consistent with
   how the sibling `TestImportEnvironments` methods rely on the same
   module-level marker).

**Mandatory — Failing Repro (next Step 3):** Write one red test in
`tests/test_environment_list_widget.py::TestImportButtonWiring::test_mouse_click_on_import_button_starts_import`
(exact method name may be adjusted for clarity in Step 3/4) asserting: (a)
`widget.findChild(QPushButton, ENV_IMPORT_BUTTON)` returns a non-`None`
button, and (b) `QTest.mouseClick(button, Qt.MouseButton.LeftButton)`
causes a `@patch.object(EnvironmentListWidget, "import_environments")` mock
to be called exactly once. No live external deps are involved — `qapp` is
the project's existing offscreen-Qt fixture already used by every other
test in this file, and the import method itself is mocked so no real file
dialog or disk I/O occurs. Today's production wiring
(`import_btn.clicked.connect(self.import_environments)`, current line 124)
is believed correct, so this test is expected to go green immediately
after being written, without a driving production change — it is a
verification lock, not a red-then-fix repro in the classic TDD sense. If
Step 3 finds it does fail against current code, that failure is the real
defect this task exists to catch, and the sequencing becomes: write test
(red) → restore the one-line `clicked.connect` wiring (green). Either way,
sequencing is: this research (done) → write the assertion → run it → fix
only if red.

## Architecture

No new modules, classes, or production interfaces are introduced. This is
a test-only addition to the existing Environments-manager test module.

```
tests/test_environment_list_widget.py
├── TestImportEnvironments            (existing, untouched — 9 direct-call tests)
└── TestImportButtonWiring            (new — 1 test)
    └── test_mouse_click_on_import_button_starts_import(self, mock_import, qapp)
            │
            │ 1. widget = _make_widget(envs)
            │      EnvironmentListWidget.__init__
            │        creates import_btn (QPushButton)
            │        set_widget_id(import_btn, ENV_IMPORT_BUTTON)   [pypost/ui/widget_ids.py]
            │        import_btn.clicked.connect(self.import_environments)  ← bound to mock
            │
            │ 2. button = widget.findChild(QPushButton, ENV_IMPORT_BUTTON)
            │      assert button is not None
            │
            │ 3. QTest.mouseClick(button, Qt.MouseButton.LeftButton)
            │      → Qt event system → QPushButton emits clicked
            │      → EnvironmentListWidget.import_environments()  (mocked)
            │
            └── 4. mock_import.assert_called_once()
```

**Module interaction.**

- `tests/test_environment_list_widget.py` (test) → imports
  `EnvironmentListWidget` from
  `pypost.ui.widgets.environments.environment_list_widget` (system under
  test, unchanged) and `ENV_IMPORT_BUTTON` from `pypost.ui.widget_ids`
  (existing identity constant, unchanged).
- No change to `pypost/ui/widget_ids.py`, `environment_list_widget.py`, or
  any other production module is planned. If Step 3/4 finds the click does
  not reach `import_environments`, the only expected production edit is
  restoring the single `clicked.connect(...)` line already present at
  `environment_list_widget.py:124` — no new interface, signal, or class is
  needed to fix that class of defect.

**Selected pattern and justification.**

- **Behavior-locking Qt widget test via `findChild` + `QTest.mouseClick` +
  `patch.object` spy**, matching two precedents already established in
  this codebase (`test_collection_export_ui.py` for the
  `findChild`-by-stable-id + method-patch shape, and
  `test_response_search_flow_integration.py` /
  `test_tabs_presenter.py` for the `QTest.mouseClick` real-input-event
  shape). Reusing the established pattern rather than inventing a new one
  keeps the suite's testing style consistent and keeps the new test
  hermetic (offscreen Qt via the existing `qapp` fixture, mocked import
  side effects, no disk/network).
- **Mock/spy over observable side effect**: the click's downstream import
  behavior (list mutation, dialogs) is already covered exhaustively by
  `TestImportEnvironments`'s direct-call tests. Re-asserting a list
  mutation here would duplicate that coverage and violate the DoD's "does
  not re-assert Import's conflict, invalid-file, or parse logic" scope
  boundary. A `patch.object(..., "import_environments")` spy is the
  narrowest correct assertion of *wiring* (click → method called), which
  is the one thing no existing test proves.

## Q&A

**Q:** Why `findChild(QPushButton, ENV_IMPORT_BUTTON)` instead of exposing
`self.import_btn` on the widget?

**A:** `widget_ids.py`'s documented contract is that `objectName` (via
`set_widget_id`) is the stable automation identity for UI tests — not
Python attribute access. The Collections-panel precedents
(`test_collection_export_ui.py`, `test_collection_import_responsiveness.py`)
already use `findChild(..., <WIDGET_ID_CONSTANT>)` for this exact purpose,
and `import_btn`/`export_btn` in `environment_list_widget.py` are
deliberately local variables (not `self.` attributes) already exposed only
through their widget id, consistent with that contract. Adding a new
`self.import_btn` attribute would be an unrequested production change; scope
is test-only.

**Q:** Why patch `import_environments` at the class level instead of
stubbing `prompt_import_environments_file` (as `TestImportEnvironments`
does)?

**A:** Stubbing only the file picker (as the direct-call tests do) still
exercises parse/conflict/apply/result-dialog logic — the exact logic DoD
says this new test must **not** re-assert. Patching
`EnvironmentListWidget.import_environments` itself isolates the assertion
to "was the method called," which is precisely the click→wiring contract
in scope, and satisfies "file-picker and import side effects may be
stubbed" with a single patch instead of three.

**Q:** Does `QTest.mouseClick` need `qapp` and an event loop pump?

**A:** `qapp` (already a fixture used by every test in this file and
project-wide, per the `Qt.mouseClick` precedents surveyed above) provides
the offscreen `QApplication` instance `QTest.mouseClick` requires to
dispatch synthetic mouse events. No explicit `processEvents()` pump is
needed: `QTest.mouseClick` is synchronous — it sends the press/release
event pair and returns after Qt's event system (including the connected
slot call) has run, matching the pattern already relied on in
`test_response_search_flow_integration.py` and `test_tabs_presenter.py`.
