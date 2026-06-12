# PYPOST-687: Technical Debt Analysis

**Task type:** Code quality and maintainability audit (no application code changes).

**Source:** `30-audit-report.md` — P1/P2/P3 remediation recommendations.

Thirteen remediation items for follow-up ticketing.

## Shortcuts Taken

- **No `make analyze`:** Target undefined; used `make lint` and AST scans instead.
- **Heuristic type adoption:** Counted `from __future__ import annotations`; no full typing coverage
  analysis.
- **Function LOC via AST:** Includes docstrings/blanks inside function body; sufficient for ranking.
- **No code fixes in scope:** Findings document gaps; remediation deferred to follow-up work.

## Code Quality Issues

Maintainability issues observed in the audited codebase (not introduced by this task):

- **SOLID cap regressions (P1):** `main_window.py`, `MainWindow` class, `template_service.py`
  exceed PYPOST-376 caps.
- **Lint gate broken (P1):** Four flake8 violations block `make lint`.
- **Complexity hotspots (P2):** `encryption_migration._rewrite_environments` (225 LOC),
  `tabs_presenter.py` (715 LOC), `metrics_registry._init_metrics` (196 LOC).
- **Broad exception handling (P2):** 29 `except Exception` in `pypost/`.
- **No static type checker (P2):** mypy/pyright absent from Makefile and CI.
- **Approaching caps (P2):** `metrics.py` (2% headroom), `request_service.py` (10%).

## Missing Tooling

- CI does not run `make lint` despite installing flake8
- No `make analyze` umbrella target for lint + caps + optional types

## Performance Concerns

N/A for this audit. LOC/complexity proxies only; no runtime profiling.

## Follow-up Tasks

### P1 — Critical / guardrail failure

#### R-P1-001 — Resolve SOLID cap violations for main_window and template_service

- **Priority:** P1
- **Finding refs:** MR-001, MR-003, cap check output
- **Description:** `main_window.py` 383 LOC (cap 300), `MainWindow` 343 (cap 260),
  `template_service.py` 204 (cap 200). Fails `audit_baseline_metrics.py --check` and
  `test_solid_audit_baseline.py`.
- **Remediation:** Extract shortcuts/MCP/status wiring from MainWindow **or** remeasure and update
  caps with documented justification in `doc/dev/solid_audit.md`. Split template expression helpers
  from `template_service` if refactor preferred.
