# PYPOST-154: Technical Debt

## Resolved

- **No Error Handling for Port Binding** (PYPOST-20) — MCP and metrics both emit
  operator-facing `start_failed` messages with UI dialogs. Shared `format_bind_error` in
  `server_bind.py`.

## Remaining (non-blocker)

- Metrics server has no ON/OFF status indicator (unlike MCP); dialog-only on failure.
- Auto-retry or alternate-port selection on bind conflict — deferred.

## Verdict

**SAFE TO CLOSE** — PYPOST-20 port-binding acceptance criteria met for both servers;
automated tests pass; developer docs updated.
