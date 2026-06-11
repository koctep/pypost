# PYPOST-154: Verify port-in-use error handling (MCP + metrics)

## Goals

Close the PYPOST-20 follow-up by confirming both observability servers surface clear,
actionable bind failures to operators — not only in logs or silent OFF status.

## User Stories

- As a **PyPost user**, when the MCP port is busy at startup, I see a warning dialog and
  the status stays OFF (PYPOST-556).
- As a **PyPost user**, when the metrics port is busy at startup, I see a warning dialog
  even if the failure happened before the main window opened (PYPOST-153).
- As a **developer**, I can run automated tests that prove both servers share the same
  operator-facing bind error format.

## Definition of Done

- [x] MCP `start_failed` + `EnvPresenter` dialog verified unchanged and tested.
- [x] Metrics `start_failed` + `MainWindow` dialog verified and tested.
- [x] Shared `format_bind_error` used by both servers; dedicated unit tests added.
- [x] Developer docs cover both servers in troubleshooting and test coverage tables.
- [x] PYPOST-20 port-binding debt item marked resolved.

## Task Description

Follow-up from [PYPOST-20](https://pypost.atlassian.net/browse/PYPOST-20) tech debt.
Implementation landed in PYPOST-556 (MCP) and PYPOST-153 (metrics). This task verifies
end-to-end coverage, documents the combined behavior, and closes remaining doc gaps.

**In scope:** verification, shared-helper tests, developer documentation.

**Out of scope:** auto-retry, alternate port selection, metrics ON/OFF status indicator.

## Q&A

| Question | Answer |
| --- | --- |
| Is new code required? | Minimal — mostly verification; one focused `test_server_bind.py`. |
| Duplicate of PYPOST-153? | Partially — 153 implemented metrics; 154 closes PYPOST-20 across both servers. |
