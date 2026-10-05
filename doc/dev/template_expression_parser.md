# Template Expression Parser

## Overview

`pypost.core.template_expression_parser` is the shared lexer and grammar utility for `{{ ... }}`
template expressions. It provides utilities for scanning expression delimiters, inspecting
function and identifier names, and parsing function arguments with clear discrimination between
arity violations and argument syntax malformations.

Callers should use:
- `lex_template_expressions()` when source spans or unclosed placeholders matter.
- `tokenize_template_expressions()` for legacy lists of closed inner expressions.
- `function_names()` and `identifier_names()` for expression inspection.
- `parse_function_argument()` for argument inspection with structured outcome reporting.
- `split_single_argument()` as a backward-compatible wrapper returning a single extracted argument.

## Data Structures

### `ExpressionToken`

A frozen dataclass representing an expression match and its character offsets in the template:

- `expression: str` — The extracted inner expression content (trimmed).
- `start: int` — Start index of `{{` in the source string.
- `end: int` — End index following `}}` or unclosed delimiter end in the source string.
- `closed: bool` — True if closed by matching `}}`, False if unclosed or truncated.

### `ArgumentParseResult`

A frozen dataclass representing the structural outcome of parsing a function argument payload:

- `argument: str | None` — The single argument string if well-formed, or `None` if multiple
  arguments or syntax errors were encountered.
- `has_multiple_arguments: bool` — True if one or more top-level commas (`depth == 0`) were
  encountered outside quoted strings, indicating an arity violation.
- `is_malformed: bool` — True if parenthesis nesting or quotation is unbalanced (unclosed
  quotes, unclosed parentheses, or extraneous closing parentheses).

## API & Semantics

### `lex_template_expressions(content: str) -> tuple[ExpressionToken, ...]`

Scans template content for `{{` and `}}` delimiters, returning tokens with source spans. Handles
unclosed expressions and nested occurrences cleanly in a single delimiter scan.

### `function_names(expression: str) -> tuple[str, ...]`

Returns all function call identifiers present within an expression string, including nested
function calls (e.g. `md5(urlencode(x))` yields `("md5", "urlencode")`).

### `identifier_names(expression: str) -> tuple[str, ...]`

Returns all standalone identifiers that are not dotted object-path attributes.

### `parse_function_argument(raw_arg: str) -> ArgumentParseResult`

Parses the raw text inside outer function parentheses to separate top-level argument delimiter
commas from internal argument syntax malformations:

1. **State Tracking**: Iterates through characters tracking:
   - Nested parentheses `(` and `)` (`depth`).
   - Quoted string literals (`'` and `"`), supporting escaped quotes (`\"`, `\'`).
   - Negative depth (`had_negative_depth`) triggered when closing parentheses exceed opens.
2. **Arity Separation**:
   - Commas encountered at `depth == 0` without negative depth flag `has_multiple_arguments = True`.
3. **Syntax Malformation Separation**:
   - Non-zero terminal depth (`depth != 0`), unclosed quotes (`quote is not None`), or premature
     closing parentheses (`had_negative_depth = True`) set `is_malformed = True`.
4. **Result Classification**:
   - If `has_multiple_arguments`: returns `ArgumentParseResult(None, True, is_malformed)`.
   - If `is_malformed`: returns `ArgumentParseResult(None, False, True)`.
   - Well-formed single argument: returns `ArgumentParseResult(raw_arg.strip(), False, False)`.

### `split_single_argument(arguments: str) -> str | None`

A backward-compatibility wrapper preserving earlier helper call signatures. Delegates directly
to `parse_function_argument(arguments).argument`. Returns the stripped argument string when
valid, or `None` if the argument string has multiple arguments or malformed syntax.

## Integration & Error Code Mapping in FunctionExpressionResolver

`FunctionExpressionResolver._validate_function_args(function_name, args)` uses
`parse_function_argument(args)` to accurately differentiate `invalid_arity` from
`invalid_argument`:

1. **Arity Violations (`invalid_arity`)**:
   - When `has_multiple_arguments and not is_malformed`, the user passed multiple arguments to a
     single-argument function (e.g. `urlencode(a, b)`). Returns `invalid_arity`.
2. **Malformed Argument Syntax (`invalid_argument`)**:
   - When `is_malformed` is True (e.g. `urlencode(db))`, `md5(urlencode(db)`, `md5('test)`):
     - If the inner argument looks like a nested function signature (`_FUNCTION_SIGNATURE_RE`),
       it recursively validates the nested expression.
     - If nested validation yields `invalid_arity` (due to extra closing parens like in
       `md5(urlencode(db)))`), the error is mapped to `invalid_argument` for the outer call.
     - Otherwise, returns `invalid_argument` directly.
3. **Residual Checks**:
   - Any residual `has_multiple_arguments` returns `invalid_arity`.
   - If `argument is None`, returns `invalid_argument`.

This prevents syntax errors in nested expressions or arguments from being falsely reported as
arity mismatches.
