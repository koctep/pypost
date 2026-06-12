# PYPOST-66: main_window.py exceeds 150 LOC target

## Programming language

Python — per `.cursor/lsr/do-python.md`.

## Goals

Continue PYPOST-43 MainWindow decomposition (TD-1): reduce `main_window.py` size by extracting
cohesive wiring logic so the composition root stays readable and regression caps remain healthy.

## Problem statement

`MainWindow` still carries cross-presenter signal wiring inline. PYPOST-43 targeted ≤ 150 LOC;
pragmatic follow-up work extracts one meaningful chunk per sprint without a full rewrite.

## User stories

- As a **developer**, I want presenter signal wiring in a dedicated module so I can review
  and test cross-presenter connections without scrolling through layout and lifecycle code.
- As a **maintainer**, I want `MainWindow` class LOC to shrink incrementally toward the
  PYPOST-43 target while staying under PYPOST-376 regression caps (300 file / 260 class).

## Functional requirements

- **FR-1:** Cross-presenter `connect()` calls move out of `MainWindow` into
  `pypost/ui/main_window_signals.py`.
- **FR-2:** `MainWindow.__init__` calls the extracted wiring function; behavior unchanged.
- **FR-3:** History panel `curl_copied` still shows the status-bar message.

## Non-functional requirements

- **NFR-1:** No new logging required (wiring-only refactor).
- **NFR-2:** Existing MainWindow tests pass with updated patch targets.
- **NFR-3:** New unit tests cover the extracted wiring module.

## Out of scope

- Extracting layout builder, menu bar, or keyboard shortcuts (future PYPOST-43 follow-ups).
- Reaching the full ≤ 150 LOC target in this ticket.

## Definition of Done

| # | Criterion |
|---|-----------|
| AC-1 | `wire_presenter_signals()` lives in `main_window_signals.py` |
| AC-2 | `MainWindow` no longer defines `_wire_signals` or `_on_curl_copied` |
| AC-3 | `main_window.py` file and class LOC within PYPOST-376 caps |
| AC-4 | `tests/test_main_window_signals.py` and existing MainWindow tests pass |
