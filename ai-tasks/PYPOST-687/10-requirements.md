# PYPOST-687: Audit — code quality and maintainability

## Goals

PyPost has grown to **141 Python modules** and **~16,400 LOC** under `pypost/` since the original
SOLID audit (PYPOST-40). Presenter extraction, metrics/template injection, and regression caps
(PYPOST-376) improved structure, but ongoing feature work risks complexity growth, lint drift, and
error-handling inconsistency.

This audit establishes an evidence-based picture of **code quality and maintainability** so the
team can prioritize refactors, cap updates, and hygiene work alongside features.

## Programming Language

Python (audit and analysis task; deliverables are markdown reports and follow-up issues).

## User Stories

- As a **maintainer**, I want a consolidated view of lint failures, complexity hotspots, and cap
  regressions, so I can schedule refactors before modules become unmaintainable.
- As a **reviewer**, I want clarity on error-handling and logging patterns, so new code follows
  consistent conventions.
- As a **tech-debt owner**, I want alignment with PYPOST-40 SOLID findings and PYPOST-376 caps, so
  remediation does not duplicate or contradict prior audits.
- As a **CI operator**, I want to know whether `make lint` and baseline guardrails pass, so merge
  confidence matches documented gates.
- As a **new contributor**, I want naming and duplication patterns documented, so I extend existing
  abstractions instead of copying logic.
- As a **product owner**, I want prioritized follow-ups (P1/P2/P3), so maintainability work is
  schedulable.

## Definition of Done

- [x] An audit report is stored under `ai-tasks/PYPOST-687/` with summary, scope, methodology,
  findings, and recommendations.
- [x] Findings cover lint/type hygiene (`make lint`, flake8, type-hint adoption).
- [x] Findings cover complexity hotspots (large files, long functions, capped modules).
- [x] Findings cover duplication and naming conventions.
- [x] Findings cover error-handling patterns (`except Exception`, logging, user messaging).
- [x] Findings align with PYPOST-40 SOLID audit and `scripts/audit_baseline_metrics.py`.
- [x] Findings cover dead code and maintainability regressions since 2026-06-11 baseline.
- [x] Each significant finding includes impact and a recommended remediation direction.
- [x] Findings are prioritized (P1/P2/P3) for follow-up ticketing.
- [x] Developer summary added at `doc/dev/maintainability_audit.md`.
- [x] Out-of-scope areas are explicitly listed.

## Task Description

**Problem:** PyPost enforces flake8 via `make lint` and SOLID regression caps via
`test_solid_audit_baseline.py`, but there is no consolidated audit of whether the codebase remains
maintainable as modules grow, whether lint passes, and where complexity concentrates after years
of feature work.

**Business intent:** Make maintainability visible and schedulable — reducing god-module relapse,
lint surprise, and opaque error paths.

### In Scope

- `pypost/` application source (core, models, ui).
- Lint hygiene: `make lint`, `.flake8`, flake8 violations in `pypost/`.
- Complexity: file/class/function LOC, `audit_baseline_metrics.py --check`, AST function-length scan.
- Duplication: fold scanners, polling helpers, dialog/message patterns.
- Naming: module/class/function conventions, re-export patterns.
- Error handling: exception breadth, logging vs user alerts.
- Alignment with PYPOST-40, PYPOST-376, `doc/dev/solid_audit.md`.
- Dead code: unused variables/imports flagged by flake8.

### Out of Scope

- Implementing fixes or refactors (audit only).
- Test suite health (see PYPOST-686).
- Security/secrets (see PYPOST-685).
- Package boundary re-audit (see PYPOST-684).
- Performance profiling beyond LOC/complexity proxies.
- Adopting mypy/pyright in CI (recommendation only).

## Functional Requirements

- The audit must produce a structured written report for developers.
- The audit must run `make lint` and `scripts/audit_baseline_metrics.py --check`.
- The audit must identify largest files and longest functions (≥50 LOC).
- The audit must compare current metrics to PYPOST-40 audit era and 2026-06-11 baseline.
- The audit must include prioritized recommendations for follow-up work.

## Non-Functional Requirements

- **Clarity:** Findings understandable to a developer new to PyPost.
- **Actionability:** Recommendations specific enough to become Jira tickets.
- **Traceability:** Report links to `solid_audit.md`, PYPOST-40, PYPOST-376.
- **Proportionality:** Depth matches risk — prioritize caps, lint, and largest modules.

## Constraints and Assumptions

- Audit artifacts are markdown under `ai-tasks/PYPOST-687/`.
- `make analyze` is not defined; `make lint` is the static-analysis entry point.
- No mypy/pyright configuration exists today.
- Step 1 captures business requirements only; methodology belongs in Step 2.

## Main Entities (Business View)

| Entity | Description |
| --- | --- |
| Lint gate | `make lint` — flake8 on `pypost/` only |
| SOLID caps | LOC limits in `scripts/audit_baseline_metrics.py` |
| Complexity hotspot | File or function disproportionately large vs peers |
| Error path | Exception handler + log and/or user-visible alert |
| Maintainability regression | Growth beyond baseline or cap since 2026-06-11 |
| Audit finding | Documented gap with impact and priority |

## Acceptance Criteria (Audit Deliverables)

| ID | Criterion |
| --- | --- |
| AC-1 | Report exists under `ai-tasks/PYPOST-687/` with executive summary and detailed findings. |
| AC-2 | Lint section cites `make lint` result and violation list for `pypost/`. |
| AC-3 | Complexity section cites baseline `--check` result and top files/functions. |
| AC-4 | SOLID alignment section maps PYPOST-40 recommendations to current state. |
| AC-5 | Error-handling section summarizes patterns and outliers. |
| AC-6 | Recommendations prioritized P1/P2/P3. |
| AC-7 | `doc/dev/maintainability_audit.md` summarizes findings with link to full report. |

## Q&A

| Question | Answer |
| --- | --- |
| Why audit maintainability now? | Caps drifted; lint fails; largest modules grew post-presenter split. |
| How is this different from PYPOST-40? | PYPOST-40 was initial SOLID audit; this re-measures and finds regressions. |
| Will this refactor code? | No — audit only; follow-ups ticketed separately. |
| Primary deliverable? | Written audit report plus dev doc summary. |
