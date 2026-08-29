# PYPOST-1151: Fix template expression tokenizer whitespace rejection test

## Goals

Ensure strict classification boundaries and semantic consistency between strict plain variable placeholders and expressions with internal whitespace. From a business and product perspective, template expressions should have predictable syntactic guarantees:
- Strict plain variable tokens (e.g. `{{host}}`) represent direct, non-spaced variable identifiers used for fast-path evaluation and strict grammar checks.
- Expressions containing leading or trailing whitespace inside delimiters (e.g. `{{ host }}`) represent loose formatting variations that should be parsed via general expression handling rather than treated as strict plain variable identifiers.
- Test suite assertions must accurately reflect the grammar rules so regression testing maintains confidence across template parsing, variable resolution, and UI hover previews without false positives or silent specification drift.

## Programming Language

- **Python**

## User Stories

### US-1: Developer and System Token Classification
**As a** core system component or developer integrating template variable resolution,  
**I want** token helper functions to strictly differentiate between exact unspaced variable identifiers and expressions containing internal delimiter whitespace,  
**So that** fast-path optimizations and strict grammar validation operate reliably without misclassifying spaced tokens.

### US-2: API User and Template Authoring Consistency
**As an** API designer or template author writing variable placeholders with varied whitespace conventions,  
**I want** template expression tokenization and variable evaluation to maintain clear boundaries between strict plain identifiers and expressions,  
**So that** my requests and template strings behave deterministically across editing, hover previews, and runtime rendering.

## Definition of Done

1. **Acceptance Criteria 1: Strict Token Validation**:
   - Evaluating `{{host}}` as a plain variable token evaluates to `True`, extracting variable name `host`.
   - Evaluating `{{ host }}` (with inner whitespace) as a strict plain variable token evaluates to `False`, extracting `None`.
2. **Acceptance Criteria 2: Test Suite Health**:
   - The test suite node `tests/test_template_expression_tokenizer.py::TestPlainVariablePattern::test_plain_pattern_rejects_whitespace_inside` passes successfully and accurately asserts rejection of inner whitespace for strict plain tokens.
   - All other existing tests in `tests/test_template_expression_tokenizer.py` and across the repository continue to pass without regressions.
3. **Acceptance Criteria 3: Quality Gate**:
   - Code adheres to repository quality standards (`make check` passing cleanly).

## Task Description

### Background
During tech debt analysis in PYPOST-1149, a pre-existing discrepancy was noted regarding `TestPlainVariablePattern::test_plain_pattern_rejects_whitespace_inside` in `tests/test_template_expression_tokenizer.py`.

The test expects strict rejection of tokens with whitespace inside delimiters (`{{ host }}` returning `False` for `is_plain_variable_token` and `None` for `extract_plain_variable_name`).

### Functional Requirements
1. The template expression tokenizer must enforce that strict plain variable token verification (`is_plain_variable_token`) accepts only unspaced tokens matching the strict identifier pattern and rejects tokens with internal whitespace.
2. The plain variable name extractor (`extract_plain_variable_name`) must extract the identifier name when a strict plain token is provided, and return `None` when given tokens with internal whitespace or function expressions.
3. General template expression tokenization (`tokenize_template_expressions`) must continue to extract inner expression bodies regardless of delimiter-adjacent whitespace (e.g., extracting `host` from `{{ host }}`).

### Non-Functional Requirements
- **Performance**: Token evaluation must remain fast and lightweight.
- **Reliability & Backward Compatibility**: Existing template tokenization and hover resolution behaviors must not break.
- **Maintainability**: Clear separation between strict plain variable tokens and loose variable tokens.

### Constraints and Assumptions
- Implementation language is Python.
- Tooling standard: All operations must run via `make` targets.

## Q&A

**Q1: Why does `is_plain_variable_token` need to reject whitespace?**  
**A1:** `is_plain_variable_token` and `extract_plain_variable_name` represent strict contracts for plain identifier tokens (without spaces). Loose whitespace forms (e.g., `{{ host }}`) are supported via loose helpers (`is_loose_plain_variable_token` / `extract_loose_plain_variable_name`) or general template expression pipelines.

**Q2: Does this break template placeholder extraction in runtime requests?**  
**A2:** No. Runtime request rendering and `tokenize_template_expressions` use `TEMPLATE_PLACEHOLDER_PATTERN` which strips surrounding whitespace inside `{{ ... }}`.
