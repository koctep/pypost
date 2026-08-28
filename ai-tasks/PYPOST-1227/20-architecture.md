# PYPOST-1227: [Libraries] Collection Namespace Resolution for Shared Libraries

## Research

In `pypost/core/variable_resolver.py`, `LibraryVariableResolver.resolve` computes effective runtime variables across base defaults, active presets, and local overlay overrides/secrets.
Currently:
- All variable keys are treated as a single flat namespace.
- If two collections in the same library use common variable names (`api_key`, `base_url`, `timeout`), overlay overrides or preset configurations for one collection collide with the other.
- Support for namespaced syntax (`<collection_name>.<variable_name>`) allows scoped overrides while maintaining fallback to shared variables.

## Implementation Plan

1. **Step 3 (Failing Repro):**
   - Create `tests/test_collection_namespace_resolution.py`:
     - Test collection-scoped preset overrides: `billing.api_key` in preset overrides base `api_key` when resolving for `collection="billing"`.
     - Test collection-scoped overlay overrides and secrets: `billing.api_key` in `overlay.secrets` takes precedence for `billing` collection, while leaving `users` collection with its default or `users.api_key`.
     - Test namespaced variable template accessibility (`variables["billing.api_key"]`).
     - Test fallback to shared library defaults when no scoped override is defined.
   - Confirm tests fail on unmodified code.

2. **Step 4 (Development):**
   - Update `LibraryVariableResolver.resolve` in `pypost/core/variable_resolver.py`:
     - Extract collection identifier candidates (exact name, lowercase name, snake_case slug, ID).
     - Route namespaced entries from `manifest.presets`, `overlay.overrides`, and `overlay.secrets` matching `<prefix>.<var_name>` to override `var_name` for the active collection.
     - Preserve both stripped (`var_name`) and fully qualified (`<prefix>.<var_name>`) names in `variables` and `provenance`.
   - Verify tests pass cleanly.

3. **Steps 5–8:**
   - Code cleanup, observability logging, tech debt analysis, and dev docs.

## Architecture

```
+--------------------------------------------------------------------------+
|                       LibraryVariableResolver                            |
+--------------------------------------------------------------------------+
|                                                                          |
|  Collection Identifiers:                                                 |
|    - collection.name (e.g. "Billing API")                                |
|    - collection.name.lower() (e.g. "billing api")                        |
|    - collection.name.lower().replace(" ", "_") (e.g. "billing_api")       |
|    - collection.id (e.g. "col-12345")                                    |
|                                                                          |
|  Precedence Resolution Flow for Target Collection:                       |
|    1. Base Defaults (manifest.variables, collection.variables)           |
|    2. Active Profile (manifest.presets, collection.presets)              |
|       - Un-namespaced: preset[var_name]                                  |
|       - Namespaced: preset["<prefix>.<var_name>"] (Higher priority)      |
|    3. Local Overlay Overrides & Secrets                                  |
|       - Un-namespaced: overlay.overrides / overlay.secrets               |
|       - Namespaced: overlay.overrides["<prefix>.<var_name>"] /           |
|                     overlay.secrets["<prefix>.<var_name>"]               |
|                     (Highest priority for target collection)             |
|                                                                          |
+--------------------------------------------------------------------------+
```

## Q&A

| Question | Answer |
| --- | --- |
| Are namespaced keys exposed in `result.variables`? | Yes, both `result.variables["api_key"]` (effective for collection) and `result.variables["billing.api_key"]` are available. |
| What happens if a collection name has spaces or hyphens? | Normalized prefix matching supports exact name, lowercase, and snake_case representations. |
