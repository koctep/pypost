# PYPOST-457: Technical Debt Analysis

## Shortcuts Taken

- **Tests-only delivery:** No production changes. Parity held before and after; tests lock
  the invariant explicitly.
- **Private attribute in integration test:** `test_catalog_allow_list_matches_jinja_globals`
  reads `svc._function_registry` because `TemplateService` does not expose the registry.
  Acceptable until optional injection API exists (PYPOST-451 debt).

No release blockers.

## Code Quality Issues

None introduced. Pre-existing items remain tracked elsewhere:

- [PYPOST-458](https://pypost.atlassian.net/browse/PYPOST-458): `FunctionRegistry` docstring
  overlap cleanup.
- [PYPOST-459](https://pypost.atlassian.net/browse/PYPOST-459): `TemplateService.render_string`
  orchestration split.

## Missing Tests

**Resolved for this ticket** — explicit parity tests added in:

- `tests/test_function_registry.py` — `test_catalog_allow_list_matches_env_globals`
- `tests/test_template_service.py` — `test_catalog_allow_list_matches_jinja_globals`

Remaining gaps (out of scope):

- Custom registry injection (no constructor hook).
- Deeper expression edge cases — [PYPOST-461](https://pypost.atlassian.net/browse/PYPOST-461).

## Performance Concerns

None. Tests run once per module; O(catalog size) with three entries today.

## Follow-up Tasks

No new Jira issues required. This ticket closes debt from PYPOST-451.

## Blocker Review

**SAFE TO CLOSE** — acceptance criteria met; no production defects found.
