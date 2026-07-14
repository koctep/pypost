# PYPOST-762: Technical Debt

## Shortcuts taken

- Daemon `threading.Thread` for history load (not `QThread` gateway) — matches existing
  `HistoryManager` save pattern; UI callback marshaled via `QTimer.singleShot`.
- History panel shows empty list until async load completes; no loading spinner (P3 scope).

## Code quality

No blockers identified. Implementation is minimal and aligned with `RequestManager` defer
pattern.

## Follow-up tasks

None — scope fully addressed R-P3-002 from PYPOST-689 audit.
