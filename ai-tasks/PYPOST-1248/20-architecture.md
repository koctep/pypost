# PYPOST-1248: Architecture

## Design

`template_expression_parser` owns the shared expression boundary and small grammar operations.
The existing tokenizer remains the compatibility facade for closed-token callers. Function
validation, environment-variable reference discovery, and strict provenance consume the shared
helpers without changing their public APIs.

```text
content -> lexer -> ExpressionToken
expression -> function/identifier scanner and argument splitter
tokenizer, function resolver, environment resolver -> existing callers
```

Unclosed tokens retain their source span and are reported by provenance inspection; ordinary
tokenization continues to return closed expressions only. Quoted characters and nested
parentheses are ignored when finding top-level argument separators.

## Verification Plan

Unit coverage checks mixed closed/unclosed input, nested calls, quoted commas, and shared
identifier extraction. Focused parser/resolver tests and repository Make gates validate behavior.
