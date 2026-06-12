# PYPOST-66: Architecture — extract presenter signal wiring

## Change

Move cross-presenter Qt signal connections from `MainWindow._wire_signals()` into a module-level
function `wire_presenter_signals(window)`.

## Components

| File | Role |
|------|------|
| `pypost/ui/main_window_signals.py` | **New** — all collections/tabs/env/history `connect()` calls |
| `pypost/ui/main_window.py` | Calls `wire_presenter_signals(self)` after `_build_layout()` |
| `tests/test_main_window_signals.py` | **New** — unit tests with `MagicMock` window |

## Wiring preserved

All 18 connections from the former `_wire_signals()` method, including `curl_copied` → status bar.

## Test seam

Heavy-init tests patch `pypost.ui.main_window.wire_presenter_signals` (same pattern as former
`MainWindow._wire_signals` patch). Dedicated tests import `wire_presenter_signals` directly.

## LOC impact (post-change)

| Metric | Before | After | Cap |
|--------|-------:|------:|----:|
| `main_window.py` file | 287 | 260 | 300 |
| `MainWindow` class | 249 | 222 | 260 |