- **Jira:** [PYPOST-728](https://pypost.atlassian.net/browse/PYPOST-728)

#### R-P1-002 — Fix flake8 violations to restore passing make lint

- **Priority:** P1
- **Finding refs:** Lint table, DC-001–DC-003
- **Description:** Four violations: F841 `error_prefix`, F401 `MigrationReport`, W391 `mixins.py`,
  E501 `request_editor.py`.
- **Remediation:** Remove dead assignment/import, fix line wrap, trim EOF blank line; verify
  `make lint` passes.

### P2 — Meaningful maintainability gaps
- **Jira:** [PYPOST-729](https://pypost.atlassian.net/browse/PYPOST-729)

#### R-P2-001 — Decompose encryption_migration._rewrite_environments

- **Priority:** P2
- **Finding refs:** Complexity table (225 LOC function)
- **Description:** Single function handles backup, rewrite, error aggregation, and reporting.
- **Remediation:** Extract per-environment rewrite, backup writer, and result collector; add unit
  tests per step.
- **Jira:** [PYPOST-730](https://pypost.atlassian.net/browse/PYPOST-730)

#### R-P2-002 — Reduce tabs_presenter complexity (715 LOC)

- **Priority:** P2
- **Finding refs:** Largest uncapped presenter
- **Description:** Tab send, save, MCP, and metrics wiring concentrated in one class.
- **Remediation:** Extract send-handler, save-handler, or MCP-status sub-presenters; stay under cap
  785 with headroom.
- **Jira:** [PYPOST-731](https://pypost.atlassian.net/browse/PYPOST-731)

#### R-P2-003 — Deduplicate fold structure scanner logic

- **Priority:** P2
- **Finding refs:** D-001
- **Description:** JSON/XML/YAML scanners duplicate `_scan_regions` structure.
- **Remediation:** Shared traversal utilities or template-method base with format-specific token
  parsers.
- **Jira:** [PYPOST-732](https://pypost.atlassian.net/browse/PYPOST-732)

#### R-P2-004 — Narrow broad except Exception in persistence layers

- **Priority:** P2
- **Finding refs:** Error handling section
- **Description:** `storage.py`, `request_manager.py`, `alert_manager.py` use broad catches.
- **Remediation:** Catch `OSError`, `json.JSONDecodeError`, `httpx` errors explicitly; use
  `logger.exception` in remaining broad handlers.
- **Jira:** [PYPOST-733](https://pypost.atlassian.net/browse/PYPOST-733)

#### R-P2-005 — Add optional static type checking to dev workflow

- **Priority:** P2
- **Finding refs:** Type hygiene section
- **Description:** ~16% of modules use postponed annotations; no mypy/pyright.
- **Remediation:** Add `make typecheck` on `pypost/core/` and `pypost/models/` with incremental
  strictness.
- **Jira:** [PYPOST-734](https://pypost.atlassian.net/browse/PYPOST-734)

#### R-P2-006 — Extend baseline caps to metrics.py and mixins.py

- **Priority:** P2
- **Finding refs:** MR-004, MR-005, MR-006
- **Description:** `metrics.py` at 161/165; `mixins.py` 374 LOC uncapped.
- **Remediation:** Add FILE_CAPS entries or split `VariableHoverMixin` from editor helpers before
  breach.
- **Jira:** [PYPOST-735](https://pypost.atlassian.net/browse/PYPOST-735)

#### R-P2-007 — Run make lint in CI

- **Priority:** P2
- **Finding refs:** MR-007, O-004
- **Description:** flake8 installed in test workflow but not executed.
- **Remediation:** Add `make lint` step to `.github/workflows/test.yml` or dedicated lint job.

### P3 — Minor hygiene
- **Jira:** [PYPOST-736](https://pypost.atlassian.net/browse/PYPOST-736)

#### R-P3-001 — Remove dead code flagged by flake8

- **Priority:** P3
- **Finding refs:** DC-001, DC-002
- **Description:** Overlaps R-P1-002; standalone hygiene ticket if lint fix split.
- **Remediation:** Delete unused `error_prefix` branch variable and import.
- **Jira:** [PYPOST-737](https://pypost.atlassian.net/browse/PYPOST-737)

#### R-P3-002 — Expand postponed annotations in modified modules

- **Priority:** P3
- **Finding refs:** Type hygiene
- **Description:** Legacy modules lack `from __future__ import annotations`.
- **Remediation:** Adopt when touching files; no big-bang migration required.
- **Jira:** [PYPOST-738](https://pypost.atlassian.net/browse/PYPOST-738)

#### R-P3-003 — Document error-handling convention in dev docs

- **Priority:** P3
- **Finding refs:** O-003, error handling section
- **Description:** Mix of log-only, log+dialog, and silent pass patterns.
- **Remediation:** Add section to `doc/dev/maintainability_audit.md` or `architecture.md`.
- **Jira:** [PYPOST-739](https://pypost.atlassian.net/browse/PYPOST-739)

#### R-P3-004 — Clarify request_sync module naming

- **Priority:** P3
- **Finding refs:** Naming section, PYPOST-684 L-003
- **Description:** `request_sync.py` implements tab dirty helpers, not HTTP sync.
- **Remediation:** Rename to `tab_dirty_state.py` or move to `ui/presenters/`.
- **Jira:** [PYPOST-740](https://pypost.atlassian.net/browse/PYPOST-740)

## Blocker Review

**SAFE TO CLOSE** — audit deliverables complete; no application code changes required. PYPOST-40
goals largely met; cap and lint regressions need scheduled follow-up. Thirteen remediation items
ticketed in Jira (PYPOST-728–740).
