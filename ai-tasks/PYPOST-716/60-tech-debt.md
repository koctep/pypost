# PYPOST-716: Technical Debt

## Resolved

- **Stabilize MCPServerManager port-busy test** (PYPOST-686) — Patched `uvicorn.Server.serve` to simulate the EADDRINUSE OSError directly, removing complex socket bind/cleanup in tests and fully stabilizing the suite.

## Remaining (non-blocker)

- **PYPOST-429** — The underlying root cause of Qt/PySide6 thread-termination segfaults on macOS remains open and should be addressed separately.

## Verdict

**SAFE TO CLOSE** — All acceptance criteria met; the tests run cleanly and stably on macOS; signal propagation is fully exercised; and no native crashes or flakiness are introduced.
