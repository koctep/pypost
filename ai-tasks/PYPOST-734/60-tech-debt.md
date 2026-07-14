# PYPOST-734: Technical Debt

## Shortcuts Taken

- **Frozen baseline:** 54 mypy errors accepted as known debt; gate prevents regressions only.
- **UI excluded:** `pypost/ui/` not type-checked (Qt/PySide6 stubs add noise; separate effort).

## Residual Debt

| Item | Severity | Notes |
| --- | --- | --- |
| 54 baseline mypy errors in `pypost/core/` | Medium | Triage in `20-architecture.md`; fix incrementally |
| No CI typecheck job | Low | Optional dev target by design |
| `pypost/models/` clean today | Info | Keep clean as models grow |

## Blocker Review

**SAFE TO CLOSE** — acceptance criteria met; baseline documented; no blockers.

## Follow-up Tasks

#### R-P2-005a — Fix implicit Optional defaults in http_client and request_service

- **Priority:** P2
- **Description:** 8 `assignment` errors from `param: dict = None` patterns; add `| None` or
  use `Optional` defaults.
- **Remediation:** Annotate `send_request` / `execute` optional callbacks and variables.
- **Jira:** [PYPOST-813](https://pypost.atlassian.net/browse/PYPOST-813)

#### R-P2-005b — Align ExecuteRequestProtocol with RequestService

- **Priority:** P2
- **Description:** Protocol mismatch in `worker.py`, `mcp_server_impl.py` (optional vs required
  keyword defaults).
- **Remediation:** Harmonize protocol signature with implementation or use structural typing
  `# type: ignore` only as last resort.
- **Jira:** [PYPOST-814](https://pypost.atlassian.net/browse/PYPOST-814)

#### R-P2-005c — Type-check pypost/ui incrementally

- **Priority:** P3
- **Description:** Qt layer excluded from mypy scope.
- **Remediation:** Add PySide6 stubs or per-module overrides when core debt is reduced.
- **Jira:** [PYPOST-815](https://pypost.atlassian.net/browse/PYPOST-815)
