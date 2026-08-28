# PYPOST-1227: [Libraries] Collection Namespace Resolution for Shared Libraries

## Goals

In large collection libraries with multiple independently authored collections (e.g. `billing`, `users`, `notifications`), variable names frequently collide (e.g. `api_key`, `base_url`, `timeout`).

To enable clean multi-collection library composition without variable collisions:
- Support optional variable namespacing syntax: `<collection_name>.<variable_name>`.
- When resolving variables for a specific collection, allow collection-scoped overrides and secrets (e.g. `billing.api_key`) to override generic/shared variables (`api_key`) for that target collection.
- Make namespaced variable names available for request templates referencing `{{<collection_name>.<variable_name>}}`.
- Support multiple collection lookup keys (e.g. exact collection name, lowercase/slug format).

**Implementation language**: Python

## User Stories

- As a library author with multiple collections in a shared library repo, I want to define collection-scoped secrets and presets like `billing.api_key` and `auth.api_key` so that different collections do not inadvertently overwrite each other's credentials.
- As a request runner, I want collection-specific namespaced variables to take precedence when executing requests inside that collection, while still falling back to shared library defaults when no collection namespace is specified.

## Definition of Done

- The variable resolution engine supports collection namespacing when evaluating variables for a specific collection.
- Namespaced overrides and secrets (e.g. `billing.api_key`) in preset configurations and local overlay storage are correctly routed and prioritized for the target collection.
- Both un-namespaced (`api_key`) and namespaced (`billing.api_key`) keys are populated in the resolved variable dictionary where applicable.
- Full backward compatibility for existing un-namespaced variable resolution.
- Comprehensive automated unit tests verify namespace resolution, override priority, and multi-collection isolation.
- All quality gates pass cleanly.

## Task Description

- **Problem Description**: Large libraries containing multiple collections authored by different teams share the same local overlay and preset namespaces. Without namespacing support, identically named variables (`api_key`, `endpoint`) across collections collide.
- **Scope**: Extend variable resolution to support collection namespace resolution (`<collection_name>.<variable_name>`), collection-specific override precedence, and namespaced template variable exposure.
- **Constraints & Assumptions**: Preserves 3-tier precedence semantics. Backward compatibility for collections without namespaced keys.

## Non-Functional Requirements

- **Determinism**: Resolution order is fully deterministic across collection name matching.
- **Robustness**: Case-insensitive and normalized slug matching support (e.g. `"Billing API"` -> `"Billing API"` and `"billing_api"` and `"billing"`).

## Main Entities

- **Variable Resolution Engine**: Engine computing effective runtime variables.
- **Collection Namespace**: Prefix derived from collection name or identifier.
- **Namespaced Variable**: A variable key prefixed with `<collection_name>.`.

## User Scenarios

1. **Scoped Secret Resolution**: A user defines `billing.api_key = "secret-1"` and `users.api_key = "secret-2"` in overlay secrets. When resolving for the `billing` collection, `api_key` resolves to `"secret-1"`.
2. **Template Access**: Request templates referencing `{{billing.api_key}}` successfully resolve when running within the library context.
3. **Shared Default Fallback**: If `billing.timeout` is not defined, it falls back cleanly to the shared library default `timeout`.

## Q&A

| Question | Answer |
| --- | --- |
| What naming formats are matched for collection prefixes? | Exact collection name (e.g. `billing`), lowercase/slug (e.g. `billing_api`), and collection ID. |
| Does namespacing apply to all layers (presets, overrides, secrets)? | Yes, namespaced keys in presets, overrides, and secrets all take precedence for the matching collection. |
