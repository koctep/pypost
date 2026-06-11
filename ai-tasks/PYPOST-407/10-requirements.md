# PYPOST-407: Collections — address RequestData deep copy overheads

## Goals

Tab isolation (PYPOST-405/406/408) relies on deep copies of `RequestData` so each open tab
owns its draft. That approach works today, but scattered `model_copy(deep=True)` calls and an
unwritten copy policy make future regressions likely — especially if `RequestData` grows heavier.
This task reduces that risk pragmatically without premature micro-optimization.

## User Stories

- As a developer maintaining tab isolation, I want a single documented copy helper so copy
  semantics stay consistent across Collections, restore, and tab creation.
- As a maintainer, I want `RequestData` to remain a lean editor model so deep copies stay
  predictable as request bodies grow.
- As a reviewer, I want automated tests that guard copy isolation and model leanness so
  refactors do not silently weaken tab boundaries.

## Definition of Done

- A centralized copy helper is used for tab-isolation paths (Collections emit, `add_new_tab`,
  `restore_tabs`, UI snapshot reads where applicable).
- Copy policy is documented for developers (when to copy, what stays out of `RequestData`,
  double-copy rationale).
- `RequestData` documents that response/history payloads must not live on the model.
- Tests cover deep-copy isolation and a lean-model regression guard.
- No premature optimization (e.g. shallow copies) unless a clear win is demonstrated.
- Full test suite passes.

## Task Description

PYPOST-405/406/408 introduced extensive `model_copy(deep=True)` usage for tab isolation. Deep
copying is correct for typical request sizes because `RequestData` holds editor fields only
(responses live in `ResponseView` / history). The debt is organizational: copy calls are
duplicated, policy is implicit, and nothing prevents `RequestData` from absorbing heavy buffers
later.

### In Scope

- Centralize tab-isolation deep copy in one helper.
- Document copy policy in dev docs and model docstring.
- Route existing tab-isolation call sites through the helper.
- Add tests for copy semantics and model leanness.

### Out of Scope

- Shallow-copy or structural-sharing optimizations without measured need.
- Changing tab isolation behavior or save/sync flows.
- Moving response data onto `RequestData`.

## Functional Requirements

- Tab opening, restore, and UI read paths that require owned `RequestData` must use the
  centralized helper.
- Developer documentation must explain when to copy and what must not be stored on
  `RequestData`.
- Existing tab isolation behavior must remain unchanged from the user perspective.

## Non-functional Requirements

- **Maintainability**: one place to adjust copy semantics if `RequestData` evolves.
- **Performance**: no regression; avoid extra copies beyond existing defense-in-depth pattern.
- **Testability**: automated guards for deep copy and forbidden heavy fields on `RequestData`.

## Constraints and Assumptions

- Pydantic v2 `model_copy(deep=True)` remains the underlying copy primitive.
- Double copy on Collections → `add_new_tab` path is acceptable defense-in-depth.
- Python 3.10+; project line-length and markdown rules apply.

## Main Entities and Interactions

- **RequestData**: in-memory request draft for editor and persistence.
- **Tab**: owns an isolated copy of `RequestData` for unsaved edits.
- **Collections tree**: holds canonical saved instances; emits copies when opening tabs.
- **Copy helper**: enforces consistent deep-copy policy at boundaries.

## Q&A

- Q: Why not eliminate double copy on the Collections path?
  A: Defense-in-depth ensures `add_new_tab` always owns its buffer even if a caller passes a
  shared reference; cost is negligible for typical requests.
- Q: Why not optimize large-body copies now?
  A: No measured pain today; responses are already outside `RequestData`. Optimize when profiling
  shows a clear win.
