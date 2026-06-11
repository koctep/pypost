# PYPOST-536: Dev Docs

## Updates

- `doc/dev/template_expression_functions.md`:
  - Document `TEMPLATE_PLACEHOLDER_PATTERN` as shared regex.
  - Note `VariableHoverHelper.EXPRESSION_PATTERN` aliases it for hover iteration.

## Rationale

Developers extending placeholder syntax must change one pattern in
`template_expression_tokenizer.py`; hover and validation stay aligned.
