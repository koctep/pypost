# PYPOST-489: Observability

Test-only task: validates existing `env_hidden_flag_changed` contract from PYPOST-448 in a
persistence round-trip context.

## Event under test

- `env_hidden_flag_changed env_name=<name> key=******** hidden=True` when
  `log_hidden_key_names` is omitted (default false).

## Privacy constraints

- Variable key name must not appear in readable form (masked as `********`).
- Variable values must never appear in logs.
- `env_name` and `hidden` state must remain observable.

## Production changes

None.
