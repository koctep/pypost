# PYPOST-1247: Dynamic and decorator-based strict function registration

## Research

The current registry owns the allow-listed callable catalog and a private static strict-name
set. Existing resolver code asks the registry whether a function is allowed or strict, so the
registry is the correct single point for metadata changes.

## Implementation Plan

Add one registration primitive that updates the callable catalog and strict metadata atomically.
Expose it both as a direct API and as a decorator helper. Add unit tests before implementation,
then preserve environment binding and existing built-in behavior.

**Mandatory — Failing Repro:** Extend `tests/test_function_registry.py` with tests for direct
registration, `register(..., is_strict=True)` decorator use, `register_strict`, replacement, and
invalid inputs. Run the focused Make test target before production edits; failures should show the
missing registration API.

## Architecture

`FunctionRegistry` remains the catalog boundary:

```text
caller/decorator -> FunctionRegistry.register -> functions + strict names
resolver --------> is_allowed / is_strict_conversion
template service -> register_into_env -> Jinja globals
```

Registration validates a non-empty string name and callable implementation before mutating state.
Replacing a name replaces both its implementation and strict flag. Decorators return the original
callable. The built-in catalog is copied per registry instance, keeping instances isolated.

## Q&A

| Question | Answer |
| --- | --- |
| Are class-level global registrations needed? | No; per-instance registries preserve isolation. |
| What is the strict decorator name? | `register_strict`, with `register(..., is_strict=True)` also supported. |
