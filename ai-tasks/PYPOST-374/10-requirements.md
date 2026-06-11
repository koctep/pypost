# PYPOST-374: Individual ui/dialogs/ SOLID audit

## Goals

The PYPOST-40 SOLID audit summarized all dialogs under `ui/dialogs/` (~400 LOC) as a single
inventory row. Maintainers cannot prioritize dialog refactors or assess test gaps per component
without per-dialog SOLID scoring and finding references.

This task closes the PYPOST-40 tech-debt shortcut by publishing an individual audit for each
dialog module, aligned with the original audit methodology.

## Programming Language

Python 3.10+ (PyPost project standard).

## User Stories

- As a **maintainer**, I want per-dialog SOLID findings with file references so I can schedule
  refactors without re-reading every dialog.
- As a **tech-debt owner**, I want prioritized recommendations (P1/P2/P3) per dialog so follow-up
  work can be filed against concrete findings.
- As a **reviewer**, I want an inventory guard so new dialogs are not omitted from future audits.

## Definition of Done

- [x] Each module under `pypost/ui/dialogs/*.py` (excluding empty `__init__.py`) has a SOLID
      assessment with severity ratings and maintainability notes.
- [x] Primary deliverable: `ai-tasks/PYPOST-374/30-dialogs-audit-report.md`.
- [x] Audit-era grouped summary from PYPOST-40 preserved for comparison (LOC and scope drift).
- [x] Script reproduces dialog inventory LOC from the repository tree.
- [x] Unit test ensures inventory matches on-disk modules and audit report lists all dialogs.
- [x] Developer docs cross-linked from `doc/dev/solid_audit.md`.

## Task Description

**Source:** `ai-tasks/PYPOST-40/60-tech-debt.md` — "Dialogs audited as a group."

### In Scope

- All seven dialog modules: About, Hotkeys, Save, Environment, Settings, MCP Activity, MCP Tools
  Overview.
- SOLID assessment per principle (SRP, OCP, LSP, ISP, DIP) plus testability.
- Prioritized recommendations and finding IDs traceable to file:line references.
- Offline inventory script and regression test.

### Out of Scope

- Refactoring dialogs to fix findings (separate follow-up tasks).
- Auditing `pypost/ui/collection_item_dialogs.py` (outside `ui/dialogs/`).
- Automated radon/pylint (PYPOST-373).

## Functional Requirements

1. Record file LOC and responsibility per dialog.
2. Score SOLID violations with High/Medium/Low severity (qualitative, same as PYPOST-40).
3. Document test coverage status per dialog.
4. Map findings to P1/P2/P3 recommendations.

## Non-functional Requirements

- Analysis-first — no production behavior changes.
- Reproducible LOC via script; audit report date documented.
- Markdown artifacts follow project style (UTF-8, LF, ≤100 char lines where practical).

## Constraints and Assumptions

- Manual code walkthrough; no automated static analysis.
- Presenters (`env_presenter`, `main_window`, `request_save_orchestrator`) own dialog launch;
  audit focuses on dialog classes themselves.
- Baseline snapshot date: 2026-06-11.

## Main Entities

| Entity | Description |
| --- | --- |
| Dialog module | One `QDialog` subclass file under `pypost/ui/dialogs/` |
| Finding | SOLID or maintainability issue with ID, location, severity |
| Inventory row | Module path, LOC, caller, test coverage summary |

## Q&A

| Question | Answer |
| --- | --- |
| Why seven dialogs vs five in PYPOST-40? | MCP Activity and MCP Tools Overview were added after the original audit; Settings grew significantly. |
| Should widgets inside EnvironmentDialog be audited? | Note composition in EnvironmentDialog; deep widget audit is out of scope unless they block dialog SRP assessment. |
| Is code change allowed? | Only inventory script and regression test; no dialog production code changes. |
