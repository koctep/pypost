# PYPOST-1531: Hidden field interaction coverage

## Research

The widget already routes Delete and Backspace through selected-row removal unless editing.
Its context menu creates Add Selector and Remove Selected actions; removal is disabled without
selected rows. Existing virtualization tests call operations directly rather than dispatching events.
No production defect was identified during inspection.

Qt's [QTest key simulation](https://doc.qt.io/qt-6/qtest.html) supports dispatching key clicks
without a positive delay. A
[QContextMenuEvent](https://doc.qt.io/qtforpython-6/PySide6/QtGui/QContextMenuEvent.html)
represents a menu request; using that event avoids platform differences in right-click synthesis.

## Implementation Plan

1. Step 3: **N/A — no behavioral change**. This ticket adds coverage of delivered behavior;
   there is no production fix and no defect to demonstrate with a deliberately red assertion.
   Independently review this rationale before adding the tests in Step 4.
2. Add `tests/test_hidden_fields_event_paths.py`, using the existing application fixture and
   real table/model/delegate. Dispatch Delete and Backspace with `QTest.keyClick` after selecting
   nonadjacent rows. Assert remaining order, the trailing blank, and forwarded change signals.
3. Dispatch context-menu events through Qt to the table viewport. Replace only the blocking
   `QMenu.exec` boundary with a deterministic chooser that inspects the real actions and returns
   Add Selector, Remove Selected, or cancellation. Keep the real handler and row operations.
4. Cover menu removal, disabled removal without selection, cancellation, and addition followed
   by typing into the real editor and committing. Also cover trailing-row deletion protection
   and deletion keys during active editing without losing the selector row.
5. Give the module an explicit timeout. Use bounded event processing only where needed; no
   fixed sleeps, interactive popup, external service, or unbounded wait. Close/delete widgets
   reliably and restore monkeypatches per test.
6. Run the event suite and existing hidden-field regression suites through targeted `make test`;
   run appropriate Make lint/documentation gates. Reuse fresh recorded full-suite triage rather
   than repeat unrelated baseline failures.

## Architecture

```text
QTest key events / QContextMenuEvent sent by Qt
  -> HiddenFieldsTable event overrides and real menu actions
  -> selected-row removal or real delegate editor
  -> HiddenFieldsTableModel -> ordered selectors, blank row, change signals
```

Production modules and interfaces stay unchanged. The test module owns setup, event dispatch,
menu selection, public `get_data()`/`rowCount()` assertions, editor checks, and signal spies.
The model/view architecture remains the test subject; only modal menu execution is substituted
so tests remain deterministic in the offscreen environment. Selection uses the Qt selection
model; tests must not call `keyPressEvent`, `contextMenuEvent`, or removal helpers directly.

## Q&A

- Why no red repro? Missing event-path coverage is the debt; user behavior is already present.
- What if a defect appears? Report it and revisit the approved assumptions before a product fix.
- How is acceptance gated? Independent review in the authorized autonomous sprint run.
