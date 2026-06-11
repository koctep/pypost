# PYPOST-460: Dev Docs

## Updates

- `doc/dev/template_expression_functions.md`:
  - Document `template_expression_tokenizer.tokenize_template_expressions`.
  - Note `validate_expressions` on resolver.
  - Update rendering stages table: single tokenization pass in `render_string`.
  - Mark PYPOST-460 follow-up row as done in known gaps table.

## Review

- Docs align with implementation and parity contract.
- No new standalone doc file required; feature is an internal core utility.
