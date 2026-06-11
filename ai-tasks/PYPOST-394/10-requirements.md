# PYPOST-394: Close debt — no JSON validation in highlighter

## Goals

JsonHighlighter may color invalid JSON without reporting errors. JSON validation lives
elsewhere (`ValidationController`). Confirm this separation is intentional.

## Definition of Done

1. Highlighter scope limited to syntax coloring.
2. Validation handled by `body_editor_validation.md` pipeline.
3. Debt closed without code change.

## Task Description

Accepted-debt closure. Validation and highlighting are separate concerns.
