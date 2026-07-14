"""Qt framework integration layer within core.

Modules in this package import PySide6 for QThread, QObject, Signal, and QTimer.
They bridge async work to UI presenters via queued signal delivery.

Import rule: code that must run headless without PySide6 must NOT import from
``pypost.core.qt``. Use Qt-free modules in ``pypost.core`` and protocols in
``pypost.core.metrics_protocol`` instead.

Test setup: prefer ``pytest-qt`` or an offscreen ``QApplication`` when testing
modules here; see ``doc/dev/testability.md`` (updated in Step 7).
"""
