# PYPOST-116: Observability

## Status: N/A (documentation task)

## Assessment

Variable propagation is already logged at the env presenter boundary:

- `env_variables_updated_from_script` (INFO) when script sync updates vars
- `EnvPresenter.env_variables_changed` emission on selection changes

Widget-level `set_variables` is synchronous and cheap; adding per-push logs would be noisy
without aiding diagnosis. No new metrics or log lines added.

## Recommendation

If propagation bugs are reported, trace from `on_env_variables_changed` log context in
`EnvPresenter` first; widget snapshots are deterministic given the pushed dict.
