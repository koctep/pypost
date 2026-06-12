# PYPOST-148: Dev Docs

## Updates

| File | Change |
| --- | --- |
| `doc/dev/template_service.md` | Added **Compile cache decision (PYPOST-148)** — audit, benchmark summary, deferral, revisit |
| `tests/test_template_service_caching_eval.py` | Docstring references PYPOST-148 closure |
| `ai-tasks/PYPOST-18/40-tech-debt.md` | Marked PYPOST-148 follow-up resolved |

## Cross-references

- Full benchmark and strategy comparison: `ai-tasks/PYPOST-455/20-architecture.md`
- Caching evaluation section: `doc/dev/template_expression_functions.md`

## Review

Documentation reflects audit outcome: no bounded cache in `TemplateService`; deferral justified
by PYPOST-455 measurements.
