# PYPOST-147: Unit tests for `TemplateService`

## Research

### Module under test

`pypost/core/template_service.py` — `TemplateService`:

| Method | Role |
| --- | --- |
| `__init__(metrics?)` | Jinja `Environment`, `FunctionRegistry`, `FunctionExpressionResolver` |
| `validate_function_expressions(content)` | Delegate to resolver `validate_content` |
| `render_string(content, variables, render_path)` | Tokenize → validate → Jinja render → fallback |
| `parse(content)` | Jinja AST parse |

Private helpers (`_record_empty_render_attempt`, `_emit_*`, `_fallback_*`) are exercised via
`render_string` and direct helper tests where metrics branching matters.

### Existing test file

`tests/test_template_service.py` (delivered incrementally via PYPOST-450, PYPOST-454,
PYPOST-459, PYPOST-460):

| Test class | Coverage |
| --- | --- |
| `TestTemplateServiceRenderString` | Variables, catalog functions, nesting, invalid forms, parity |
| `TestTemplateServiceParse` | `parse()` AST |
| `TestTemplateServiceValidationOutcomes` | `validate_function_expressions` error codes |
| `TestTemplateServiceObservability` | Metrics + `render_path` labels |
| `TestTemplateServiceRenderStages` | Staged outcomes with mocked render error |
| `TestTemplateServiceHelperStages` | Fallback helper metrics branching |

Shared case data: `MALFORMED_NESTED_EXPRESSION_CASES` imported from
`tests/test_function_expression_resolver.py`.

### Gap analysis (PYPOST-147)

| API / behavior | Prior coverage | PYPOST-147 action |
| --- | --- | --- |
| Plain identifier validation | Implicit via render tests only | Add `test_validate_allows_plain_identifier` |
| `render_string` without metrics | Empty-content path | Covered indirectly; no change required |
| `parse` invalid syntax | Not required for DoD | Out of scope (Jinja raises; not product API) |

### Implementation plan

1. **Audit** — map public methods to existing test classes (no production edits).
2. **Fill gap** — one validation test for plain `{{name}}` allow-list pass-through.
3. **Verify** — `.venv/bin/python -m pytest tests/test_template_service.py -v`.
4. **Document** — update `doc/dev/template_expression_functions.md` test inventory.

### Test design principles

- **Isolation**: instantiate `TemplateService()` or with `MagicMock()` metrics; no Qt/HTTP.
- **Determinism**: fixed inputs and expected hashes for `md5`/`base64`/`urlencode`.
- **Parity**: `subTest` over `render_path in ("runtime", "hover")` for representative forms.
- **Fallback contract**: invalid expressions assert `result == content` (original preserved).

### Dependencies

- `FunctionRegistry`, `FunctionExpressionResolver` — behavior locked in sibling test modules;
  `TemplateService` tests assert delegate outcomes and render integration.

## Validation

```text
.venv/bin/python -m pytest tests/test_template_service.py -v
→ 49 passed, 30 subtests passed (after PYPOST-147 gap fill)
```
