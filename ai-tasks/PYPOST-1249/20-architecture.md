# PYPOST-1249: Strict rendering optimization architecture

## Research

The existing lexer already returns closed and unclosed placeholder spans. The strict fallback
path can therefore carry that result through validation, provenance inspection, and evaluation.
Jinja compilation is already cached by `TemplateService`.

## Implementation Plan

1. Produce one lexer result at the start of rendering.
2. Pass that result to resolver provenance inspection.
3. Collect valid strict expressions and render them in one synthetic cached template.
4. Preserve existing exception classification and fallback behavior.

## Architecture

`TemplateService` owns the render lifecycle, `lex_template_expressions` owns placeholder
scanning, and `FunctionExpressionResolver` owns expression classification. The service passes
the shared token sequence between these components. Batched evaluation is diagnostic-only and
does not affect the returned content.

## Failing Repro

The regression test asserts that multiple strict placeholders are combined into one Jinja
evaluation template while an invalid conversion still raises `IntegerConversionError`.

## Q&A

- **Compatibility:** Existing public rendering APIs and fallback semantics remain unchanged.
