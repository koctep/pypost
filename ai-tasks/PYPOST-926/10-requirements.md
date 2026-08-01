# PYPOST-926: Optional lazy PySide6 import in tests/conftest.py

## Goals

[PYPOST-923](https://pypost.atlassian.net/browse/PYPOST-923) restored CI by provisioning
Qt/EGL system libraries on all jobs that collect the shared pytest suite. Shared
`tests/conftest.py` still imported `PySide6` at module load, so **any** collection path
that loads conftest required those system libraries—even when the selected tests are
purely non-GUI.

**Business need:** Reduce environment coupling for future CI jobs, local tooling, and
narrow pytest invocations that do not exercise Qt, while keeping the existing shared
`qapp` fixture behavior for GUI tests.

**Source:** [PYPOST-926](https://pypost.atlassian.net/browse/PYPOST-926) (TD-3 from
[PYPOST-923](https://pypost.atlassian.net/browse/PYPOST-923)).

## Programming Language

Python for conftest and pytest contract tests (`.cursor/lsr/do-python.md`,
`.cursor/lsr/do-testing.md`). Developer documentation in English Markdown
(`.cursor/lsr/do-markdown.md`).

## User Stories

- As a **CI maintainer**, I want conftest not to force PySide6 import during collection
  when a job runs only non-GUI tests, so missing EGL/GL libs do not fail before tests
  that never touch Qt.
- As a **contributor**, I want `qapp`-based GUI tests to keep working unchanged after
  the conftest import change.
- As a **reviewer**, I want an automated contract that conftest defers PySide6 until
  the `qapp` fixture runs.

## Definition of Done

- [ ] `tests/conftest.py` does not import PySide6 at module level.
- [ ] Non-GUI collection paths that load conftest succeed without triggering PySide6
  import (contract test in subprocess).
- [ ] Shared `qapp` fixture still provides a module-scoped `QApplication` singleton.
- [ ] Existing GUI / `qapp` tests remain green (`make check` or targeted pytest).
- [ ] No product feature behavior under `pypost/` is intentionally changed.

## Task Description

### Problem

`tests/conftest.py` eagerly imports `QApplication` from PySide6. Pytest loads conftest
during collection for the whole suite, so runners without Qt/EGL system libraries fail
at import time—even when the selected tests never request `qapp` or import Qt widgets.

### In Scope

- Defer PySide6 import in `tests/conftest.py` to the `qapp` fixture (or equivalent
  lazy boundary).
- Keep `QT_QPA_PLATFORM=offscreen` set before any deferred Qt import.
- Add a fast contract test proving module-level conftest import does not load PySide6.
- Light developer doc note in `doc/dev/`.

### Out of Scope

- Removing PySide6 imports from individual GUI test modules (they still load Qt when
  collected).
- Changing CI apt provisioning (PYPOST-923/924/925 remain authoritative for full-suite
  jobs).
- Replacing the shared `qapp` fixture or pytest-qt adoption.

### Constraints and Assumptions

- PySide6 remains a dev dependency; lazy conftest reduces coupling, not the need for Qt
  libs when GUI test modules are collected.
- Autonomous sprint-task-runner: Step artifacts pre-approved.

## Functional Requirements

1. **FR1 — Lazy conftest:** Module-level execution of `tests/conftest.py` must not
   import PySide6.
2. **FR2 — qapp unchanged:** The `qapp` fixture must still create or reuse the process
   `QApplication` singleton with module scope.
3. **FR3 — Contract test:** Automated check fails on eager import and passes after fix.
4. **FR4 — GUI regression:** Representative `qapp` tests continue to pass.

## Non-Functional Requirements

- **Scope discipline:** Minimal diff to conftest; no unrelated test refactors.
- **Maintainability:** Document lazy-import intent for future conftest edits.

## Q&A

| Question | Answer |
| --- | --- |
| Why not remove Qt from all tests? | Out of scope; only conftest eager import is targeted. |
| Does this remove CI apt packages? | No; full GUI collection still needs system libs per test modules. |
| Interactive Step 1 approval? | Skipped — sprint-task-runner autonomous mode. |
