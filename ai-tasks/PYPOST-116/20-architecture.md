# PYPOST-116: Variable propagation architecture

## Current state

Two layers cooperate:

1. **Reactive boundary (presenter):** `EnvPresenter.env_variables_changed` emits when the
   active environment's variable map changes. `MainWindow` connects this to
   `TabsPresenter.on_env_variables_changed`, which stores `_current_variables` and pushes to
   every open `RequestTab`.
2. **Push propagation (widgets):** `RequestWidget.set_variables` forwards the dict to
   `url_input`, `params_table`, `headers_table`, and `body_edit`. Each consumer stores
   `self._variables` for on-demand reads during hover (`VariableHoverMixin`) or rendering.

New tabs receive the cached `_current_variables` in `_create_request_tab` so late-opened tabs
stay in sync without re-emitting the signal.

## Decision

**Document the existing pattern** rather than introduce per-widget signals. Rationale:

- Presenter-level signal already provides reactivity at the application boundary.
- Widgets only need the latest snapshot when the user hovers or renders; storing a dict and
  reading on `mouseMoveEvent` avoids N signal connections per tab field.
- A full observer/`Property` refactor is deferred to [PYPOST-128](https://pypost.atlassian.net/browse/PYPOST-128).

## Implementation plan

1. Add `doc/dev/variable_propagation.md` with flow diagram and extension checklist.
2. Cross-link from `doc/dev/ui_mixins.md`.
3. Add docstrings on `TabsPresenter.on_env_variables_changed`,
   `RequestWidget.set_variables`, and `VariableHoverMixin.set_variables`.
4. Strengthen `tests/test_tabs_presenter.py` to assert child widgets receive updated dicts.

## Extension checklist (for new widgets)

| Step | Action |
|------|--------|
| 1 | Implement `set_variables(self, variables: dict[str, str])` storing a snapshot |
| 2 | If nested, forward from parent composite (e.g. `RequestWidget`) |
| 3 | Do **not** connect to `env_variables_changed` directly — stay under `TabsPresenter` |
| 4 | For hover, reuse `VariableHoverMixin` or call `VariableHoverHelper` with stored dict |

## Risks

| Risk | Mitigation |
| --- | --- |
| Docs drift from code | Link to concrete methods; test asserts propagation |
| Contributors add duplicate signals | Doc states single reactive entry at presenter layer |
