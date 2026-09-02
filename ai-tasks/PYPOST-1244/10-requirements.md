# PYPOST-1244: Add candidate display limit and prefix trie indexing

## Goals

Keep autocomplete responsive and usable when an environment contains more than 1,000
variables, while preserving the existing name-only completion behavior.

## User Stories

- As a request editor user, I want autocomplete results to remain manageable in large
  environments so I can select a variable quickly.
- As a request editor user, I want prefix searches to remain responsive as variables grow.
- As an integrator, I want existing completion and environment-refresh behavior to remain
  unchanged for normal-sized environments.

## Definition of Done

- Autocomplete displays no more than 30 matching names by default.
- A caller can configure a different positive candidate limit.
- Prefix matching returns the same case-insensitive names as before, bounded by the limit.
- Variable updates rebuild the search data and expose newly added names without stale results.
- Variable values and sensitive data are never indexed or displayed.
- Existing request editor hosts and completion interactions continue to work.

## Task Description

Add a candidate display limit and prefix indexing to `VariableAutocompleteLineEdit` for large
variable environments. This task is limited to autocomplete lookup and result presentation;
large-environment UI virtualization and asynchronous indexing are out of scope.

## Q&A

- Q: What is the default display limit? A: 30 matching variable names.
- Q: What is indexed? A: Variable names only; values remain outside the autocomplete index.
