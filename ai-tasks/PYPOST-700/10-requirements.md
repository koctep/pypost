# PYPOST-700: Split template_service.py if LOC grows

## Goals

Close architecture audit finding **R-P3-002 (S-TMPL-004)** from PYPOST-684:
`template_service.py` exceeded the documented LOC cap (204 vs 200). Split private
render and observability helpers into a sibling module so the orchestration class
stays within maintainability limits without changing consumer behavior.

**Business intent:** Improve code maintainability and satisfy SOLID baseline metrics —
no user-visible behavior change.

## User Stories

- As a **developer**, I want `TemplateService` to focus on orchestration, so render
  stages and metrics/logging helpers are easier to locate and test.
- As a **reviewer**, I want `architecture_audit.md` to mark R-P3-002 remediated, so
  the P3 backlog reflects current state.

## Definition of Done

- Private render/observability helpers (~80 LOC) live in `template_service_render.py`.
- `template_service.py` LOC at or below audit cap (225).
- Public `TemplateService` API unchanged (`render_string`, `parse`,
  `validate_function_expressions`).
- Existing template service tests pass.
- `make check` passes.

## Out of scope

- Changing validation or resolver modules.
- Refactoring hover DI or consumer injection patterns.
- Adjusting audit baseline caps (already raised to 225 in PYPOST-717).

## Source

- Jira [PYPOST-700](https://pypost.atlassian.net/browse/PYPOST-700)
- Audit R-P3-002 / S-TMPL-004 in `ai-tasks/PYPOST-684/60-tech-debt.md`
