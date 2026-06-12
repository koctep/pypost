# PYPOST-145: Architecture — TemplateService Variable-Type Unit Tests

## Research

### Prior work

| Ticket | Deliverable |
| --- | --- |
| PYPOST-147 | Broad `tests/test_template_service.py` suite (49+ tests) |
| PYPOST-450+ | Render, validation, observability, parity matrices |

### Gap analysis

| Behavior | PYPOST-147 coverage | PYPOST-145 action |
| --- | --- | --- |
| String variables | `test_render_known_variable` | None |
| Catalog functions | Multiple render tests | None |
| Syntax / structure errors | `test_render_invalid_syntax_*`, validation class | Audit only — satisfied |
| Integer / float / bool / None values | **Missing** | Add `TestTemplateServiceVariableTypes` |
| Catalog function + int arg | **Missing** | `test_render_catalog_function_with_integer_argument` |

### Implementation plan

1. Add `TestTemplateServiceVariableTypes` with six focused assertions.
2. Run scoped pytest on `tests/test_template_service.py`.
3. Update `doc/dev/template_expression_functions.md` test inventory.

### Test design

- **Isolation**: `TemplateService()` only; no metrics unless needed.
- **Determinism**: fixed literals for int/float/bool/None expectations per Jinja2 defaults.
- **No production edits**: tests document current behavior only.

## Validation

```text
make test TESTS=tests/test_template_service.py
→ all passed (55 tests + subtests after PYPOST-145)
```
