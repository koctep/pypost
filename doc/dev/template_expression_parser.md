# Template Expression Parser

`pypost.core.template_expression_parser` is the shared lexer and grammar utility for `{{ ... }}`
expressions. Use `lex_template_expressions()` when source spans or incomplete placeholders matter,
and `tokenize_template_expressions()` for the legacy list of closed inner expressions.

Use `function_names()`, `identifier_names()`, and `split_single_argument()` for expression-level
inspection. The latter respects nested parentheses and quoted strings when detecting top-level
commas. Callers should preserve the existing resolver and tokenizer facades for compatibility.
