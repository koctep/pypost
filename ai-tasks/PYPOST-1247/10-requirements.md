# PYPOST-1247: Dynamic and decorator-based strict function registration

## Goals

Allow the template-function catalog to evolve without editing a hard-coded strict-function
list. Maintainers must be able to add approved functions at runtime while preserving the
existing allow-list and strict-conversion behavior.

## User Stories

- As a maintainer, I want to register a callable dynamically and declare whether it is strict.
- As a maintainer, I want a decorator form for registering strict functions beside their
  definitions.
- As a template renderer, I want strict-function classification to remain authoritative and
  consistent with the registered catalog.

## Definition of Done

- Dynamic registration adds a callable to the allowed catalog and makes it available through
  `get`, `is_allowed`, and `allowed_names`.
- A registered strict function is reported by `is_strict_conversion`.
- Decorator registration returns the original callable so normal function use is unchanged.
- Re-registering a name updates its callable and strictness metadata consistently.
- Existing built-in functions and environment binding remain compatible.
- Invalid registration inputs fail clearly and do not create partial catalog entries.

## Task Description

Replace the static strict-function metadata in `FunctionRegistry` with an extensible registration
API. The scope is limited to the registry and its tests/documentation; no new template syntax or
external request behavior is introduced.

**Programming language:** Python

## Q&A

| Question | Answer |
| --- | --- |
| Why is this needed? | Future strict functions should not require modifying registry internals. |
| Does this change existing templates? | No. Existing built-ins retain their names and behavior. |
| Is arbitrary execution enabled? | No. Only explicitly registered callables enter the allow-list. |
