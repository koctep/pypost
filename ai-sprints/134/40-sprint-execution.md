# Sprint 134 — Execution Report

> Date: 2026-03-26
> Sprint: 134
> Total issues: 32 (3 Wave 1 + 29 Wave 2)

---

## Wave 1 — Completed Issues

| # | Key | Summary | Commit(s) |
|---|-----|---------|-----------|
| 1 | PYPOST-403 | Fix failing tests in CI | `afd2a58` |
| 2 | PYPOST-404 | Font size settings not applied on startup | `4ac96b8`, `cf45465` |
| 3 | PYPOST-405 | Open request in new independent tab | `061a590` |

**Tests at Wave 1 close:** 191 passed, 0 failed (see `90-sprint-report.md`).

---

## Wave 2 — Tech debt (test hardening), all Done

Groups A–K delivered per [00-roadmap.md](00-roadmap.md): CI + cov threshold (PYPOST-89/88),
test infrastructure clean-up (PYPOST-83–87), HistoryManager (58–60), MetricsManager (79),
tree state (92/93/95), JsonHighlighter (100/103), CodeEditor (104/108/110),
VariableHoverHelper batches (117–121, 130–133), settings persistence (125), MCP server impl
(139/142), EnvironmentDialog (56).

**Representative commits:** `9f0a52d` (CI), `df542ac` (coverage floor), … `865dcc1` (env dialog).

**Tests at sprint close:** 268 passed (see latest `make test` in PM closure notes).

---

## Failed Issues

None.

---

## Blockers

None encountered during execution.

---

## Retries Performed

None for Wave 1. Wave 2 executed as batched groups with roadmap/backlog sync commits.

---

## Notes (Wave 1 detail)

- **PYPOST-403** resolved two independent test-infrastructure regressions and removed an 86 MB ELF
  core dump from the repo root. Fixes: `HTTPClient` default-constructs `TemplateService()` when arg
  is `None`; `HistoryManager` retains `_save_thread` and exposes `flush()`.
- **PYPOST-404** fixed call-order in `apply_settings` (Qt 6 stylesheet vs `setFont`).
- **PYPOST-405** added isolated-tab flow with `model_copy(deep=True)` and hardened `restore_tabs`.

Full narrative: [90-sprint-report.md](90-sprint-report.md).
