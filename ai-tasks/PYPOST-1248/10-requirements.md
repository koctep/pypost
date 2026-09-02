# PYPOST-1248: Centralized expression lexer/parser and resolver helper deduplication

## Goals

Make template expressions behave consistently wherever PyPost scans, validates, resolves, or
reports them. Reduce maintenance risk from several subtly different parsing implementations.

## User Stories

- As a developer, I want one expression grammar so new template syntax has one change point.
- As a user, I want nested expressions and malformed placeholders to retain existing behavior.
- As an operator, I want existing strict-conversion diagnostics and secret-safe logs preserved.

## Definition of Done

- Closed and unclosed placeholders are represented consistently with source positions.
- Nested calls, quoted commas, and top-level argument validation use shared helpers.
- Environment reference extraction and strict provenance use shared parser helpers.
- Existing behavior remains compatible and focused regression tests pass.

## Task Description

Consolidate the expression parser and remove duplicated resolver logic identified in PYPOST-1120.
Scope is limited to expression scanning, argument parsing, identifier/function discovery, and
strict-provenance helper reuse. Performance optimization and new expression features are out of
scope.

## Q&A

- Q: What language is used? A: Python.
