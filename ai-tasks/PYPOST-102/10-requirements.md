# PYPOST-102: Move JsonHighlighter colors to theme or config

## Goals

Confirm whether JSON syntax colors still need extraction from `JsonHighlighter`, or close
this debt item as a duplicate of the work already delivered under PYPOST-99.

## Programming Language

Python 3.10+ (review scope only)

## User Stories

- As a maintainer, I want a single source of truth for JSON highlight colors so theme
  changes do not require editing the highlighter widget.
- As a reviewer, I want duplicate PYPOST-11 follow-ups consolidated so sprint debt does
  not re-implement completed work.

## Definition of Done

- Theme module and `JsonHighlighter` wiring verified against acceptance criteria.
- Verdict documented: duplicate of [PYPOST-99](https://pypost.atlassian.net/browse/PYPOST-99).
- `doc/dev/json_syntax_highlighting.md` references PYPOST-99 resolution and this closure.
- `ai-tasks/PYPOST-11/40-tech-debt.md` updated to remove the open PYPOST-102 follow-up.
- No new code required unless verification finds a gap (none found).

## Task Description

**Source:** `ai-tasks/PYPOST-11/40-tech-debt.md` — move color settings to application
theme or config.

[PYPOST-99](https://pypost.atlassian.net/browse/PYPOST-99) already closed the hardcoded-
colors debt by verifying `JsonSyntaxColors` in `pypost/ui/theme/json_syntax_theme.py`,
palette resolution (PYPOST-395), and `JsonHighlighter` consumption. PYPOST-102 repeats the
same PYPOST-11 follow-up wording and is closed as duplicate when confirmed.

### In Scope

- Cross-check theme module, highlighter wiring, and unit tests
- Documentation update referencing PYPOST-99
- PYPOST-11 debt registry cleanup

### Out of Scope

- Settings UI for user-editable colors
- New palette variants beyond existing light/dark themes
- Regex or highlight-behavior changes
