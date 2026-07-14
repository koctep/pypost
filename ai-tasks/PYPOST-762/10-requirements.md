# PYPOST-762: Defer or async HistoryManager startup load

## Goals

Remove synchronous history file I/O from the GUI startup path so the main window appears
faster and remains responsive while persisted history is read.

## Programming language

Python (PySide6 desktop app).

## Functional requirements

- History must still be available in the History panel after startup completes loading.
- New request executions must still append to history correctly during and after deferred load.
- Existing history persistence (save, cap, delete, clear) must behave unchanged.
- Tests and non-GUI callers may still construct `HistoryManager` with immediate load.

## Non-functional requirements

- Startup must not block the Qt main thread on `history.json` read.
- Load may run in a background daemon thread; UI refresh must occur on the main thread.
- Pattern should align with `RequestManager(defer_initial_load=True)` precedent.

## Constraints and assumptions

- History files remain bounded (500 entries cap); P3 priority — acceptable to show empty
  panel briefly at startup.
- `HistoryManager` is constructed in `main.py` composition root (PYPOST-694).

## Main entities

- **HistoryManager** — reads/writes `history.json`; serves entries to UI and request pipeline.
- **HistoryPanel** — displays and filters history; refreshes when data is ready.
- **MainWindow** — wires startup load dispatch and panel refresh.

## User scenarios

1. User launches PyPost: window appears without waiting for history disk read; History tab
   populates shortly after.
2. User sends a request before history load finishes: entry is recorded and appears after load
   and refresh complete.
3. Developer runs unit tests with `HistoryManager(history_path=tmp)`: synchronous load
   remains default for simplicity.
