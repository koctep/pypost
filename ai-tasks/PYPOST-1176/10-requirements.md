# PYPOST-1176 — Requirements

## Problem

`make test` fails on `dev` with multiple deterministic failures blocking CI.

## Acceptance Criteria

1. `make test` passes (all test files green under parallel runner).
2. `make check` passes.
3. No local `qapp` fixtures outside `conftest.py`.
4. `PLAIN_VARIABLE_PATTERN` rejects inner whitespace per contract.
5. PYPOST-374 dialog audit artifact matches current discovery totals.

## Fixes

| Area | Action |
| --- | --- |
| qapp alignment | Remove local fixtures from MCP/WS test modules |
| Tokenizer | Strict plain pattern; loose matcher for hover masking |
| Audit artifact | Update `30-dialogs-audit-report.md` to 1,208 LOC |
| Baseline snapshot | Regenerate `baseline-metrics.md` |
