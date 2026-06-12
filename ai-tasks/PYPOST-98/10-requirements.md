# PYPOST-98: Close debt — no JSON validation in highlighter

## Goals

`JsonHighlighter` colors tokens in JSON text but does not report structural errors. Users
need reliable invalid-JSON feedback while editing request bodies. This debt item tracks
whether the highlighter must validate JSON or whether another component already does.

## User Stories

- As an **API user** editing a JSON body, I want invalid syntax reported with line and
  column so I can fix mistakes before sending a request.
- As a **maintainer**, I want a clear boundary between syntax coloring and structural
  validation so we do not duplicate parse work on every keystroke.

## Definition of Done

1. Confirm `JsonHighlighter` scope is syntax coloring only.
2. Confirm body editor validation (`ValidationController` / `JsonBodyValidator`) covers
   structural JSON errors with inline UI feedback.
3. Document the separation in developer docs and the highlighter docstring.
4. Debt closed without adding validation logic to the highlighter.

## Task Description

Accepted-debt closure from `ai-tasks/PYPOST-11/40-tech-debt.md`. Validation and
highlighting are separate concerns; PYPOST-512 implemented editor validation.
