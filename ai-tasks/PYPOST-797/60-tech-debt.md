# PYPOST-797: Technical Debt Analysis

## Shortcuts Taken

No intentional "quick fixes" or temporary workarounds were introduced. The fix wires
`QPushButton.clicked` to `new_tab_requested` — the Qt-correct minimal change for a
`setTabButton` widget.

Pragmatic choices (not crutches):

- **Dual click paths retained** — `plus_btn.clicked` is the primary handler; `_on_tab_bar_clicked`
  still emits `new_tab_requested` when the plus-tab chrome (outside the button) is clicked.
  Belt-and-suspenders per architecture; no duplicate-tab risk in normal use because Qt routes
  clicks on the embedded button to the child widget, not `tabBarClicked`.
- **Direct `connect(..., self.new_tab_requested.emit)`** — no dedicated slot method. Acceptable
  for a one-line signal relay; matches existing simplicity in `RequestTabHeader`.

## Code Quality Issues

- **`doc/dev/request_actions.md` outdated** — the plus-tab section and troubleshooting still
  describe `tabBarClicked` as the click path. After this fix, `plus_btn.clicked` is primary;
  `tabBarClicked` is a fallback for chrome clicks. Deferred to Step 7 (Dev Docs) per
  `20-architecture.md`.
- **Pre-existing E402 in Qt test modules** — `pytestmark` precedes imports in
  `test_tab_header.py` and `test_tabs_presenter.py`. Established project pattern (PYPOST-548,
  PYPOST-792); no change required.

## Missing Tests

Both test modules declare explicit timeouts via module-level
`pytestmark = pytest.mark.timeout(60)` — **timeout blocker cleared**.

| Scenario | Status |
| --- | --- |
| **+ button click emits `new_tab_requested`** | Covered (`test_plus_tab_click_emits_new_tab_requested` via `QTest.mouseClick` on real widget) |
| **+ button click adds request tab via presenter** | Covered (`test_plus_tab_click_adds_request_tab` via `QTest.mouseClick`) |
| Plus tab remains last after add | Covered (`test_plus_tab_is_last`, click test assertion) |
| Plus tab close ignored | Covered (`test_plus_tab_close_is_ignored`) |
| **`tabBarClicked` fallback on plus-tab chrome** | Not covered — secondary path kept intentionally; low regression risk but untested |
| **macOS native click / layout verification** | Not automatable in CI — manual verification required per Jira reproduction steps |
| **End-to-end `MainWindow` + click** | Not covered — header and presenter unit tests deemed sufficient per architecture |

## Performance Concerns

None introduced. One additional signal connection at plus-tab creation; no per-frame or
hot-path cost.

## Follow-up Tasks

| Priority | Task | Rationale | Jira |
| --- | --- | --- | --- |
| Low | **Update `doc/dev/request_actions.md`** — document `plus_btn.clicked` as primary + path; note `tabBarClicked` as chrome fallback; refresh troubleshooting ("Ctrl+N works but + click does nothing") | Completed in Step 7 | — |
| Low | **Add regression test for `tabBarClicked` fallback** — emit or synthesize click on plus-tab chrome outside the embedded button; assert `new_tab_requested` / `add_new_tab` | Belt-and-suspenders path is production code with zero test coverage | [PYPOST-798](https://pypost.atlassian.net/browse/PYPOST-798) |
| — | **Manual macOS verification** | Required by Definition of Done; not ticketed (acceptance criterion, not debt) | — |

## Validation Summary

- `make test PYTEST_ARGS="tests/test_tab_header.py tests/test_tabs_presenter.py"`: 58 passed.
- Explicit `pytest.mark.timeout(60)` on both changed test modules.
- No new technical debt blockers for Step 7 pending user review of this document.
