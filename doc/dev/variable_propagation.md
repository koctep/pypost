# Environment variable propagation

## Overview

pypost pushes environment variable snapshots into request-editor widgets through explicit
`set_variables(dict)` calls. Reactivity lives at the **presenter** layer via Qt signals;
individual text fields and tables store the latest dict and read it on demand (hover,
template preview).

This is intentional: variable-aware widgets do not subscribe to environment changes
directly.

## Data flow

```text
EnvPresenter.env_variables_changed(dict)
    → TabsPresenter.on_env_variables_changed(dict)
        → caches _current_variables
        → for each RequestTab: request_editor.set_variables(dict)
            → url_input / params_table / headers_table / body_edit.set_variables(dict)
                → self._variables = variables  (snapshot)
```

Wiring is established in `pypost/ui/main_window_signals.py`:

```python
window.env.env_variables_changed.connect(window.tabs.on_env_variables_changed)
```

New tabs created while an environment is active receive the cached map in
`TabsPresenter._create_request_tab` without waiting for another signal emission.

## Why push instead of per-widget signals?

| Approach | Used here? | Rationale |
| --- | --- | --- |
| Presenter signal at env boundary | Yes | One emission fans out to all open tabs |
| `set_variables` push into composites | Yes | Matches QWidget tree; no global bus |
| Per-field `variables_changed` signals | No | Would multiply connections per tab (URL, params, headers, body, tables) |
| Shared `Property` / observer object | Deferred | Tracked as [PYPOST-128](https://pypost.atlassian.net/browse/PYPOST-128) |

Widgets keep a **snapshot** because hover and template helpers only need the current map
when the user moves the mouse or renders text — not on every keystroke in the env table.

## Implementing a new variable-aware widget

1. Add `set_variables(self, variables: dict[str, str])` that assigns `self._variables`.
2. If the widget is nested under `RequestWidget`, forward from the parent's
   `set_variables` (see `pypost/ui/widgets/request_editor.py`).
3. Do **not** connect to `EnvPresenter.env_variables_changed` from the widget; stay under
   `TabsPresenter` so tab lifecycle and caching stay centralized.
4. For `{{name}}` hover tooltips, inherit `VariableHoverMixin` or use
   `VariableHoverHelper` with the stored dict. See `doc/dev/ui_mixins.md`.

Optional: implement `set_hidden_keys` when the widget should mask secret values in tooltips.

## Related entry points

| Location | Role |
| --- | --- |
| `EnvPresenter.env_variables_changed` | Signal when active env vars change |
| `TabsPresenter.on_env_variables_changed` | Fan-out to open tabs; update cache |
| `TabsPresenter._create_request_tab` | Apply cached vars to new tabs |
| `RequestWidget.set_variables` | Forward to child editors |
| `VariableHoverMixin.set_variables` | Store snapshot for hover resolution |

## Tests

- `tests/test_tabs_presenter.py` — `test_on_env_variables_changed_updates_tabs`,
  `test_new_tab_applies_env_variables`
- `tests/test_variable_hover.py` — hover behaviour with injected dicts
- `tests/test_env_presenter.py` — `env_variables_changed` emission

## Future work

Broader dependency injection or a shared variable context object is out of scope for this
document. See [PYPOST-128](https://pypost.atlassian.net/browse/PYPOST-128) for a possible
global propagation refactor if the widget tree grows further.
