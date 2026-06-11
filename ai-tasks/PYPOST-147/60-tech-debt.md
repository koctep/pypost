# PYPOST-147: Technical Debt Analysis

## Functional Completeness (DoD Cross-Check)

| DoD # | Criterion | Status | Evidence |
| --- | --- | --- | --- |
| 1 | `test_template_service.py` exists | **Met** | 49 tests + subtests |
| 2 | `render_string` coverage | **Met** | `TestTemplateServiceRenderString`, `TestTemplateServiceRenderStages` |
| 3 | `validate_function_expressions` coverage | **Met** | `TestTemplateServiceValidationOutcomes` incl. plain identifier |
| 4 | `parse` coverage | **Met** | `TestTemplateServiceParse` |
| 5 | Observability / metrics | **Met** | `TestTemplateServiceObservability`, `TestTemplateServiceHelperStages` |
| 6 | Runtime/hover parity | **Met** | `test_runtime_hover_parity_*` subTests |
| 7 | Scoped test run passes | **Met** | pytest exit 0 |

**Release stance:** **SAFE TO CLOSE** — PYPOST-18 missing-test debt for `TemplateService` is
resolved.

## Shortcuts Taken

- **Incremental delivery:** Most tests landed under PYPOST-450+; PYPOST-147 audits and
  documents rather than rewriting the suite.
- **Shared test data import:** `MALFORMED_NESTED_EXPRESSION_CASES` imported from resolver
  tests — acceptable for matrix consistency.

## Code Quality Issues

- **Cross-module test import** (pre-existing): optional extraction to `tests/helpers.py` if
  matrices grow — not a PYPOST-147 blocker.

## Missing Tests

**None for PYPOST-147 scope.** Optional integration gaps remain in HTTPClient (body, header
name) — tracked under PYPOST-450 follow-ups, not this ticket.

## Performance Concerns

- None introduced; unit file runs in ~0.3s.

## Resolved Items

- ~~PYPOST-18: no isolated `TemplateService` unit tests~~ — **resolved** by this ticket.

## Follow-up Tasks

- [**PYPOST-461**](https://pypost.atlassian.net/browse/PYPOST-461): Empty-argument calls,
  multi-placeholder first-failure, standalone malformed closing-paren patterns.
- [**PYPOST-457**](https://pypost.atlassian.net/browse/PYPOST-457): Registry/globals parity test.
- [**PYPOST-455**](https://pypost.atlassian.net/browse/PYPOST-455): Template/expression caching
  after usage metrics.
- [**PYPOST-148**](https://pypost.atlassian.net/browse/PYPOST-148): Jinja2 `from_string` caching
  (from PYPOST-18).

## STEP 6 Validation

```text
.venv/bin/python -m pytest tests/test_template_service.py -v
→ 49 passed, 30 subtests passed in 0.27s
```
