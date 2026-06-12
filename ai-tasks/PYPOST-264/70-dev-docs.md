# PYPOST-264: Dev Docs

## Changes

Updated `doc/dev/request_actions.md`:

- Documented allowed `source` labels for `gui_new_tab_actions_total`
- Noted that `MetricsManager.track_gui_new_tab_action` normalizes invalid strings to `unknown`

## Rationale

Developers adding new new-tab entry points need to know the allowed label set and that the
metrics layer enforces it — no separate validation required at each call site.
